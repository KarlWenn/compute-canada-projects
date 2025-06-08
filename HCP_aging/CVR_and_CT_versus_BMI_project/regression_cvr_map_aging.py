import statsmodels.api as sm
import statsmodels.tools as st
import os
import argparse
import numpy as np
import nibabel as nib
import subprocess
import glob
import math
import pandas as pd
from nilearn import image, signal
from scipy import stats
from scipy.interpolate import splev, splrep

# Define affine matrix as global variable
AFFINE_MATRIX = np.array([[-2., 0., 0., 90.], [0., 2., 0., -126.], [0., 0., 2., -72.], [0., 0., 0., 1.]])

def finish_preprocessing(image, mask, output_dir, track_processing):
    """ Wrapper function to perform the following preprocessing steps: smoothing, filtering, and detrending.
        Calls the corresponding function for each preprocessing step, saves the fully preprocessed image, and returns the path to the preprocessed image.
    
    Parameters
    ----------
    image : str, PathLike
        Path to minimally preprocessed rs-fMRI image.
    mask : str, PathLike
        Path to brain mask for rs-fMRI image.
    output_dir : str, PathLike
        Directory to store fully preprocessed image.
    
    Returns
    -------
    output_file : str, PathLike
        Path to fully preprocessed image.
    """
    # Perform despiking
    image_array, mask_array = create_numpy_arrays(image, mask)
    voxel_course_dict, _ = generate_time_courses(image_array, mask_array)

    despiked_image_path = despiking(voxel_course_dict, output_dir)

    # Perform in-house detrending
    image_array, mask_array = create_numpy_arrays(despiked_image_path, mask)
    voxel_course_dict, _ = generate_time_courses(image_array, mask_array)

    detrended_image_path = spline_detrending(voxel_course_dict, output_dir)

    # Perform smoothing, checking if smoothed file already exists
    smoothed_image_path = smoothing(detrended_image_path, mask, output_dir)

    # Perform filtering on detrended and smoothed image
    preprocessed_image = filtering(smoothed_image_path)

    # Save the preprocessed image
    output_file = f"{output_dir}/preprocessed_image_new_v14.nii.gz"
    nib.save(preprocessed_image, output_file)

    # Perform file clean up, namely intermediary files generated while smoothing.
    # Fully preprocessed image is not deleted and kept in file system
    if not track_processing:
        CMD_ARGS = f"rm {output_dir}/despiked_image.nii.gz {output_dir}/detrended_image.nii.gz {output_dir}/prefiltered_func_data_smooth.nii.gz {output_dir}/func_data_filter_masked.nii.gz {output_dir}/prefiltered_func_data_smooth.nii.gz_usan_size.nii.gz {output_dir}/mean_func.nii.gz {output_dir}/filtered_mask.nii.gz"
        CMD = CMD_ARGS.split()
        subprocess.run(CMD)
    
    return output_file

def smoothing(image, mask, output_dir, fwhm_mm=8):
    """ Performs smoothing on an rs-fMRI image, given a brain mask, an output directory, and a FWHM (default 8mm).

    Parameters
    ----------
    image : str, PathLike
        Path to rs-fMRI image.
    mask : str, PathLike
        Path to binary brain mask for rs-fMRI image.
    output_dir : str, PathLike
        Path to directory where smoothed image will be stored.

    Returns
    -------
    susan_output_file : str, PathLike
        Path to rs-fMRI image smoothed by FSL's SUSAN. 
    """
    # Convert Gaussian FWHM from mm to sigma for compatibility with SUSAN smoothing.
    fwhm_sigma = fwhm_mm / (2 * math.sqrt(2 * math.log(2)))

    # Call function to prepare for smoothing
    int_2, median_intensity, mask_output_file = smoothing_prep(image, mask, output_dir)

    # Remove detrended image at th

    # Brightness threshold for smoothing is set to 75% of the median intensity
    # Don't ask me why this is the threshold for smoothing, I don't know...
    # It's just the value recommended by creators of FSL feat and is used for fMRIprep as well
    # Setting it to 50% of median intensity results in minimal changes in the CVR maps (look a bit more sharp)
    susan_intensity = (median_intensity - int_2) * 0.75

    mean_output_file = f"{output_dir}/mean_func"
    smoothed_output_file = f"{output_dir}/func_data_filter_masked"

    CMD_ARGS = f"fslmaths {smoothed_output_file} -Tmean {mean_output_file}"
    CMD = CMD_ARGS.split()
    subprocess.run(CMD)

    # Perform smoothing on functional image, using previously determined intensity and fwhm_sigma values,
    # As well as the time-averaged and mask-wrapped functional image to determine the smoothing area.
    susan_output_file = f"{output_dir}/prefiltered_func_data_smooth.nii.gz"

    print("Running susan...", flush=True)
    CMD_ARGS = f"susan {image} {susan_intensity} {fwhm_sigma} 3 1 1 {mean_output_file} {susan_intensity} {susan_output_file}"
    print("SUSAN CMD:", CMD_ARGS, flush=True)
    CMD = CMD_ARGS.split()
    subprocess.run(CMD)
    print("Susan complete.")

    # 
    CMD_ARGS = f"fslmaths {susan_output_file} -mas {mask_output_file} {susan_output_file}"
    CMD = CMD_ARGS.split()
    subprocess.run(CMD)
    
    return susan_output_file

def smoothing_prep(image, mask, output_dir):
    """ This function exists to do two things with relation to the smoothing() function that calls it
        1: It calculates the median intensity of the voxels within the brain mask.
        2: It wraps the functional image with a filtered version of the brain mask, so that this wrapped image may serve to
        define the "smoothing area" for the smoothing operation, i.e., this masks defines the voxels that will be smoothed.
    
    Parameters
    ----------
    image : str, PathLike
        Path to rs-fMRI image.
    mask : str, PathLike
        Path to brain mask for rs-fMRI image.
    output_dir : str, PathLike
        Path to directory wherein output files will be stored.

    Returns
    -------
    int_2 : float
        2nd percentile intensity of voxels in the image.
    median_intensity : float
        Median intensity of voxels in the image. Only considers voxels designated as being within the brain
        by the brain mask.
    filtered_mask
        A filtered version of the brain mask, to define area to be smoothed by FSL's SUSAN. Filtering makes the mask more robust
        (smoothing the mask, in effect), and hence a filtered mask is preferable over an unfiltered mask for defining smoothing area.
    """
    # Get 2nd and 98th percentiles of intensity for the image
    CMD_args = f"fslstats {image} -p 2 -p 98"
    CMD = CMD_args.split()
    command_object = subprocess.run(CMD, capture_output=True, text=True)

    # Grab 2nd percentile of intensity, for later calculation of brightness threshold of smoothing
    int_2 = float(command_object.stdout.split()[0])

    # Get median intensity, using only voxels that fall within the brain mask
    CMD_ARGS = f"fslstats {image} -k {mask} -p 50"
    CMD = CMD_ARGS.split()
    command_object = subprocess.run(CMD, capture_output=True, text=True)
    median_intensity = float(command_object.stdout)

    # Get filtered mask
    # Perform max filtering of all voxels in mask (-dilF option)
    filtered_mask = f"{output_dir}/filtered_mask"
    CMD_ARGS = f"fslmaths {mask} -dilF {filtered_mask}"
    CMD = CMD_ARGS.split()
    subprocess.run(CMD)

    # Define where to save the functional image wrapped in the filtered mask
    smoothed_output_file = f"{output_dir}/func_data_filter_masked"

    # Wrapping functional image with filtered mask
    CMD_ARGS = f"fslmaths {image} -mas {filtered_mask} {smoothed_output_file}"
    CMD = CMD_ARGS.split()
    subprocess.run(CMD)
    
    # Return three things used for later smoothing:
    # Second percentile of intensity, median intensity, and the filtered mask
    return int_2, median_intensity, filtered_mask

def despiking(voxel_course_dict, output_dir):
    """ Perform despiking on an rs-fMRI image. In house implementation works better than AFNI 3D Despike
    since it is more general. Go figure!

    Parameters
    ----------
    voxel_course_dict : dict
        Dictionary storing time courses for each voxel to be despiked, in the form
        {voxel_x_y_z: [time_course], ...} where x, y, and z are the coords of the voxel.
    """
    despiked_map = np.empty((91, 109, 91, 478))

    despiked_map[:] = np.nan

    for voxel in voxel_course_dict:
        _, x, y, z = voxel.split("_")
        time_course = voxel_course_dict[voxel]
        std = np.std(time_course)
        mean = np.nanmean(time_course)
        vfunc = np.vectorize(voxel_chop)
        despiked_time_course = vfunc(time_course, std, mean)
        despiked_map[int(x), int(y), int(z)] = despiked_time_course

    #CMD_ARGS = f"3dDespike -prefix {subject_number} -nomask -localedit -NEW {smoothed_image_path}"
    #CMD = CMD_ARGS.split()
    #subprocess.run(CMD)

    #CMD_ARGS = f"mv {subject_number}+tlrc.BRIK {subject_number}+tlrc.HEAD {output_dir}"
    #CMD = CMD_ARGS.split()
    #subprocess.run(CMD)

    despiked_image_path = f"{output_dir}/despiked_image.nii.gz"

    #despiked_image = nib.load(f"{output_dir}/{subject_number}+tlrc.BRIK")
    #despiked_map = despiked_image.get_fdata()

    #CMD_ARGS = f"rm {output_dir}/{subject_number}+tlrc.BRIK {output_dir}/{subject_number}+tlrc.HEAD"
    #CMD = CMD_ARGS.split()
    #subprocess.run(CMD)

    # Convert to NIFTI from BRIK format

    despiked_image = nib.Nifti1Image(despiked_map, AFFINE_MATRIX)
    nib.save(despiked_image, despiked_image_path)

    return despiked_image_path

def voxel_chop(voxel_score, std, mean):

    diff_from_mean = voxel_score - mean

    if abs(diff_from_mean) > 3*std:
        if voxel_score > mean:
            return mean + 2.5*std 
        else:
            return mean - 2.5*std
    else:
        return voxel_score

def spline_detrending(voxel_course_dict, output_dir):

    detrended_map = np.empty((91, 109, 91, 478))

    detrended_map[:] = 0.

    for voxel in voxel_course_dict:
        _, x, y, z = voxel.split("_")

        print("VOXEL:", x, y, z, flush=True)

        time_course = voxel_course_dict[voxel]

        # Check it isn't an all NaN time course
        if np.isnan(time_course).all():
            continue
    
        # Check if there is a trend in the first place

        p_value = 0.04

        if p_value < 0.05:
            print("P_VALUE:", p_value, flush=True)
            print("COORDS:", x, y, z, flush=True)

        if p_value > 0.05:
            detrended_array = time_course - np.nanmean(time_course)
            detrended_map[int(x), int(y), int(z)] = detrended_array
        else:

            # TODO: check if there is a linear trend by looking for a constant slope over time
            # and if so, simply perform linear detrending as it should perform better than spline detrending
            # For this one case
            # This was never done, and may never be done, at Filip's recommendation

            tens_floats = np.linspace(20, 460, 23)

            tens_ints = [int(x) for x in tens_floats]

            reshaped_time_course = np.split(time_course, tens_ints)
            reshaped_time_course[-1] = np.append(reshaped_time_course[-1], np.nanmean(reshaped_time_course[-1]))
            reshaped_time_course[-1] = np.append(reshaped_time_course[-1], np.nanmean(reshaped_time_course[-1]))

            reshaped_array = np.array(reshaped_time_course)

            minvalues = np.amin(reshaped_array, axis=1)
            maxvalues = np.amax(reshaped_array, axis=1)
            variation = maxvalues - minvalues
            average_amplitude = np.nanmean(variation)

            smoothing_value = 75.*(average_amplitude**2.)

            time_points = np.linspace(0, 478, 478)

            spl = splrep(x=time_points, y=time_course, s=smoothing_value)
            spline_values = splev(time_points, spl)

            detrended_array = time_course - spline_values

            detrended_map[int(x), int(y), int(z)] = detrended_array

    detrended_image = nib.Nifti1Image(detrended_map, AFFINE_MATRIX)

    nib.save(detrended_image, f"{output_dir}/detrended_image.nii.gz")

    return f"{output_dir}/detrended_image.nii.gz"

def detrending(voxel_course_dict, output_dir, track_processing):
    """ Perform detrending on an rs-fMRI image.

    Parameters
    ----------
    smoothed_image : str, PathLike
        Path to smoothed image.

    Returns
    -------
    detrended_image : Niimg-like object
        Detrended Nifti image object.
    """
    # Use nilearn function clean_img to perform detrending
    detrended_map = np.empty((91, 109, 91, 478))

    detrended_map[:] = np.nan

    for voxel in voxel_course_dict:
        _, x, y, z = voxel.split("_")

        time_course = voxel_course_dict[voxel]

        time_course_series = pd.Series(time_course)

        rolling_mean = time_course_series.rolling(window=45, min_periods=1, center=True, closed='both').mean()

        detrended_series = time_course_series - rolling_mean

        detrended_list = detrended_series.to_list()

        detrended_array = np.array(detrended_list)

        detrended_map[int(x), int(y), int(z)] = detrended_array

    detrended_image = nib.Nifti1Image(detrended_map, AFFINE_MATRIX)

    if track_processing:
        nib.save(detrended_image, f"{output_dir}/detrended_image.nii.gz")

    return detrended_image

def filtering(detrended_image):
    """ Perform filtering on an rs-fMRI image.
    
    Parameters
    ----------
    detrended_image : Niimg-like object
        Nifti image object that has already undergone minimal preprocessing, smoothing, and filtering.
    
    Returns
    -------
    filtered_image : Niimg-like object
        Fully preprocessed Nifti image object.
    """
    # Use nilearn function clean_img to perform temporal filtering
    filtered_image = image.clean_img(detrended_image, detrend=False, standardize=False, low_pass=0.1164, high_pass=0.008, t_r=0.800)
    
    # No track processing option since by default the preprocessed image is saved
    # Which is simply the image after filtering
    # This may change in the future if saving the preprocessed image ceases to be default behaviour
    # But likely not :P

    return filtered_image

def create_numpy_arrays(image, mask):
    """ Transform Nifti images to numpy arrays for data manipulation.

    Parameters
    ----------
    image : str, PathLike
        Path to rs-fMRI image.
    mask : str, PathLike
        Path to brain mask for rs-fMRI image.
    
    Returns
    -------
    image_array : ndarray
        4D numpy array containing all data for the rs-fMRI image, i.e., BOLD signal at each voxel for each time point
        in the image.
    mask_array : ndarray
        3D binary numpy array designating which voxels are inside the brain. 
    """
    # Get array for image
    img = nib.load(image)
    image_array = img.get_fdata()

    # Get array for mask
    mask = nib.load(mask)
    mask_array = mask.get_fdata()

    return image_array, mask_array

def run_glm(voxel_course_dict, global_time_course, output_dir):
    """ Given time courses for each voxel of interest (voxel_course_dict), a filtered global average time course, and an output directory,
    run a voxel-wise general linear model analysis. Each voxel time course is regressed against the global average time course.
    6 motion parameters and their squares are used as covariates.

    Parameters
    ----------
    voxel_course_dict : dict
        Dictionary mapping voxels to their time courses.
    global_time_course : ndarray
        1D array representing the global average time course for the subject.
    output_dir : str, PathLike
        Location to save output files. By default, same location as input files (i.e. image, brain mask, and motion confounders)
    """
    # Create array (i.e. map) to put CVR values into
    beta_1_CVR_map = np.empty((91, 109, 91))

    # Initialize all values in the map to NaN
    beta_1_CVR_map[:] = np.nan

    # Grab motion regressors
    motion_regressors_full = np.loadtxt(os.path.join(output_dir, "Movement_Regressors.txt"))
    
    motion_regressors = np.array([motion_regressors_full[:,0], motion_regressors_full[:,1], motion_regressors_full[:,2], motion_regressors_full[:,3], motion_regressors_full[:,4], motion_regressors_full[:,5]]).T
    filtered_motion_regressors = signal.clean(motion_regressors, detrend=False, standardize=False, low_pass=0.1164, t_r=0.800, high_pass=0.008)
    squared_motion_regressors = np.square(filtered_motion_regressors)
    global_signal_regressor = np.array([global_time_course]).T

    regressors = np.concatenate((global_signal_regressor, filtered_motion_regressors, squared_motion_regressors), axis=1)
    design_matrix = st.tools.add_constant(regressors)

    # For each voxel in the brain mask, perform a GLM analysis on its time course regressed against the BOLD signal
    # Along with covariates described above (i.e. motion parameters)
    for voxel in voxel_course_dict:
        # Get x, y, and z coordinates for the voxel from voxel name in dict
        _, x, y, z = voxel.split("_")
        
        # Run GLM and generate results
        gaussian_model = sm.GLM(voxel_course_dict[voxel], design_matrix, family=sm.families.Gaussian())
        gaussian_results = gaussian_model.fit()

        # Grab the beta parameter for the global BOLD signal, i.e. the "CVR score" for the voxel
        beta_1 = gaussian_results.params[1]
        beta_1_CVR_map[int(x), int(y), int(z)] = beta_1
    
    # z score all CVR scores across the image
    z_score_CVR_map_beta_1 = stats.zscore(beta_1_CVR_map, axis=None, nan_policy='omit')
    
    # Create CVR image and CVR z-score image
    beta_1_img = nib.Nifti1Image(beta_1_CVR_map, AFFINE_MATRIX)
    z_score_beta_1_img = nib.Nifti1Image(z_score_CVR_map_beta_1, AFFINE_MATRIX)

    # Save images
    nib.save(beta_1_img, os.path.join(output_dir, 'CVR_map_beta_1_new_preproc_v14.nii.gz'))
    nib.save(z_score_beta_1_img, os.path.join(output_dir, 'CVR_map_beta_1_z_new_preproc_v14.nii.gz'))

    return

def generate_time_courses(image_array, mask_array):
    """ Given an rs-FMRI image and a brain mask for this image, generates time courses for each voxel
    of the rs-fMRI image that falls within the brain mask. Also generates a global time course by averaging
    the time courses for each voxel within the mask.

    Parameters
    ----------
    image_array : ndarray
        4D array representing an rs-fMRI image.
    mask_array : ndarray
        3D array representing a brain mask for iamge described by image_array.

    Returns
    -------
    voxel_course_dict : dict
        A dictionary where voxels are mapped to their time courses. Keys are strings: "voxel_x_y_z"
        Where x, y, and z are replaced with the appropriate values
    global_time_course : ndarray
        1D array representing the global time course for the subject. 
    """

    # Grab all non-zero coordinates from the mask array, i.e., all voxel coords within the mask
    non_zero_xvalues, non_zero_yvalues, non_zero_zvalues = np.nonzero(mask_array)
    
    # Zip all non-zero values together, result is a list of form [(x1, y1, z1,), (x2, y2, z2), ...]
    non_zero_voxels = zip(non_zero_xvalues, non_zero_yvalues, non_zero_zvalues)

    # Create dictionary to store time courses for each voxel
    # Dictionary will have form {voxel1: [time_course1], voxel2: [time_course2], ...}
    voxel_course_dict = {}

    # For all non-zero voxels in the mask, grab the related time course
    for x_value, y_value, z_value in non_zero_voxels:
        voxel_name=f"voxel_{x_value}_{y_value}_{z_value}"
        if np.count_nonzero(image_array[x_value, y_value, z_value, :]) < 470:
            # Skip over values that, while within the mask, have all 0 time courses
            # np.any() returns True if any elements are True
            # 0s are False, so an all 0 time course returns False and loop skips to next voxel
            continue
        else:
            # From image array, grab voxel time course and put it into the dictionary
            voxel_time_course = image_array[x_value, y_value, z_value, :]
            voxel_course_dict[voxel_name] = voxel_time_course
    
    # Create global time course by averaging all voxel courses for voxels within the mask
    all_voxel_courses = np.array(list(voxel_course_dict.values()))
    global_time_course = np.average(all_voxel_courses, axis=0)

    return voxel_course_dict, global_time_course


def main():
    HELPTEXT="""
    Script to generate CVR maps from resting state BOLD fMRI images.
    """
    # Parse arguments passed in batch script
    # Mainly the dataset root, and the subject to examine
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--dataset_root', type=str, help="Root of dataset directory")
    parser.add_argument('--subject_number', type=str, help="Subject number to examine")
    parser.add_argument('--track_processing', type=str, help="Controls whether to save files of the image at each preprocessing step.")

    args = parser.parse_args()

    dataset_root = args.dataset_root
    subject_number = args.subject_number
    track_processing = args.track_processing
    track_processing = (track_processing == "True")

    # Generate path to subject data by joining root of dataset and subject number
    subject_path = os.path.join(dataset_root, subject_number)

    # Get path to image and path to mask
    image_path_list = glob.glob(os.path.join(subject_path, "**/rfMRI_REST?_??.nii.gz"), recursive=True)
    mask_path_list = glob.glob(os.path.join(subject_path, "**/rfMRI_REST?_??_finalmask.nii.gz"), recursive=True)
    image_mask_list = zip(image_path_list, mask_path_list)

    for image_path, mask_path in image_mask_list:
        print(f"Image path: {image_path}")
        print(f"Mask path: {mask_path}")
        # Set directory for output files
        output_dir = os.path.dirname(image_path)

        # Finish preprocessing (in order: smoothing, detrending, filtering)
        preprocessed_image_path = finish_preprocessing(image_path, mask_path, output_dir, track_processing)

        image_array, mask_array = create_numpy_arrays(preprocessed_image_path, mask_path)
        voxel_course_dict, global_time_course = generate_time_courses(image_array, mask_array)
        run_glm(voxel_course_dict, global_time_course, output_dir)

if __name__ == "__main__":
    main()