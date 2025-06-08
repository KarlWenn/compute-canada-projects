import argparse
import glob
import nibabel as nib
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score

DATA_ARRAY  = np.loadtxt("/home/karlwenn/scratch/HCP_aging/bsc01.txt", dtype=str, delimiter='\t')
SEX_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 7][1:-1] for i in range(2, 727)}
FASTING_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 18][1:-1] for i in range(2, 727)}
INSULIN_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 36][1:-7] for i in range(2, 727)}
GLUCOSE_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, -5][1:-1] for i in range(2, 727)}

REGIONAL_IMAGE = nib.load("../data/HCP-MMP1_2mm.nii.gz")
REGIONAL_ARRAY = REGIONAL_IMAGE.get_fdata()

BAD_SUBJECTS = ['HCA6058970', 'HCA6109658', 'HCA6131449', 'HCA6144357', 'HCA6249977', 'HCA6388082', 'HCA6475986', 'HCA6653277', 'HCA6946191', 'HCA6963696', 'HCA6967199', 'HCA7108358', 'HCA7155973', 'HCA7268178', 'HCA7385889', 'HCA7625176', 'HCA7651278', 'HCA7918393', 'HCA7974909', 'HCA7987312', 'HCA8126971', 'HCA8321565', 'HCA8481789', 'HCA8578704', 'HCA8591796', 'HCA8620979', 'HCA8623581', 'HCA8873908', 'HCA9022762', 'HCA9085685', 'HCA9099999', 'HCA9198092', 'HCA9386902', 'HCA9443079', 'HCA9460079', 'HCA9766912', 'HCA9938309']

def main():
    HELPTEXT="""
    Script to generate BMI/CVR scatter plots from HCP-aging CVR maps.
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--dataset_root', type=str, help="Root of dataset directory.")

    args = parser.parse_args()

    dataset_root = args.dataset_root

    CVR_map_list = glob.glob(os.path.join(dataset_root, "**/CVR_map_avg_new_preproc_v10.nii.gz"), recursive=True)

    CVR_array_dict = {os.path.dirname(CVR_map).split('/')[-1][:-6]: nib.load(CVR_map).get_fdata() for CVR_map in CVR_map_list}
    
    subject_list = list(SEX_DICTIONARY.keys())
    subject_list.sort()
    
    homa_ir_dict = get_homa_ir_dictionary(subject_list)

    print(homa_ir_dict)

    subject_list = list(homa_ir_dict.keys())
    #Sort subjects
    subject_list.sort()

    regions = [29]

    subject_cvr_dict = get_cvr_scores(CVR_array_dict, subject_list, regions)

    #subject_cvr_dict = {subject: np.nanmean(CVR_array_dict[subject]) for subject in subject_list}

    cvr_values = []
    homa_ir_values = []

    for subject in subject_list:
        if subject in BAD_SUBJECTS or homa_ir_dict[subject] > 10.:
            continue
        if subject_cvr_dict[subject][29] > 3.6:
            print(subject)
        else:
            homa_ir_values.append(homa_ir_dict[subject])
            cvr_values.append(subject_cvr_dict[subject][29])

    plt.scatter(x=homa_ir_values, y=cvr_values)
    plt.ylim(-1, 4)
    plt.xlabel("HOMA-IR")
    plt.ylabel("CVR Score")
    plt.title("CVR versus HOMA-IR for HCP-Aging Subjects - Region 29")

    z = np.polyfit(homa_ir_values, cvr_values, 1)
    y_hat = np.poly1d(z)(homa_ir_values)
    plt.plot(homa_ir_values,y_hat,"r--")

    text = f"$R^2 = {r2_score(cvr_values, y_hat):0.3f}$"

    plt.gca().text(0.05, 0.95, text,transform=plt.gca().transAxes,
     fontsize=14, verticalalignment='top')

    plt.savefig("../data/region_29_HOMA_IR_CVR_scatter_new_preproc_v10.png")

def get_homa_ir_dictionary(subject_list):
    return {subject: (float(INSULIN_DICTIONARY[subject]) * float(GLUCOSE_DICTIONARY[subject]))/405. for subject in subject_list\
            if (not (INSULIN_DICTIONARY[subject] == '' or GLUCOSE_DICTIONARY[subject] == '' or FASTING_DICTIONARY[subject] == '')) and int(FASTING_DICTIONARY[subject])}

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