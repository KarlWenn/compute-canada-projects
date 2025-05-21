import nibabel as nib
import subprocess
import os
import numpy as np

PPMI_DIR = "/home/karlwenn/scratch/ppmi_micapipe_outputs_v2"
SUBJECT_LIST = "../data/appa1_subs.txt"
OUTPUT_DIR = "/home/karlwenn/scratch/PPMI_appa_data_dropped_2000s"

def main():
    with open(SUBJECT_LIST) as f:
        for subject in f:
            subject, session = subject.rstrip().split()
            print(subject, session)
            input_dwi_mif, output_dwi_nifti, output_dwi_bval, output_dwi_bvec = make_dwi_inputs_outputs(subject, session)
            run_mrconvert(input_dwi_mif, output_dwi_nifti, output_dwi_bval, output_dwi_bvec)
            sliced_nifti, sliced_bval, sliced_bvec = drop_slices(output_dwi_nifti, output_dwi_bval, output_dwi_bvec)
            output_dir = f"{OUTPUT_DIR}/{subject}/{session}/dwi"
            save_data(sliced_nifti, sliced_bval, sliced_bvec, subject, session, output_dir)
    return

def make_dwi_inputs_outputs(subject, session):
    input_dwi_mif = f"{PPMI_DIR}/{subject}/{session}/dwi/{subject}_{session}_space-dwi_desc-preproc_dwi.mif"
    # Make output directories
    try:
        os.makedirs(f"{OUTPUT_DIR}/{subject}/{session}/dwi")
    except FileExistsError: # avoiding benign errors if the directories already exist
        pass
    output_dwi_nifti = f"{OUTPUT_DIR}/{subject}/{session}/dwi/{subject}_{session}_space-dwi_desc-preproc_dwi.nii.gz"
    output_dwi_bval = f"{OUTPUT_DIR}/{subject}/{session}/dwi/{subject}_{session}_space-dwi_desc-preproc_dwi.bval"
    output_dwi_bvec = f"{OUTPUT_DIR}/{subject}/{session}/dwi/{subject}_{session}_space-dwi_desc-preproc_dwi.bvec"
    return input_dwi_mif, output_dwi_nifti, output_dwi_bval, output_dwi_bvec

def run_mrconvert(input_dwi_mif, output_dwi_nifti, output_dwi_bval, output_dwi_bvec):
    CMD_ARGS = f"mrconvert {input_dwi_mif} {output_dwi_nifti} -force --export_grad_fsl {output_dwi_bvec} {output_dwi_bval}"
    print(CMD_ARGS)
    CMD = CMD_ARGS.split()
    subprocess.run(CMD)
    return

def drop_slices(output_dwi_nifti, output_dwi_bval, output_dwi_bvec):
    nifti_image = nib.load(output_dwi_nifti)
    nifti_data = nifti_image.get_fdata()
    nifti_affine = nifti_image.affine
    bval_data = np.loadtxt(output_dwi_bval)
    bvec_data = np.loadtxt(output_dwi_bvec)

    # Just index based on where the first 2000 bvalue occurs and take all the slices that occur before.
    # Since the 2000 bvals were always added at the end in concatenate_appa_dwis.py
    first_2000 = np.where(bval_data==2000)[0][0]
    nifti_data_indexed = nifti_data[:,:,:,:first_2000]
    bvec_data_indexed = bvec_data[:,:first_2000]
    bval_data_indexed = bval_data[:first_2000]

    truncated_nifti_img = nib.Nifti1Image(nifti_data_indexed, nifti_affine)

    return truncated_nifti_img, bval_data_indexed, bvec_data_indexed

def save_data(sliced_nifti, sliced_bval, sliced_bvec, subject, session, output_dir):
    output_nifti = f"{output_dir}/{subject}_{session}_space-dwi_desc-preproc_acq-truncated_dwi.nii.gz"
    output_bval = f"{output_dir}/{subject}_{session}_space-dwi_desc-preproc_acq-truncated_dwi.bval"
    output_bvec = f"{output_dir}/{subject}_{session}_space-dwi_desc-preproc_acq-truncated_dwi.bvec"
    nib.save(sliced_nifti, output_nifti)
    np.savetxt(sliced_bval, output_bval)
    np.savetxt(sliced_bvec, output_bvec)
    return

if __name__ == "__main__":
    main()