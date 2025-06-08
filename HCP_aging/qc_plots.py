from nilearn import plotting
import argparse
import glob
import os
import subprocess

def main():
    HELPTEXT="""
    Script to produce .png's of 7T CVR maps from HCP cohort to help with quality control.
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--dataset_root', type=str, help="Root of dataset directory.")
    parser.add_argument('--subject_number', type=str, help="Subject number to examine.")

    args = parser.parse_args()

    dataset_root = args.dataset_root
    subject_number = args.subject_number

    subject_path = os.path.join(dataset_root, subject_number)

    CVR_map_list = glob.glob(os.path.join(subject_path, "**/CVR_map_avg_new_preproc_v14.nii.gz"), recursive=True)

    for map in CVR_map_list:
        output_dir = f"../data/{subject_number}/"
        print(output_dir)
        CMD_ARGS = f"mkdir -p {output_dir}"
        CMD = CMD_ARGS.split()
        subprocess.run(CMD)
        plotting.plot_img(map, cut_coords=(0, -7, 6), black_bg=True, output_file=f"{output_dir}/qc_img.png", vmin=-1., vmax=4., threshold=None)

if __name__ == "__main__":
    main()