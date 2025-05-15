import nibabel as nib
import numpy as np
import glob
import os

appa1_sub_list = "../data/appa1_subs.txt"
appa2_sub_list = "../data/appa2_subs.txt"
ppmi_data_dir = "/home/karlwenn/projects/rrg-adagher/public_data/PPMI_NEW/bids"
toplvl_output_dir = "/home/karlwenn/scratch/concatenated_PPMI_appa_data"

def main():
    with open(appa1_sub_list) as f:
        for subject in f:
            subject, session = subject.rstrip().split()
            print(subject, session)
            concatenate_dwis(subject, session)
    return

def concatenate_dwis(subject, session):
    dwi_dir = f"{ppmi_data_dir}/{subject}/{session}/dwi"
    output_dir = f"{toplvl_output_dir}/{subject}/{session}/dwi"
    try:
        os.makedirs(output_dir)
    except FileExistsError:
        pass
    b0_pa_nifti = glob.glob(dwi_dir + "/*B0_dir-PA_run-01_dwi.nii.gz")
    b700_pa_nifti = glob.glob(dwi_dir + "/*B700_dir-PA_run-01_dwi.nii.gz")
    b1000_pa_nifti = glob.glob(dwi_dir + "/*B1000_dir-PA_run-01_dwi.nii.gz")
    b2000_pa_nifti = glob.glob(dwi_dir + "/*B2000_dir-PA_run-01_dwi.nii.gz")

    b0_pa_bval = glob.glob(dwi_dir + "/*B0_dir-PA_run-01_dwi.bval")
    b700_pa_bval = glob.glob(dwi_dir + "/*B700_dir-PA_run-01_dwi.bval")
    b1000_pa_bval = glob.glob(dwi_dir + "/*B1000_dir-PA_run-01_dwi.bval")
    b2000_pa_bval = glob.glob(dwi_dir + "/*B2000_dir-PA_run-01_dwi.bval")

    b0_pa_bvec = glob.glob(dwi_dir + "/*B0_dir-PA_run-01_dwi.bvec")
    b700_pa_bvec = glob.glob(dwi_dir + "/*B700_dir-PA_run-01_dwi.bvec")
    b1000_pa_bvec = glob.glob(dwi_dir + "/*B1000_dir-PA_run-01_dwi.bvec")
    b2000_pa_bvec = glob.glob(dwi_dir + "/*B2000_dir-PA_run-01_dwi.bvec")

    nifti_list = [b0_pa_nifti, b700_pa_nifti, b1000_pa_nifti, b2000_pa_nifti]
    bval_list = [b0_pa_bval, b700_pa_bval, b1000_pa_bval, b2000_pa_bval]
    bvec_list = [b0_pa_bvec, b700_pa_bvec, b1000_pa_bvec, b2000_pa_bvec]

    joined_list = zip(nifti_list, bval_list, bvec_list)

    print(joined_list)

    nifti_data_list = []
    bval_data_list = []
    bvec_data_list = []

    old_affine = ""

    for nifti, bval, bvec in joined_list:
        # Indexing is because glob returns a list, perhaps cleaner to do it above
        # But w/e
        try:
            nifti_img = nib.load(nifti[0]) # Some subjects don't have a B0 PA, so glob operations above return an empty list, resulting in an IndexError here. Can just catch it and continue
        except IndexError:
            continue
        nifti_affine = nifti_img.affine
        if old_affine != "":
            if not np.array_equal(old_affine, nifti_affine):
                print("WHATTHEFUCKRIGHTNOW")
                print(f"PUBLIC ENEMY NUMBER ONE: {subject} {session}")
        nifti_data_list.append(nifti_img.get_fdata()) 
        bval_data_list.append(np.loadtxt(bval[0]))
        bvec_data_list.append(np.loadtxt(bvec[0]))
        old_affine = nifti_affine

    try: # Can get a numpy.AxisError if b0 PA is a 3D image (only one B0 slice)
        concatenated_nifti = np.concatenate(nifti_data_list, axis=3)
        concatenated_bval = np.concatenate(bval_data_list)
        concatenated_bvec = np.concatenate(bvec_data_list, axis=1)
    except np.AxisError: # Way we will deal with this is by catching the error and only concatenating the other three PA scans in this case
        nifti_data_list = nifti_data_list[1:]
        bval_data_list = bval_data_list[1:]
        bvec_data_list = bvec_data_list[1:]
        concatenated_nifti = np.concatenate(nifti_data_list, axis=3)
        concatenated_bval = np.concatenate(bval_data_list)
        concatenated_bvec = np.concatenate(bvec_data_list, axis=1)

    concatenated_nifti_img = nib.Nifti1Image(concatenated_nifti, nifti_affine)
    nib.save(concatenated_nifti_img, f"{output_dir}/{subject}_{session}_acq-concatenated_dir-PA_run-01_dwi.nii.gz")

    np.savetxt(f"{output_dir}/{subject}_{session}_acq-concatenated_dir-PA_run-01_dwi.bval", concatenated_bval)
    np.savetxt(f"{output_dir}/{subject}_{session}_acq-concatenated_dir-PA_run-01_dwi.bvec", concatenated_bvec)

    return

if __name__ == "__main__":
    main()