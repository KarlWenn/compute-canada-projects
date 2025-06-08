import argparse
import glob
import numpy as np
import nibabel as nib
import os
import pandas as pd

AFFINE_MATRIX = np.array([[-2., 0., 0., 90.], [0., 2., 0., -126.], [0., 0., 2., -72.], [0., 0., 0., 1.]])

def main():
    HELPTEXT="""
    Script to generate subject average CVR maps for the HCP agin dataset.
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--dataset_root', type=str, help="Root of dataset directory")
    parser.add_argument('--subject_number', type=str, help="Subject number to examine")

    args = parser.parse_args()

    dataset_root = args.dataset_root
    subject_number = args.subject_number
    subject_path = os.path.join(dataset_root, subject_number)

    output_file = os.path.join(subject_path, "CVR_map_avg_new_preproc_v14.nii.gz")

    image_path_list = glob.glob(os.path.join(subject_path, "**/rfMRI_REST?_??/CVR_map_beta_1_new_preproc_v14.nii.gz"), recursive=True)

    #qc_df = pd.read_excel("../data/HCP_scan-specific_QC.xlsx")

    #bad_scans = get_bad_scans(qc_df, dataset_root)

    #for image_path in image_path_list:
    #    if image_path in bad_scans:
    #        image_path_list.remove(image_path)

    image_list = [nib.load(image_path).get_fdata() for image_path in image_path_list]

    average_map = np.nanmean(image_list, axis=0)
    
    average_map_image = nib.Nifti1Image(average_map, AFFINE_MATRIX)
    
    nib.save(average_map_image, output_file)
    
def get_bad_scans(qc_df, dataset_root):
    bad_scans = []

    #Technically this could be done in one list comprehension but it becomes very messy
    for i in range (148):
        subject = qc_df.at[i, 'Subject']
        session = qc_df.at[i, 'Session']
        polarity = qc_df.at[i, 'Polarity']
        comment = qc_df.at[i, 'Comments']

        if comment != "Checked, looked fine.":
            bad_scans.append(f"{dataset_root}/{subject}/MNINonLinear/Results/rfMRI_{session}_{polarity}/CVR_map_beta_1_new_preproc_v9.nii.gz")

    return bad_scans

if __name__ == "__main__":
    main()