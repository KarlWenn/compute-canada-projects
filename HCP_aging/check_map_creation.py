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

    args = parser.parse_args()

    dataset_root = args.dataset_root

    image_path_list = glob.glob(os.path.join(dataset_root, "**/CVR_map_avg_new_preproc_v10.nii.gz"), recursive=True)

    print(image_path_list)

    print(len(image_path_list))

if __name__ == "__main__":
    main()