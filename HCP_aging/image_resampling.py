from nilearn import image
import numpy as np
import nibabel as nib
import argparse
import os
import glob
import subprocess

AFFINE_MATRIX = np.array([[-2., 0., 0., 90.], [0., 2., 0., -126.], [0., 0., 2., -72.], [0., 0., 0., 1.]])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_root', type=str, help="Root of dataset directory")
    parser.add_argument('--cbf_dataset_root', type=str, help="Subject number to examine.")

    args = parser.parse_args()

    cbf_dataset_root = args.cbf_dataset_root

    CBF_map_list = glob.glob(os.path.join(cbf_dataset_root, "**/MNINonLinear/ASL/perfusion_calib.nii.gz"), recursive=True)

    for image_path in CBF_map_list:
        subject = os.path.dirname(image_path).split('/')[-3]
        print(subject)

        resampled_image = image.resample_to_img(source_img=image_path, target_img="/home/karlwenn/projects/def-adagher/karlwenn/CVR_maps/data/HCP-MMP1_cortices_2mm.nii.gz", clip=True)
        resampled_array = resampled_image.get_fdata()

        if np.any(~np.isnan(resampled_array)):
            print("Not all NaN.")
        else:
            print("All NaN.")

        CMD_ARGS=f"mkdir -p ../data/HCP_aging_perfusion/{subject}"
        CMD = CMD_ARGS.split()
        subprocess.run(CMD)

        nib.save(resampled_image, f"../data/HCP_aging_perfusion/{subject}/perfusion_calib_resampled.nii.gz")

if __name__ == "__main__":
    main()