import os
import argparse
import numpy as np
import glob
import nibabel as nib
import statsmodels.api as sm
import statsmodels.tools as st
from statsmodels.stats import multitest
from scipy import stats

#Declare constants, namely, csv dataframes and affine matrix.
DATA_ARRAY  = np.loadtxt("/home/karlwenn/scratch/HCP_aging/vitals01.txt", dtype=str, delimiter='\t')
HEIGHT_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 10][1:-1] for i in range(2, 727)}
WEIGHT_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 8][1:-1] for i in range(2, 727)}
SEX_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 7][1:-1] for i in range(2, 727)}
AGE_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 6][1:-1] for i in range(2, 727)}

REGIONAL_IMAGE = nib.load("../data/HCP-MMP1_2mm.nii.gz")
REGIONAL_ARRAY = REGIONAL_IMAGE.get_fdata()

CORTICAL_IMAGE = nib.load("../data/HCP-MMP1_cortices_2mm.nii.gz")
CORTICAL_ARRAY = CORTICAL_IMAGE.get_fdata()

WHOLE_BRAIN = True

AFFINE_MATRIX = np.array([[-2., 0., 0., 90.], [0., 2., 0., -126.], [0., 0., 2., -72.], [0., 0., 0., 1.]])

BAD_SUBJECTS = ['HCA6058970', 'HCA6109658', 'HCA6131449', 'HCA6144357', 'HCA6249977', 'HCA6388082', 'HCA6475986', 'HCA6653277', 'HCA6946191', 'HCA6963696', 'HCA6967199', 'HCA7108358', 'HCA7155973', 'HCA7268178', 'HCA7385889', 'HCA7625176', 'HCA7651278', 'HCA7918393', 'HCA7974909', 'HCA7987312', 'HCA8126971', 'HCA8321565', 'HCA8481789', 'HCA8578704', 'HCA8591796', 'HCA8620979', 'HCA8623581', 'HCA8873908', 'HCA9022762', 'HCA9085685', 'HCA9099999', 'HCA9198092', 'HCA9386902', 'HCA9443079', 'HCA9460079', 'HCA9766912', 'HCA9938309']

#Main function grabs pre-generated average CVR maps for each subject,
#transforms them into an np array, and maps subjects to their CVR arrays in a dict.
def main():
    HELPTEXT="""
    Script to generate CVR maps from resting state BOLD fMRI images.
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

    CVR_map_list = glob.glob(os.path.join(dataset_root, "**/CVR_map_avg_new_preproc_v12.nii.gz"), recursive=True)

    CVR_array_dict = {os.path.dirname(CVR_map).split('/')[-1][:-6]: nib.load(CVR_map).get_fdata() for CVR_map in CVR_map_list}
    
    subject_list = list(HEIGHT_DICTIONARY.keys())
    subject_list.sort()

    bmi_dictionary = get_bmi_dictionary(subject_list)
    
    #After mapping subjects to their average maps, can start to generate correlations.
    generate_correlations(CVR_array_dict, bmi_dictionary, roi_range, parcellation_array, parcellation)

def get_bmi_dictionary(subject_list):

    bmi_dictionary = {}

    for subject in subject_list:
         #If height or weight data is missing skip subject
        if WEIGHT_DICTIONARY[subject] == '' or HEIGHT_DICTIONARY[subject] == '':
            continue
        weight_lbs = WEIGHT_DICTIONARY[subject]
        height_ins = HEIGHT_DICTIONARY[subject]
        bmi = 703 * (float(weight_lbs) / float(height_ins)**2)
        bmi_dictionary[subject] = bmi

    return bmi_dictionary

def generate_correlations(CVR_array_dict, bmi_dictionary, roi_range, parcellation_array, parcellation):

    #List of subjects
    subject_list = list(bmi_dictionary.keys())
    #Sort subjects
    subject_list.sort()

    #Temp measures
    subject_list.remove('HCA6757390')
    subject_list.remove('HCA6937998')
    subject_list.remove('HCA7101546')
    subject_list.remove('HCA7605978')
    subject_list.remove('HCA8000040')
    subject_list.remove('HCA9231670')

    for subject in BAD_SUBJECTS:
        subject_list.remove(subject)

    for subject in subject_list:
        if int(AGE_DICTIONARY[subject]) > 600:
            subject_list.remove(subject)  

    sub_score_dict = {}

    #For each subject, calculate the average CVR score for each region.
    for subject in subject_list:
        print(subject)
        roi_score_dict = {roi_number: calculate_region_average(CVR_array_dict[subject], roi_number, parcellation_array) for roi_number in roi_range}
        #This dict ends up having the form: {subject no.: {1: ..., 2: ..., ...}, subject: {...}, ...}
        sub_score_dict[subject] = roi_score_dict
    
    # Since subject list is sorted, these list comprehensions give values sorted by
    # Subject name, i.e. bmi_values[0] is the BMI value for the subject with the lowest number tag
    bmi_values = np.array([bmi_dictionary[subject] for subject in subject_list]).astype(float)
    age_values = np.array([AGE_DICTIONARY[subject] for subject in subject_list]).astype(float)
    sex_values = np.array([SEX_DICTIONARY[subject] for subject in subject_list])

    #Broadcast M and F strings in gender array to 0's and 1's for compatibility purposes
    sex_values = np.where(sex_values=='M', 0, 1).astype(float)

    if WHOLE_BRAIN:
        cortex_scores_dict = {subject: np.nansum(list((sub_score_dict[subject].values())))/len(list(sub_score_dict[subject].values())) for subject in subject_list}

        CVR_scores = list(cortex_scores_dict.values())

        cortex_beta, cortex_pvalue = regression(CVR_scores, bmi_values, age_values, sex_values)

        cortex_map = np.empty((91, 109, 91))
        cortex_map[:] = np.nan

        cortex_pvalue_map = np.empty((91, 109, 91))
        cortex_pvalue_map[:] = np.nan

        for roi_number in roi_range:
            build_map(cortex_map, roi_number, cortex_beta, parcellation_array)
            build_map(cortex_pvalue_map, roi_number, cortex_pvalue, parcellation_array)

        cortex_map_image = nib.Nifti1Image(cortex_map, AFFINE_MATRIX)
        cortex_pvalue_image = nib.Nifti1Image(cortex_pvalue_map, AFFINE_MATRIX)

        nib.save(cortex_map_image, f"../data/bmi_corr_map_beta_cortex_aging_new_preproc_v10.nii.gz")
        nib.save(cortex_pvalue_image, f"../data/p_value_map_beta_cortex_aging_new_preproc_v10.nii.gz")

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
        
        bmi_values_temp = np.copy(bmi_values)
        age_values_temp = np.copy(age_values)
        sex_values_temp = np.copy(sex_values)

        CVR_scores = [sub_score_dict[subject][roi_number] for subject in subject_list]

        # Some CVR scores will be NaN if this ROI falls outside the particular subject average CVR map
        # In this case need to delete this CVR socre, as well as related scores for the other metrics
        # Need to adjust what index to delete if we have already deleted one as well,
        # Hence the j counter variable
        j=0
        for i, score in enumerate(CVR_scores):
            if np.isnan(score):

                del CVR_scores[i-j]
                bmi_values_temp = np.delete(bmi_values_temp, i-j)
                age_values_temp = np.delete(age_values_temp, i-j)
                sex_values_temp = np.delete(sex_values_temp, i-j)
                j+=1
        
        #Perform regression, get values
        if np.array_equal(bmi_values_temp, bmi_values):
            bmi_beta, bmi_pvalue = regression(CVR_scores, bmi_values, age_values, sex_values)
        else:
            bmi_beta, bmi_pvalue = regression(CVR_scores, bmi_values_temp, age_values_temp, sex_values_temp)
        roi_pvalues_dict[roi_number] = bmi_pvalue
        build_map(roi_map, roi_number, bmi_beta, parcellation_array)
        build_map(p_value_map, roi_number, bmi_pvalue, parcellation_array)

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

    nib.save(z_map_image, f"../data/bmi_z_map_beta_{parcellation}_aging_new_preproc_v10.nii.gz")
    nib.save(roi_map_image, f"../data/bmi_corr_map_beta_{parcellation}_aging_new_preproc_v10.nii.gz")
    nib.save(p_value_image, f"../data/p_value_map_beta_{parcellation}_aging_new_preproc_v10.nii.gz")
    nib.save(corrected_pvalue_image, f"../data/corrected_pvalue_map_beta_{parcellation}_aging_new_preproc_v10.nii.gz")

    return

def correct_pvalues(roi_pvalues_dict):

    _, corrected_pvalues = multitest.fdrcorrection(list(roi_pvalues_dict.values()))

    corrected_roi_pvalue_dict = {roi_number: corrected_pvalues[i] for (i, roi_number) in enumerate(roi_pvalues_dict)}

    return corrected_roi_pvalue_dict

def build_map(roi_map, roi_number, bmi_value, parcellation_array):
    x_coords, y_coords, z_coords = np.where(parcellation_array == roi_number)
    roi_voxels = list(zip(x_coords, y_coords, z_coords))

    for x, y, z in roi_voxels:
        roi_map[x, y, z] = bmi_value

def regression(CVR_array, bmi_values, age_values, sex_values):
    regressors = np.array([bmi_values, age_values, sex_values]).T
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