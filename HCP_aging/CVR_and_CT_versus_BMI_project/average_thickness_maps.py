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
REGIONAL_IMAGE = nib.load("../data/HCP-MMP1_2mm.nii.gz")
REGIONAL_ARRAY = REGIONAL_IMAGE.get_fdata()

CORTICAL_IMAGE = nib.load("../data/HCP-MMP1_cortices_2mm.nii.gz")
CORTICAL_ARRAY = CORTICAL_IMAGE.get_fdata()

BMI_DATA_ARRAY  = np.loadtxt("/home/karlwenn/scratch/HCP_aging/vitals01.txt", dtype=str, delimiter='\t')
HEIGHT_DICTIONARY = {BMI_DATA_ARRAY[i, 4][1:-1]: BMI_DATA_ARRAY[i, 10][1:-1] for i in range(2, 727)}
WEIGHT_DICTIONARY = {BMI_DATA_ARRAY[i, 4][1:-1]: BMI_DATA_ARRAY[i, 8][1:-1] for i in range(2, 727)}

AFFINE_MATRIX = np.array([[-2., 0., 0., 90.], [0., 2., 0., -126.], [0., 0., 2., -72.], [0., 0., 0., 1.]])

def read_annot():    
    left_labels, _, _ = nib.freesurfer.io.read_annot("../data/lh.HCP-MMP1.annot")
    right_labels, _, _ = nib.freesurfer.io.read_annot("../data/rh.HCP-MMP1.annot")

    return left_labels, right_labels

LEFT_LABELS, RIGHT_LABELS = read_annot()

def get_surf_data(img):
    vertex_mappings = img.header.get_axis(1).vertex
    vertex_hemispheres = img.header.get_axis(1).name

    thickness_values = img.get_fdata()[0]

    right_thickness_dict = {vertex_number: thickness_values[i] for i, vertex_number in enumerate(vertex_mappings) if vertex_hemispheres[i] == 'CIFTI_STRUCTURE_CORTEX_RIGHT'}
    left_thickness_dict = {vertex_number: thickness_values[i] for i, vertex_number in enumerate(vertex_mappings) if vertex_hemispheres[i] == 'CIFTI_STRUCTURE_CORTEX_LEFT'}

    return left_thickness_dict, right_thickness_dict

def map_vertices_to_regions(labels, thickness_dict, right):

    roi_dict = {}

    for vertex in thickness_dict:
        roi = labels[vertex]
        # Skip vertices which aren't attributed to an roi
        if roi == 0:
            continue
        if right:
            roi += 180
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

    get_average_map(thickness_img_dict, roi_range, parcellation_array, parcellation)

def get_average_map(thickness_img_dict, roi_range, parcellation_array, parcellation):
    subject_list = list(HEIGHT_DICTIONARY.keys())
    subject_list.sort()

    print(subject_list)

    sub_thickness_dict = {}

    # For each subject, calculate the average thickness for each region.
    for subject in subject_list:
        print(subject)
        left_thickness_dict, right_thickness_dict = get_surf_data(thickness_img_dict[subject])

        left_roi_thickness_dict = map_vertices_to_regions(LEFT_LABELS, left_thickness_dict, False)
        right_roi_thickness_dict = map_vertices_to_regions(RIGHT_LABELS, right_thickness_dict, True)

        roi_thickness_dict = dict(left_roi_thickness_dict)
        roi_thickness_dict.update(right_roi_thickness_dict)

        sub_thickness_dict[subject] = roi_thickness_dict

    roi_map = np.empty((91, 109, 91))
    roi_map[:] = np.nan

    for roi_number in roi_range:
        #This list comprehension generates an ordered list of scores for each subject for the roi

        thickness_scores = [sub_thickness_dict[subject][roi_number] for subject in subject_list]

        average_thickness = sum(thickness_scores)/len(thickness_scores)

        build_map(roi_map, roi_number, average_thickness, parcellation_array)

    roi_map_image = nib.Nifti1Image(roi_map, AFFINE_MATRIX)

    nib.save(roi_map_image, f"../data/avg_thickness_{parcellation}_aging.nii.gz")

def build_map(roi_map, roi_number, bmi_value, parcellation_array):
    x_coords, y_coords, z_coords = np.where(parcellation_array == roi_number)
    roi_voxels = list(zip(x_coords, y_coords, z_coords))

    for x, y, z in roi_voxels:
        roi_map[x, y, z] = bmi_value

if __name__ == "__main__":
    main()