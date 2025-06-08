import os
import argparse
import numpy as np
import glob
import nibabel as nib
import statsmodels.api as sm
import statsmodels.tools as st
from statsmodels.stats import multitest
from scipy import stats

DATA_ARRAY  = np.loadtxt("/home/karlwenn/scratch/HCP_aging/bsc01.txt", dtype=str, delimiter='\t')
SEX_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 7][1:-1] for i in range(2, 727)}
AGE_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 6][1:-1] for i in range(2, 727)}
FASTING_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 18][1:-1] for i in range(2, 727)}
INSULIN_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 36][1:-7] for i in range(2, 727)}
GLUCOSE_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, -5][1:-1] for i in range(2, 727)}

REGIONAL_IMAGE = nib.load("../data/HCP-MMP1_2mm.nii.gz")
REGIONAL_ARRAY = REGIONAL_IMAGE.get_fdata()

CORTICAL_IMAGE = nib.load("../data/HCP-MMP1_cortices_2mm.nii.gz")
CORTICAL_ARRAY = CORTICAL_IMAGE.get_fdata()

WHOLE_BRAIN = True

AFFINE_MATRIX = np.array([[-2., 0., 0., 90.], [0., 2., 0., -126.], [0., 0., 2., -72.], [0., 0., 0., 1.]])

def main():
    HELPTEXT="""
    Script to calculate BMI and CVR correlation for HCA CVR maps. 
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)

    parser.add_argument('--dataset_root', type=str, help="Root of dataset directory.")
    parser.add_argument('--parcellation', type=str, help="Mandatory option, must be string 'regional' or 'cortical'. Controls which parcellation to use to generate the correlation map.")

    args = parser.parse_args()

    dataset_root = args.dataset_root
    parcellation = args.parcellation

    if parcellation == "regional":
        roi_range = range(1, 361)
        parcellation_array = REGIONAL_ARRAY
    elif parcellation == "cortical":
        roi_range = range(1, 45)
        parcellation_array = CORTICAL_ARRAY

    CVR_map_list = glob.glob(os.path.join(dataset_root, "**/CVR_map_avg_new_preproc_v10.nii.gz"), recursive=True)

    CVR_array_dict = {os.path.dirname(CVR_map).split('/')[-1][:-6]: nib.load(CVR_map).get_fdata() for CVR_map in CVR_map_list}
  
    subject_list = list(SEX_DICTIONARY.keys())
    subject_list.sort()

    homa_ir_dict = get_homa_ir_dictionary(subject_list)

    generate_correlations(CVR_array_dict, homa_ir_dict, roi_range, parcellation_array, parcellation)

def generate_correlations(CVR_array_dict, homa_ir_dict, roi_range, parcellation_array, parcellation):

    #List of subjects
    subject_list = list(homa_ir_dict.keys())
    #Sort subjects
    subject_list.sort()

    sub_score_dict = {}

    #For each subject, calculate the average CVR score for each region.
    for subject in subject_list:
        print(subject)
        roi_score_dict = {roi_number: calculate_region_average(CVR_array_dict[subject], roi_number, parcellation_array) for roi_number in roi_range}
        #This dict ends up having the form: {subject no.: {1: ..., 2: ..., ...}, subject: {...}, ...}
        sub_score_dict[subject] = roi_score_dict
    
    # Since subject list is sorted, these list comprehensions give values sorted by
    # Subject name, i.e. homa_ir_values[0] is the BMI value for the subject with the lowest number tag
    homa_ir_values = np.array([homa_ir_dict[subject] for subject in subject_list]).astype(float)
    age_values = np.array([AGE_DICTIONARY[subject] for subject in subject_list]).astype(float)
    sex_values = np.array([SEX_DICTIONARY[subject] for subject in subject_list])

    #Broadcast M and F strings in gender array to 0's and 1's for compatibility purposes
    sex_values = np.where(sex_values=='M', 0, 1).astype(float)

    if WHOLE_BRAIN:
        cortex_scores_dict = {subject: np.nansum(list((sub_score_dict[subject].values())))/len(list(sub_score_dict[subject].values())) for subject in subject_list}

        CVR_scores = list(cortex_scores_dict.values())

        cortex_beta, cortex_pvalue = regression(CVR_scores, homa_ir_values, age_values, sex_values)

        cortex_map = np.empty((91, 109, 91))
        cortex_map[:] = np.nan

        cortex_pvalue_map = np.empty((91, 109, 91))
        cortex_pvalue_map[:] = np.nan

        for roi_number in roi_range:
            build_map(cortex_map, roi_number, cortex_beta, parcellation_array)
            build_map(cortex_pvalue_map, roi_number, cortex_pvalue, parcellation_array)

        cortex_map_image = nib.Nifti1Image(cortex_map, AFFINE_MATRIX)
        cortex_pvalue_image = nib.Nifti1Image(cortex_pvalue_map, AFFINE_MATRIX)

        nib.save(cortex_map_image, f"../data/homa_ir_corr_map_beta_cortex_aging_new_preproc_v10.nii.gz")
        nib.save(cortex_pvalue_image, f"../data/homa_ir_p_value_map_beta_cortex_aging_new_preproc_v10.nii.gz")

    #Make dictionary to store values, and an np array to map them.
    roi_pvalues_dict = {}
    roi_map = np.empty((91, 109, 91))
    roi_map[:] = np.nan

    p_value_map = np.empty((91, 109, 91))
    p_value_map[:] = np.nan

    corrected_p_value_map = np.empty((91, 109, 91))
    corrected_p_value_map[:] = np.nan

    #For each roi, calculate a correlation between BMI and CVR values
    for roi_number in roi_range:
        #This list comprehension generates an ordered list of scores for each subject for the roi
        CVR_scores = []
        
        homa_ir_values_temp = np.copy(homa_ir_values)
        age_values_temp = np.copy(age_values)
        sex_values_temp = np.copy(sex_values)

        CVR_scores = [sub_score_dict[subject][roi_number] for subject in subject_list]

        for i, score in enumerate(CVR_scores):
            if np.isnan(score):

                del CVR_scores[i]
                homa_ir_values_temp = np.delete(homa_ir_values_temp, i)
                age_values_temp = np.delete(age_values_temp, i)
                sex_values_temp = np.delete(sex_values_temp, i)
        
        #Perform regression, get values
        if np.array_equal(homa_ir_values_temp, homa_ir_values):
            homa_ir_beta, homa_ir_pvalue = regression(CVR_scores, homa_ir_values, age_values, sex_values)
        else:
            homa_ir_beta, homa_ir_pvalue = regression(CVR_scores, homa_ir_values_temp, age_values_temp, sex_values_temp)
        roi_pvalues_dict[roi_number] = homa_ir_pvalue
        build_map(roi_map, roi_number, homa_ir_beta, parcellation_array)
        build_map(p_value_map, roi_number, homa_ir_pvalue, parcellation_array)

    corrected_roi_pvalue_dict = correct_pvalues(roi_pvalues_dict)
    
    significant_regions = []
    for roi_number in roi_range:
        corrected_bmi_pvalue = corrected_roi_pvalue_dict[roi_number]

        # If pvalue is significant
        if corrected_bmi_pvalue < 0.05:
            significant_regions.append(roi_number)

        build_map(corrected_p_value_map, roi_number, corrected_bmi_pvalue, parcellation_array) 

    print(significant_regions)

    roi_z_map = stats.zscore(roi_map, axis=None, nan_policy='omit')

    roi_map_image = nib.Nifti1Image(roi_map, AFFINE_MATRIX)
    z_map_image = nib.Nifti1Image(roi_z_map, AFFINE_MATRIX)
    p_value_image = nib.Nifti1Image(p_value_map, AFFINE_MATRIX)
    corrected_pvalue_image = nib.Nifti1Image(corrected_p_value_map, AFFINE_MATRIX)

    nib.save(z_map_image, f"../data/homa_ir_z_map_beta_{parcellation}_aging_new_preproc_v10.nii.gz")
    nib.save(roi_map_image, f"../data/homa_ir_corr_map_beta_{parcellation}_aging_new_preproc_v10.nii.gz")
    nib.save(p_value_image, f"../data/homa_ir_p_value_map_beta_{parcellation}_aging_new_preproc_v10.nii.gz")
    nib.save(corrected_pvalue_image, f"../data/homa_ir_corrected_pvalue_map_beta_{parcellation}_aging_new_preproc_v10.nii.gz")

    return

def get_homa_ir_dictionary(subject_list):
    return {subject: (float(INSULIN_DICTIONARY[subject]) * float(GLUCOSE_DICTIONARY[subject]))/405. for subject in subject_list\
            if (not (INSULIN_DICTIONARY[subject] == '' or GLUCOSE_DICTIONARY[subject] == '' or FASTING_DICTIONARY[subject] == '')) and int(FASTING_DICTIONARY[subject])}

def correct_pvalues(roi_pvalues_dict):

    _, corrected_pvalues = multitest.fdrcorrection(list(roi_pvalues_dict.values()))

    corrected_roi_pvalue_dict = {roi_number: corrected_pvalues[i] for (i, roi_number) in enumerate(roi_pvalues_dict)}

    return corrected_roi_pvalue_dict

def build_map(roi_map, roi_number, bmi_value, parcellation_array):
    x_coords, y_coords, z_coords = np.where(parcellation_array == roi_number)
    roi_voxels = list(zip(x_coords, y_coords, z_coords))

    for x, y, z in roi_voxels:
        roi_map[x, y, z] = bmi_value

def regression(CVR_array, homa_ir_values, age_values, sex_values):
    regressors = np.array([homa_ir_values, age_values, sex_values]).T
    regressors_int = st.tools.add_constant(regressors)

    gaussian_model = sm.GLM(CVR_array, regressors_int, family=sm.families.Gaussian())
    gaussian_results = gaussian_model.fit()

    return gaussian_results.params[1], gaussian_results.pvalues[1]

def calculate_region_average(CVR_map, roi_number, parcellation_array):
    x_coords, y_coords, z_coords = np.where(parcellation_array == roi_number)
    roi_voxels = list(zip(x_coords, y_coords, z_coords))

    CVR_scores = [CVR_map[x_coord, y_coord, z_coord] for (x_coord, y_coord, z_coord) in roi_voxels 
    if not np.isnan(CVR_map[x_coord, y_coord, z_coord])]

    # Some average CVR maps might have ROIs that fall outside of their brain mask
    # Return NaN if this is the case
    if len(CVR_scores) == 0:
        return np.nan

    return sum(CVR_scores)/len(CVR_scores)

if __name__ == "__main__":
    main()