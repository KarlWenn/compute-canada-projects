import argparse
import glob
import nibabel as nib
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score

DATA_ARRAY  = np.loadtxt("/home/karlwenn/scratch/HCP_aging/vitals01.txt", dtype=str, delimiter='\t')
HEIGHT_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 10][1:-1] for i in range(2, 727)}
WEIGHT_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 8][1:-1] for i in range(2, 727)}

REGIONAL_IMAGE = nib.load("../data/HCP-MMP1_2mm.nii.gz")
REGIONAL_ARRAY = REGIONAL_IMAGE.get_fdata()

BAD_SUBJECTS = ['HCA6058970', 'HCA6131449', 'HCA6144357', 'HCA6640672', 'HCA670673', 'HCA6963696', 'HCA7108358', 'HCA7268178', 'HCA6529680', 'HCA7492486', 'HCA7536884', 'HCA7625176', 'HCA7636686', 'HCA7651278', 'HCA7673288', 'HCA8126971', 'HCA8322264', 'HCA8515578', 'HCA8591796', 'HCA8699817', 'HCA8797211', 'HCA9086990', 'HCA917997', 'HCA9198092', 'HCA9239484', 'HCA9323978', 'HCA9386902', 'HCA9443079', 'HCA9496707', 'HCA9539800', 'HCA9601374', 'HCA9650993', 'HCA9708190', 'HCA9716088', 'HCA9743900', 'HCA9766912', 'HCA9938309', 'HCA9956008']

def main():
    HELPTEXT="""
    Script to generate BMI/CVR scatter plots from HCP-aging CVR maps.
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--dataset_root', type=str, help="Root of dataset directory.")

    args = parser.parse_args()

    dataset_root = args.dataset_root

    CVR_map_list = glob.glob(os.path.join(dataset_root, "**/CVR_map_avg_new_preproc_v12.nii.gz"), recursive=True)

    CVR_array_dict = {os.path.dirname(CVR_map).split('/')[-1][:-6]: nib.load(CVR_map).get_fdata() for CVR_map in CVR_map_list}
    
    subject_list = list(HEIGHT_DICTIONARY.keys())
    subject_list.sort()

    bmi_dictionary = get_bmi_dictionary(subject_list)

    subject_list = list(bmi_dictionary.keys())
    #Sort subjects
    subject_list.sort()

    regions = [241]

    subject_cvr_dict = get_cvr_scores(CVR_array_dict, subject_list, regions)

    # TODO: add whole brain tag for these scatterplots
    #subject_cvr_dict = {subject: np.nanmean(CVR_array_dict[subject]) for subject in subject_list}

    cvr_values = []
    bmi_values = []

    for subject in subject_list:
        if subject in BAD_SUBJECTS or bmi_dictionary[subject] < 20.:
            continue
        else:
            bmi_values.append(bmi_dictionary[subject])
            cvr_values.append(subject_cvr_dict[subject][241])

    plt.scatter(x=bmi_values, y=cvr_values)
    plt.ylim(-1, 4)
    plt.xlabel("BMI")
    plt.ylabel("CVR Score")
    plt.title("CVR versus BMI for HCP-Aging Subjects - Whole Brain")

    z = np.polyfit(bmi_values, cvr_values, 1)
    y_hat = np.poly1d(z)(bmi_values)
    plt.plot(bmi_values,y_hat,"r--")

    text = f"$R^2 = {r2_score(cvr_values, y_hat):0.3f}$"

    plt.gca().text(0.05, 0.95, text,transform=plt.gca().transAxes,
     fontsize=14, verticalalignment='top')

    plt.savefig("../data/region_241_BMI_CVR_scatter_new_preproc_v12.png")

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

def get_cvr_scores(CVR_array_dict, subject_list, regions):

    subject_cvr_dict = {}

    for subject in subject_list:
        region_averages = {roi_number: calculate_region_average(CVR_array_dict[subject], roi_number) for roi_number in regions}
        subject_cvr_dict[subject] = region_averages

    return subject_cvr_dict

def calculate_region_average(CVR_map, roi_number):
    x_coords, y_coords, z_coords = np.where(REGIONAL_ARRAY == roi_number)
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