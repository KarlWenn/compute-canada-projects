import nibabel as nib
import glob
import numpy as np
import argparse
import statsmodels.api as sm
import statsmodels.tools as st
from statsmodels.stats import multitest
from scipy import stats
import os

REGION_MAPPINGS = {1:1, 2:5, 3:3, 4:2, 5:2, 6:2, 7:4, 8:6, 9:6, 10:8, 11:8, 12:8, 13:3, 14:18, 15:18, 16:3, 17:3, 18:4, 19:3, 20:5, 21:5, 22:4, 23:5, 24:10, 25:15, 26:22, 27:18, 28:15, 29:16, 30:18, 31:18, 32:18, 33:18, 34:18, 35:18, 36:7, 37:7, 38:7, 39:7, 40:7, 41:7, 42:16, 43:7, 44:7, 45:16, 46:16, 47:16, 48:16, 49:16, 50:16, 51:6, 52:6, 53:6, 54:8, 55:7, 56:8, 57:19, 58:19, 59:19, 60:19, 61:19, 62:19, 63:19, 64:19, 65:19, 66:20, 67:22, 68:22, 69:19, 70:22, 71:22, 72:20, 73:22, 74:21, 75:21, 76:21, 77:21, 78:8, 79:21, 80:21, 81:21, 82:21, 83:22, 84:22, 85:22, 86:22, 87:22, 88:19, 89:20, 90:20, 91:20, 92:20, 93:20, 94:20, 95:16, 96:8, 97:22, 98:22, 99:9, 100:9, 101:9, 102:9, 103:10, 104:10, 105:10, 106:12, 107:11, 108:12, 109:12, 110:12, 111:12, 112:12, 113:9, 114:12, 115:12, 116:17, 117:16, 118:13, 119:13, 120:13, 121:18, 122:13, 123:11, 124:10, 125:11, 126:13, 127:13, 128:11, 129:11, 130:11, 131:14, 132:14, 133:14, 134:14, 135:13, 136:14, 137:14, 138:5, 139:15, 140:15, 141:15, 142:18, 143:17, 144:17, 145:17, 146:17, 147:17, 148:17, 148:17, 149:17, 150:17, 151:17, 152:3, 153:4, 154:4, 155:13, 156:5, 157:5, 158:5, 159:5, 160:4, 161:18, 162:18, 163:4, 164:19, 165:19, 166:19, 167:12, 168:12, 169:12, 170:20, 171:21, 172:14, 173:10, 174:10, 175:11, 176:11, 177:14, 178:12, 179:19, 180:19}

BMI_DATA_ARRAY  = np.loadtxt("/home/karlwenn/scratch/HCP_aging/vitals01.txt", dtype=str, delimiter='\t')
HEIGHT_DICTIONARY = {BMI_DATA_ARRAY[i, 4][1:-1]: BMI_DATA_ARRAY[i, 10][1:-1] for i in range(2, 727)}
WEIGHT_DICTIONARY = {BMI_DATA_ARRAY[i, 4][1:-1]: BMI_DATA_ARRAY[i, 8][1:-1] for i in range(2, 727)}
SEX_DICTIONARY = {BMI_DATA_ARRAY[i, 4][1:-1]: BMI_DATA_ARRAY[i, 7][1:-1] for i in range(2, 727)}
AGE_DICTIONARY = {BMI_DATA_ARRAY[i, 4][1:-1]: BMI_DATA_ARRAY[i, 6][1:-1] for i in range(2, 727)}

IR_DATA_ARRAY  = np.loadtxt("/home/karlwenn/scratch/HCP_aging/bsc01.txt", dtype=str, delimiter='\t')
FASTING_DICTIONARY = {IR_DATA_ARRAY[i, 4][1:-1]: IR_DATA_ARRAY[i, 18][1:-1] for i in range(2, 727)}
INSULIN_DICTIONARY = {IR_DATA_ARRAY[i, 4][1:-1]: IR_DATA_ARRAY[i, 36][1:-7] for i in range(2, 727)}
GLUCOSE_DICTIONARY = {IR_DATA_ARRAY[i, 4][1:-1]: IR_DATA_ARRAY[i, -5][1:-1] for i in range(2, 727)}

REGIONAL_IMAGE = nib.load("../data/HCP-MMP1_2mm.nii.gz")
REGIONAL_ARRAY = REGIONAL_IMAGE.get_fdata()

CORTICAL_IMAGE = nib.load("../data/HCP-MMP1_cortices_2mm.nii.gz")
CORTICAL_ARRAY = CORTICAL_IMAGE.get_fdata()

WHOLE_BRAIN = False

AFFINE_MATRIX = np.array([[-2., 0., 0., 90.], [0., 2., 0., -126.], [0., 0., 2., -72.], [0., 0., 0., 1.]])

def read_annot():    
    left_labels, _, _ = nib.freesurfer.io.read_annot("../data/lh.HCP-MMP1.annot")
    right_labels, _, _ = nib.freesurfer.io.read_annot("../data/rh.HCP-MMP1.annot")

    return left_labels, right_labels

LEFT_LABELS, RIGHT_LABELS = read_annot()

def get_surf_data(img):
    vertex_mappings = img.header.get_axis(1).vertex
    vertex_hemispheres = img.header.get_axis(1).name

    thickness_values = np.asanyarray(img.dataobj)

    right_thickness_dict = {vertex_number: thickness_values[0][i] for i, vertex_number in enumerate(vertex_mappings) if vertex_hemispheres[i] == 'CIFTI_STRUCTURE_CORTEX_RIGHT'}
    left_thickness_dict = {vertex_number: thickness_values[0][i] for i, vertex_number in enumerate(vertex_mappings) if vertex_hemispheres[i] == 'CIFTI_STRUCTURE_CORTEX_LEFT'}

    return left_thickness_dict, right_thickness_dict

def regression(thickness_array, bmi_values, age_values, sex_values):
    regressors = np.array([bmi_values, age_values, sex_values]).T
    regressors_int = st.tools.add_constant(regressors)

    gaussian_model = sm.GLM(thickness_array, regressors_int, family=sm.families.Gaussian())
    gaussian_results = gaussian_model.fit()

    print(gaussian_results.summary())

    return gaussian_results.params[1], gaussian_results.pvalues[1]

def get_bmi_dictionary(subject_list):

    bmi_dict = {}

    for subject in subject_list:
         #If height or weight data is missing skip subject
        if WEIGHT_DICTIONARY[subject] == '' or HEIGHT_DICTIONARY[subject] == '':
            continue
        weight_lbs = WEIGHT_DICTIONARY[subject]
        height_ins = HEIGHT_DICTIONARY[subject]
        bmi = 703 * (float(weight_lbs) / float(height_ins)**2)
        bmi_dict[subject] = bmi

    return bmi_dict

def map_vertices_to_regions(labels, thickness_dict, right, parcellation):

    roi_dict = {}

    for vertex in thickness_dict:
        roi = labels[vertex]
        # Skip vertices which aren't attributed to an roi
        if roi == 0:
            continue
        if parcellation == "cortical":
            roi = REGION_MAPPINGS[roi]
        if right:
            if parcellation == "regional":
                roi += 180
            elif parcellation == "cortical":
                roi += 22
        thickness_value = thickness_dict[vertex]
        if roi in roi_dict:
            roi_dict[roi].append(thickness_value)
        else:
            roi_dict[roi] = [thickness_value]

    roi_average_dict = {roi:sum(thickness_values)/len(thickness_values) for roi, thickness_values in roi_dict.items()}

    return roi_average_dict

def main():
    HELPTEXT="""
    Script to generate obesity atrophy maps from CIFTI-2 thickness maps.
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

    thickness_map_list = glob.glob(os.path.join(dataset_root, "**/**/MNINonLinear/**corrThickness_MSMAll.164k_fs_LR.dscalar.nii"), recursive=True)
    thickness_img_dict = {os.path.dirname(thickness_map).split('/')[-2][0:-6]: nib.load(thickness_map) for thickness_map in thickness_map_list}

    subject_list = list(HEIGHT_DICTIONARY.keys())
    subject_list.sort()

    bmi_dict = get_bmi_dictionary(subject_list)

    generate_correlations(thickness_img_dict, bmi_dict, roi_range, parcellation_array, parcellation)

def generate_correlations(thickness_img_dict, bmi_dict, roi_range, parcellation_array, parcellation):

    #List of subjects
    subject_list = list(bmi_dict.keys())
    #Sort subjects
    subject_list.sort()

    #new_subject_list = []

    #for subject in subject_list:
        #age_in_months = int(AGE_DICTIONARY[subject])
        #if age_in_months < 600:
            #new_subject_list.append(subject)

    #subject_list = new_subject_list

    sub_thickness_dict = {}

    # For each subject, calculate the average thickness for each region.
    for subject in subject_list:
        print(subject)
        left_thickness_dict, right_thickness_dict = get_surf_data(thickness_img_dict[subject])

        left_roi_thickness_dict = map_vertices_to_regions(LEFT_LABELS, left_thickness_dict, False, parcellation)
        right_roi_thickness_dict = map_vertices_to_regions(RIGHT_LABELS, right_thickness_dict, True, parcellation)

        roi_thickness_dict = dict(left_roi_thickness_dict)
        roi_thickness_dict.update(right_roi_thickness_dict)

        sub_thickness_dict[subject] = roi_thickness_dict
    # Since subject list is sorted, these list comprehensions give values sorted by
    # Subject name, i.e. bmi_values[0] is the BMI value for the subject with the lowest number tag
    bmi_values = np.array([bmi_dict[subject] for subject in subject_list]).astype(float)
    age_values = np.array([AGE_DICTIONARY[subject] for subject in subject_list]).astype(float)
    sex_values = np.array([SEX_DICTIONARY[subject] for subject in subject_list])
    
    #Broadcast M and F strings in gender array to 0's and 1's for compatibility purposes
    sex_values = np.where(sex_values=='M', 0, 1).astype(float)

    if WHOLE_BRAIN:
        cortex_scores_dict = {subject: np.nansum(list((sub_thickness_dict[subject].values())))/len(list(sub_thickness_dict[subject].values())) for subject in subject_list}

        thickness_scores = list(cortex_scores_dict.values())

        cortex_beta, cortex_pvalue = regression(thickness_scores, bmi_values, age_values, sex_values)

        cortex_map = np.empty((91, 109, 91))
        cortex_map[:] = np.nan

        cortex_pvalue_map = np.empty((91, 109, 91))
        cortex_pvalue_map[:] = np.nan

        for roi_number in roi_range:
            build_map(cortex_map, roi_number, cortex_beta, parcellation_array)
            build_map(cortex_pvalue_map, roi_number, cortex_pvalue, parcellation_array)

        cortex_map_image = nib.Nifti1Image(cortex_map, AFFINE_MATRIX)
        cortex_pvalue_image = nib.Nifti1Image(cortex_pvalue_map, AFFINE_MATRIX)

        nib.save(cortex_map_image, f"../data/age_atrophy_map_beta_cortex_aging.nii.gz")
        nib.save(cortex_pvalue_image, f"../data/age_atrophy_p_value_map_beta_cortex_aging.nii.gz")
    
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
        print(roi_number)
        #This list comprehension generates an ordered list of scores for each subject for the roi

        thickness_scores = [sub_thickness_dict[subject][roi_number] for subject in subject_list]
        print(thickness_scores)

        for i, subject in enumerate(subject_list):
            if thickness_scores[i] != sub_thickness_dict[subject][roi_number]:
                print("Thickness mismatch.")
                print(subject, roi_number)
            if bmi_values[i] != bmi_dict[subject]:
                print("BMI mismatch.")
                print(subject, roi_number)
        
        bmi_beta, bmi_pvalue = regression(thickness_scores, bmi_values, age_values, sex_values)

        roi_pvalues_dict[roi_number] = bmi_pvalue
        build_map(roi_map, roi_number, bmi_beta, parcellation_array)
        build_map(p_value_map, roi_number, bmi_pvalue, parcellation_array)

    print(roi_pvalues_dict)

    corrected_roi_pvalue_dict = correct_pvalues(roi_pvalues_dict)
    
    print(corrected_roi_pvalue_dict)

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

    nib.save(z_map_image, f"../data/age_atrophy_z_map_beta_{parcellation}_aging.nii.gz")
    nib.save(roi_map_image, f"../data/age_atrophy_map_beta_{parcellation}_aging.nii.gz")
    nib.save(p_value_image, f"../data/age_atrophy_p_value_map_beta_{parcellation}_aging.nii.gz")
    nib.save(corrected_pvalue_image, f"../data/age_atrophy_corrected_pvalue_map_beta_{parcellation}_aging.nii.gz")
    
    return

def get_homa_ir_dictionary(subject_list):
    return {subject: (float(INSULIN_DICTIONARY[subject]) * float(GLUCOSE_DICTIONARY[subject]))/405. for subject in subject_list\
            if (not (INSULIN_DICTIONARY[subject] == '' or GLUCOSE_DICTIONARY[subject] == '' or FASTING_DICTIONARY[subject] == '')) and int(FASTING_DICTIONARY[subject])}

def build_map(roi_map, roi_number, bmi_value, parcellation_array):
    x_coords, y_coords, z_coords = np.where(parcellation_array == roi_number)
    roi_voxels = list(zip(x_coords, y_coords, z_coords))

    for x, y, z in roi_voxels:
        roi_map[x, y, z] = bmi_value

def correct_pvalues(roi_pvalues_dict):

    _, corrected_pvalues = multitest.fdrcorrection(list(roi_pvalues_dict.values()))

    corrected_roi_pvalue_dict = {roi_number: corrected_pvalues[i] for (i, roi_number) in enumerate(roi_pvalues_dict)}

    return corrected_roi_pvalue_dict

if __name__ == "__main__":
    main()