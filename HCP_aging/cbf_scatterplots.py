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

BAD_SUBJECTS = ['HCA6058970', 'HCA6109658', 'HCA6131449', 'HCA6144357', 'HCA6249977', 'HCA6388082', 'HCA6475986', 'HCA6653277', 'HCA6946191', 'HCA6963696', 'HCA6967199', 'HCA7108358', 'HCA7155973', 'HCA7268178', 'HCA7385889', 'HCA7625176', 'HCA7651278', 'HCA7918393', 'HCA7974909', 'HCA7987312', 'HCA8126971', 'HCA8321565', 'HCA8481789', 'HCA8578704', 'HCA8591796', 'HCA8620979', 'HCA8623581', 'HCA8873908', 'HCA9022762', 'HCA9085685', 'HCA9099999', 'HCA9198092', 'HCA9386902', 'HCA9443079', 'HCA9460079', 'HCA9766912', 'HCA9938309']

def main():
    HELPTEXT="""
    Script to generate CBF/CVR scatter plots from HCP-aging CVR maps.
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--dataset_root', type=str, help="Root of dataset directory.")
    parser.add_argument('--cbf_dataset_root', type=str, help="Root of CBF dataset directory.")

    args = parser.parse_args()

    dataset_root = args.dataset_root
    cbf_dataset_root = args.cbf_dataset_root

    CVR_map_list = glob.glob(os.path.join(dataset_root, "**/CVR_map_avg_new_preproc_v12.nii.gz"), recursive=True)

    CVR_array_dict = {os.path.dirname(CVR_map).split('/')[-1][:-6]: nib.load(CVR_map).get_fdata() for CVR_map in CVR_map_list}
    
    CBF_map_list = glob.glob(os.path.join(cbf_dataset_root, "**/perfusion_calib_resampled.nii.gz"), recursive=True)
    CBF_array_dict = {os.path.dirname(CBF_map).split('/')[-1][:-6]: nib.load(CBF_map).get_fdata() for CBF_map in CBF_map_list}

    subject_list = list(CBF_array_dict.keys())
    #Sort subjects
    subject_list.sort()

    regions = [88]

    subject_cvr_dict = get_cvr_scores(CVR_array_dict, subject_list, regions)
    subject_cbf_dict = get_cvr_scores(CBF_array_dict, subject_list, regions)

    # TODO: add whole brain tag for these scatterplots
    #subject_cvr_dict = {subject: np.nanmean(CVR_array_dict[subject]) for subject in subject_list}

    cvr_values = []
    cbf_values = []

    for subject in subject_list:
        if subject in BAD_SUBJECTS:
            continue
        else:
            if subject_cbf_dict[subject][88] > 50.:
                print(subject)
                print(subject_cbf_dict[subject][88])
                continue
            cbf_values.append(subject_cbf_dict[subject][88])
            cvr_values.append(subject_cvr_dict[subject][88])

    x = cbf_values
    y = cvr_values

    fig = plt.figure(layout="constrained")

    ax = fig.add_gridspec(top=0.75, right=0.75).subplots()
    ax_histx = ax.inset_axes([0, 1.05, 1, 0.25], sharex=ax)
    ax_histy = ax.inset_axes([1.05, 0, 0.25, 1], sharey=ax)

    scatter_hist(x, y, ax, ax_histx, ax_histy)

    ax.set_ylim(-1, 4)
    ax.set_xlim(0, 50)
    ax.set_xlabel("CBF")
    ax.set_ylabel("CVR Score")
    plt.title("CVR versus CBF for HCP-Aging Subjects - Region 88")

    z = np.polyfit(cbf_values, cvr_values, 1)
    y_hat = np.poly1d(z)(cbf_values)
    ax.plot(cbf_values,y_hat,"r--")

    text = f"$R^2 = {r2_score(cvr_values, y_hat):0.3f}$"

    ax.text(0.05, 0.95, text,transform=plt.gca().transAxes,
     fontsize=14, verticalalignment='top')

    plt.savefig("../data/region_88_CBF_CVR_scatter_new_preproc_v12.png")

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
    if len(CVR_scores) < 5:
        return np.nan

    return sum(CVR_scores)/len(CVR_scores)

def scatter_hist(x, y, ax, ax_histx, ax_histy):
    ax_histx.tick_params(axis="x", labelbottom=False)
    ax_histy.tick_params(axis="y", labelleft=False)

    ax.scatter(x, y)
    binwidth=0.25
    xymax = max(np.max(np.abs(x)), np.max(np.abs(y)))

    lim = (int(xymax/binwidth) + 1) * binwidth

    bins = np.arange(-lim, lim+binwidth, binwidth)
    ax_histx.hist(x, bins=15)
    ax_histy.hist(y, bins=15, orientation='horizontal')

if __name__ == "__main__":
    main()