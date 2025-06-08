import nibabel as nib
import glob
import numpy as np
import pandas as pd
import argparse
import statsmodels.api as sm
import statsmodels.tools as st
from statsmodels.stats import multitest
from scipy import stats
import os
import matplotlib.pyplot as plt

BMI_DATA_ARRAY  = np.loadtxt("/home/karlwenn/scratch/HCP_aging/vitals01.txt", dtype=str, delimiter='\t')
HEIGHT_DICTIONARY = {BMI_DATA_ARRAY[i, 4][1:-1]: BMI_DATA_ARRAY[i, 10][1:-1] for i in range(2, 727)}
WEIGHT_DICTIONARY = {BMI_DATA_ARRAY[i, 4][1:-1]: BMI_DATA_ARRAY[i, 8][1:-1] for i in range(2, 727)}
SEX_DICTIONARY = {BMI_DATA_ARRAY[i, 4][1:-1]: BMI_DATA_ARRAY[i, 7][1:-1] for i in range(2, 727)}
AGE_DICTIONARY = {BMI_DATA_ARRAY[i, 4][1:-1]: BMI_DATA_ARRAY[i, 6][1:-1] for i in range(2, 727)}

REGIONAL_IMAGE = nib.load("../data/HCP-MMP1_2mm.nii.gz")
REGIONAL_ARRAY = REGIONAL_IMAGE.get_fdata()

CORTICAL_IMAGE = nib.load("../data/HCP-MMP1_cortices_2mm.nii.gz")
CORTICAL_ARRAY = CORTICAL_IMAGE.get_fdata()

WHOLE_BRAIN = True

AFFINE_MATRIX = np.array([[-2., 0., 0., 90.], [0., 2., 0., -126.], [0., 0., 2., -72.], [0., 0., 0., 1.]])

def main():
    HELPTEXT="""
    Script to generate obesity atrophy maps from CIFTI-2 thickness maps.
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--dataset_root', type=str, help="Root of dataset directory.")

    args = parser.parse_args()

    dataset_root = args.dataset_root

    thickness_map_list = glob.glob(os.path.join(dataset_root, "**/**/MNINonLinear/**corrThickness_MSMAll.164k_fs_LR.dscalar.nii"), recursive=True)
    thickness_img_dict = {os.path.dirname(thickness_map).split('/')[-2][0:-6]: nib.load(thickness_map) for thickness_map in thickness_map_list}

    subject_list = list(HEIGHT_DICTIONARY.keys())
    subject_list.sort()

    bmi_dict = get_bmi_dictionary(subject_list)

    generate_correlations(thickness_img_dict, bmi_dict)

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

def get_surf_data(img):
    vertex_mappings = img.header.get_axis(1).vertex
    vertex_hemispheres = img.header.get_axis(1).name

    thickness_values = np.asanyarray(img.dataobj)

    left_thickness_dict = {vertex_number: thickness_values[0][i] for i, vertex_number in enumerate(vertex_mappings) if vertex_hemispheres[i] == 'CIFTI_STRUCTURE_CORTEX_LEFT'}
    right_thickness_dict = {vertex_number: thickness_values[0][i] for i, vertex_number in enumerate(vertex_mappings) if vertex_hemispheres[i] == 'CIFTI_STRUCTURE_CORTEX_RIGHT'}

    return left_thickness_dict, right_thickness_dict

def generate_correlations(thickness_img_dict, bmi_dict):

    #List of subjects
    subject_list = list(bmi_dict.keys())
    #Sort subjects
    subject_list.sort()

    sub_thickness_dict = {}

    # For each subject, calculate the average thickness for each region.
    for subject in subject_list:
        print(subject)
        left_thickness_dict, right_thickness_dict = get_surf_data(thickness_img_dict[subject])

        sub_thickness_dict[subject] = (left_thickness_dict, right_thickness_dict)

    # Since subject list is sorted, these list comprehensions give values sorted by
    # Subject name, i.e. bmi_values[0] is the BMI value for the subject with the lowest number tag
    bmi_values = np.array([bmi_dict[subject] for subject in subject_list]).astype(float)
    age_values = np.array([AGE_DICTIONARY[subject] for subject in subject_list]).astype(float)
    sex_values = np.array([SEX_DICTIONARY[subject] for subject in subject_list])
    
    #Broadcast M and F strings in gender array to 0's and 1's for compatibility purposes
    sex_values = np.where(sex_values=='M', 0, 1).astype(float)

    lh_correlation = [0.] * 163842
    rh_correlation = [0.] * 163842

    left_vertices = sub_thickness_dict[subject_list[0]][0].keys()
    print(left_vertices)
    right_vertices = sub_thickness_dict[subject_list[0]][1].keys()
    print(right_vertices)

    for vertex in left_vertices:
        thickness_scores = [sub_thickness_dict[subject][0][vertex] for subject in subject_list]
        bmi_beta, _ = regression(thickness_scores, bmi_values, age_values, sex_values)
        lh_correlation[vertex] = bmi_beta

    for vertex in right_vertices:
        thickness_scores = [sub_thickness_dict[subject][1][vertex] for subject in subject_list]
        bmi_beta, _ = regression(thickness_scores, bmi_values, age_values, sex_values)
        rh_correlation[vertex] = bmi_beta

    plt.hist(lh_correlation)
    plt.savefig("../data/lh_atrophy_histogram.jpg")
    plt.close()

    plt.hist(rh_correlation)
    plt.savefig("../data/rh_atrophy_histogram.jpg")
    plt.close()

def regression(thickness_array, bmi_values, age_values, sex_values):
    regressors = np.array([bmi_values, age_values, sex_values]).T
    regressors_int = st.tools.add_constant(regressors)

    gaussian_model = sm.GLM(thickness_array, regressors_int, family=sm.families.Gaussian())
    gaussian_results = gaussian_model.fit()

    return gaussian_results.params[1], gaussian_results.pvalues[1]

if __name__ == "__main__":
    main()
        

