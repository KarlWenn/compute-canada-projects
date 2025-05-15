import os
import json
import glob
import pandas as pd
import nibabel as nib

def main():
    ppmi_dir = "/home/karlwenn/projects/rrg-adagher/public_data/PPMI_NEW/bids"

    empty_dwi_subjects = []
    no_axis_or_dir_subs = []
    different_img_dim_subs = []
    different_voxel_dim_subs = []

    csv_dict = {"Subject": [], "Session": [], "DWIs": [], "Directionality": [], \
        "# Unique Bvals": [], "Different Bvals": [], "Existent bvals": [], "Existent AP bvals": [], "Existent PA bvals": [], \
        "JSON Polarity Identifier": [], "Different Image Dimensions": [], "Unique Image Dimensions": [], "Different Voxel Dimensions": [], "Unique Voxel Dimensions": []}

    for sub_dir in os.listdir(ppmi_dir):
        if os.path.isdir(f"{ppmi_dir}/{sub_dir}"):
            for ses_dir in os.listdir(f"{ppmi_dir}/{sub_dir}"):
                dwi_dir = f"{ppmi_dir}/{sub_dir}/{ses_dir}/dwi"
                if os.path.isdir(dwi_dir):
                    json_files = glob.glob(f"{dwi_dir}/*.json")
                    print("SUBJECT:", sub_dir, "SESSION:", ses_dir)
                    print("JSON FILES:", json_files)
                    dwi_files = glob.glob(f"{dwi_dir}/*dwi.nii.gz")
                    bval_files = glob.glob(f"{dwi_dir}/*bval")

                    dwi_files_cleaned = [os.path.basename(file) for file in dwi_files]

                    if json_files == []:
                        empty_dwi_subjects.append((sub_dir, ses_dir))
                        continue

                    # First check polarity in subject .json to see if we can get the directional information from here
                    # Create different polarity lists for PhaseEncodedDirection and PhaseEncodedAxis info
                    # Since these will be used in different checks
                    # Notably, if PhaseEncodedDirection is the same between scans, they have the same polarity. 
                    # The same is not true of PhaseEncodedAxis.
                    polarity_list_desc = [] 
                    polarity_list_axis = []
                    description_list = []

                    for f in json_files:
                        with open(f) as json_data:
                            data = json.load(json_data)
                        try:
                            polarity_list_desc.append(data["PhaseEncodingDirection"])
                            # Used to use Series description as secondary check, found it better to just use file names. See below.
                            description_list.append(data["SeriesDescription"])
                        except KeyError: # Thrown if PhaseEncodedDirection is missing
                            try:
                                # Some data only has PhaseEncodingAxis
                                # These can be the same between runs with different phase encoding directions
                                polarity_list_axis.append(data["PhaseEncodingAxis"])
                                description_list.append(data["SeriesDescription"])
                            except KeyError:
                                no_axis_or_dir_subs.append((sub_dir, ses_dir))
                                continue
                    # Check if image and voxel dimensions are the same between DWIs
                    # Make lists to Keep track of all the unique dimensions
                    different_voxel_dims = False
                    unique_voxel_dims = []
                    different_img_dims = False
                    unique_img_dims = []
                    # General strategy is to enumerate through all the dwi files, so we can keep track if the image is the
                    # First one or not. Then can just do our logic checks in the 'else' block.
                    for i, file in enumerate(dwi_files):
                        
                        if i == 0:
                            img = nib.load(file)
                            voxel_dims = img.header.get_zooms()
                            img_array = img.get_fdata()
                            img_dims = img_array.shape
                            unique_img_dims.append(img_dims)
                            unique_voxel_dims.append(voxel_dims)
                        else:
                            img = nib.load(file)
                            voxel_dims_2 = img.header.get_zooms()
                            img_array = img.get_fdata()
                            img_dims_2 = img_array.shape
                            if voxel_dims != voxel_dims_2: #logic shmogic
                                different_voxel_dims = True
                                unique_voxel_dims.append(voxel_dims_2)
                                voxel_dims = voxel_dims_2
                            if img_dims != img_dims_2:
                                different_img_dims = True
                                unique_img_dims.append(img_dims_2)
                                img_dims = img_dims_2
                    # Filling out the columns directly relevant to the code above here
                    if different_voxel_dims or different_img_dims:
                        if different_voxel_dims:
                            different_voxel_dim_subs.append((sub_dir, ses_dir))
                            csv_dict["Different Voxel Dimensions"].append("True")
                        else:
                            csv_dict["Different Voxel Dimensions"].append("False")
                        if different_img_dims:
                            different_img_dim_subs.append((sub_dir, ses_dir))
                            csv_dict["Different Image Dimensions"].append('True')
                        else:
                            csv_dict["Different Image Dimensions"].append("False")
                    else:
                        csv_dict["Different Image Dimensions"].append('False')
                        csv_dict["Different Voxel Dimensions"].append('False')

                    left_exists = False
                    right_exists = False

                    for file_name in dwi_files_cleaned:
                        if 'LR' in file_name:
                            left_exists = True
                        elif 'RL' in file_name:
                            right_exists = True

                    print(polarity_list_desc)
                    try:
                        all_same_polarity_descs = polarity_list_desc.count(polarity_list_desc[0]) == len(polarity_list_desc)
                    except IndexError:
                        # Case where we have a .json without a polarity (PhaseEncodingDirection and PhaseEncodingAxis are both missing)
                        # We want to do a check on PhaseEncodedAxis here, but always want to check PhaseEncodedDirection
                        # We only want all_same_polarity_descs to be False when there is a genuine difference in PhaseEncodedDirections
                        # So set it to a dummy variable if an IndexError is thrown
                        all_same_polarity_descs = ""
                    # Same idea as above, without the need for a dummy variable
                    try:
                        all_same_polarity_axis = polarity_list_axis.count(polarity_list_axis[0]) == len(polarity_list_axis)
                    except IndexError: 
                        all_same_polarity_axis = False
                    unique_bvals = []
                    ap_bval_exists = False
                    pa_bval_exists = False
                    for file in bval_files:
                        f = open(file, 'r')
                        bvals = f.read()
                        bval_list = bvals.split()
                        file_basename = os.path.basename(file)
                        for bval in bval_list:
                            if bval not in unique_bvals:
                                unique_bvals.append(bval)
                            if 'AP' in file_basename:
                                ap_bval_exists = True
                            elif 'PA' in file_basename:
                                pa_bval_exists = True
                    ap_exists = False
                    pa_exists = False
                    print(description_list)

                    for file_name in dwi_files:
                        if 'AP' in file_name:
                            ap_exists = True
                        elif 'PA' in file_name:
                            pa_exists = True

                    # Check for gated protocol, check for "gated" in series description
                    # Granted this might not catch everyone... but it seems every cardiac gated subject
                    # SHOULD have this word in their SeriesDescription
                    gated = False
                    for description in description_list:
                        if 'gated' in description.lower():
                            gated = True

                    # Case of genuine single direction scan (usually the cardiac gated protocol)
                    if all_same_polarity_descs and not (left_exists and right_exists) and not (ap_exists and pa_exists) and gated:
                        csv_dict['Subject'].append(sub_dir)
                        csv_dict['Session'].append(ses_dir)
                        csv_dict['DWIs'].append(dwi_files_cleaned)
                        csv_dict['Directionality'].append('Single Direction Gated')
                        csv_dict['# Unique Bvals'].append(len(unique_bvals))
                        csv_dict['Different Bvals'].append(unique_bvals)
                        if len(unique_bvals) > 1:
                            csv_dict['Existent bvals'].append('True')
                        else:
                            csv_dict['Existent bvals'].append('False')
                        csv_dict['Existent AP bvals'].append('N/A')
                        csv_dict['Existent PA bvals'].append('N/A')
                        csv_dict['JSON Polarity Identifier'].append("Description")

                        csv_dict['Unique Image Dimensions'].append(unique_img_dims)
                        csv_dict['Unique Voxel Dimensions'].append(unique_voxel_dims)
                    elif all_same_polarity_descs and not (left_exists and right_exists) and not (ap_exists and pa_exists):
                        csv_dict['Subject'].append(sub_dir)
                        csv_dict['Session'].append(ses_dir)
                        csv_dict['DWIs'].append(dwi_files_cleaned)
                        csv_dict['Directionality'].append('Single Direction (Non-Gated)')
                        csv_dict['# Unique Bvals'].append(len(unique_bvals))
                        csv_dict['Different Bvals'].append(unique_bvals)
                        if len(unique_bvals) > 1:
                            csv_dict['Existent bvals'].append('True')
                        else:
                            csv_dict['Existent bvals'].append('False')
                        csv_dict['Existent AP bvals'].append('N/A')
                        csv_dict['Existent PA bvals'].append('N/A')
                        csv_dict['JSON Polarity Identifier'].append("Description")

                        csv_dict['Unique Image Dimensions'].append(unique_img_dims)
                        csv_dict['Unique Voxel Dimensions'].append(unique_voxel_dims)
                    # Check for fake AP and PA, if they exist
                    elif ap_exists and pa_exists and all_same_polarity_descs:
                        csv_dict['Subject'].append(sub_dir)
                        csv_dict['Session'].append(ses_dir)
                        csv_dict['DWIs'].append(dwi_files_cleaned)
                        csv_dict['Directionality'].append('Fake Dual Direction (AP/PA)')
                        csv_dict['# Unique Bvals'].append(len(unique_bvals))
                        csv_dict['Different Bvals'].append(unique_bvals)
                        if len(unique_bvals) > 1:
                            csv_dict['Existent bvals'].append('True')
                        else:
                            csv_dict['Existent bvals'].append('False')
                        if ap_bval_exists:
                            csv_dict['Existent AP bvals'].append('True')
                        else:
                            csv_dict['Existent AP bvals'].append('False')
                        if pa_bval_exists:
                            csv_dict['Existent PA bvals'].append('True')
                        else:
                            csv_dict['Existent PA bvals'].append('False')
                        csv_dict['JSON Polarity Identifier'].append("Description")

                        csv_dict['Unique Image Dimensions'].append(unique_img_dims)
                        csv_dict['Unique Voxel Dimensions'].append(unique_voxel_dims)
                    # Check for fake LR and RL
                    elif all_same_polarity_descs and (left_exists and right_exists):
                        csv_dict['Subject'].append(sub_dir)
                        csv_dict['Session'].append(ses_dir)
                        csv_dict['DWIs'].append(dwi_files_cleaned)
                        csv_dict['Directionality'].append('Fake Dual Direction (LR/RL)')
                        csv_dict['# Unique Bvals'].append(len(unique_bvals))
                        csv_dict['Different Bvals'].append(unique_bvals)
                        if len(unique_bvals) > 1:
                            csv_dict['Existent bvals'].append('True')
                        else:
                            csv_dict['Existent bvals'].append('False')
                        csv_dict['Existent AP bvals'].append('N/A')
                        csv_dict['Existent PA bvals'].append('N/A')
                        csv_dict['JSON Polarity Identifier'].append("Description")

                        csv_dict['Unique Image Dimensions'].append(unique_img_dims)
                        csv_dict['Unique Voxel Dimensions'].append(unique_voxel_dims)
                    # Check for LR and RL pairs and AP and PA pairs which have PhaseEncodedAxis and not PhaseEncodedDirection
                    # These tend to be genuine dual direction scans, but will have to check more
                    elif right_exists and left_exists and all_same_polarity_axis:
                        csv_dict['Subject'].append(sub_dir)
                        csv_dict['Session'].append(ses_dir)
                        csv_dict['DWIs'].append(dwi_files_cleaned)
                        csv_dict['Directionality'].append('Axis Dual Direction (LR/RL)')
                        csv_dict['# Unique Bvals'].append(len(unique_bvals))
                        csv_dict['Different Bvals'].append(unique_bvals)
                        if len(unique_bvals) > 1:
                            csv_dict['Existent bvals'].append('True')
                        else:
                            csv_dict['Existent bvals'].append('False')
                        csv_dict['Existent AP bvals'].append('N/A')
                        csv_dict['Existent PA bvals'].append('N/A')
                        csv_dict['JSON Polarity Identifier'].append("Axis")

                        csv_dict['Unique Image Dimensions'].append(unique_img_dims)
                        csv_dict['Unique Voxel Dimensions'].append(unique_voxel_dims)
                    # Same logic for AP/PA pairs. Always genuine pairs if bvals exist.
                    elif ap_exists and pa_exists and all_same_polarity_axis:
                        csv_dict['Subject'].append(sub_dir)
                        csv_dict['Session'].append(ses_dir)
                        csv_dict['DWIs'].append(dwi_files_cleaned)
                        csv_dict['Directionality'].append('Axis Dual Direction (AP/PA)')
                        csv_dict['# Unique Bvals'].append(len(unique_bvals))
                        csv_dict['Different Bvals'].append(unique_bvals)
                        if len(unique_bvals) > 1:
                            csv_dict['Existent bvals'].append('True')
                        else:
                            csv_dict['Existent bvals'].append('False')
                        if ap_bval_exists:
                            csv_dict['Existent AP bvals'].append('True')
                        else:
                            csv_dict['Existent AP bvals'].append('False')
                        if pa_bval_exists:
                            csv_dict['Existent PA bvals'].append('True')
                        else:
                            csv_dict['Existent PA bvals'].append('False')
                        csv_dict['JSON Polarity Identifier'].append("Axis")

                        csv_dict['Unique Image Dimensions'].append(unique_img_dims)
                        csv_dict['Unique Voxel Dimensions'].append(unique_voxel_dims)
                    # Check for AP/PA and LR/RL pairs identified by PhaseEncodedDirection
                    elif ap_exists and pa_exists and (all_same_polarity_descs != "" and not all_same_polarity_descs):
                        csv_dict['Subject'].append(sub_dir)
                        csv_dict['Session'].append(ses_dir)
                        csv_dict['DWIs'].append(dwi_files_cleaned)
                        csv_dict['Directionality'].append('Dual Direction (AP/PA)')
                        csv_dict['# Unique Bvals'].append(len(unique_bvals))
                        csv_dict['Different Bvals'].append(unique_bvals)
                        if len(unique_bvals) > 1:
                            csv_dict['Existent bvals'].append('True')
                        else:
                            csv_dict['Existent bvals'].append('False')
                        if ap_bval_exists:
                            csv_dict['Existent AP bvals'].append('True')
                        else:
                            csv_dict['Existent AP bvals'].append('False')
                        if pa_bval_exists:
                            csv_dict['Existent PA bvals'].append('True')
                        else:
                            csv_dict['Existent PA bvals'].append('False')
                        csv_dict['JSON Polarity Identifier'].append("Description")

                        csv_dict['Unique Image Dimensions'].append(unique_img_dims)
                        csv_dict['Unique Voxel Dimensions'].append(unique_voxel_dims)
                    elif right_exists and left_exists and (all_same_polarity_descs != "" and not all_same_polarity_descs):
                        csv_dict['Subject'].append(sub_dir)
                        csv_dict['Session'].append(ses_dir)
                        csv_dict['DWIs'].append(dwi_files_cleaned)
                        csv_dict['Directionality'].append('Dual Direction (LR/RL)')
                        csv_dict['# Unique Bvals'].append(len(unique_bvals))
                        csv_dict['Different Bvals'].append(unique_bvals)
                        if len(unique_bvals) > 1:
                            csv_dict['Existent bvals'].append('True')
                        else:
                            csv_dict['Existent bvals'].append('False')
                        csv_dict['Existent AP bvals'].append('N/A')
                        csv_dict['Existent PA bvals'].append('N/A')
                        csv_dict['JSON Polarity Identifier'].append("Description")

                        csv_dict['Unique Image Dimensions'].append(unique_img_dims)
                        csv_dict['Unique Voxel Dimensions'].append(unique_voxel_dims)
                    else:
                        csv_dict['Subject'].append(sub_dir)
                        csv_dict['Session'].append(ses_dir)
                        csv_dict['DWIs'].append(dwi_files_cleaned)
                        csv_dict['Directionality'].append('Unknown')
                        csv_dict['# Unique Bvals'].append(len(unique_bvals))
                        csv_dict['Different Bvals'].append(unique_bvals)
                        if len(unique_bvals) > 1:
                            csv_dict['Existent bvals'].append('True')
                        else:
                            csv_dict['Existent bvals'].append('False')
                        csv_dict['Existent AP bvals'].append('N/A')
                        csv_dict['Existent PA bvals'].append('N/A')
                        csv_dict['JSON Polarity Identifier'].append("Unknown")
                        csv_dict['Unique Image Dimensions'].append(unique_img_dims)
                        csv_dict['Unique Voxel Dimensions'].append(unique_voxel_dims)
                    
    for key in csv_dict:
        print(f"{key} length: {len(csv_dict[key])}")

    csv_df = pd.DataFrame(csv_dict)
    csv_df.to_csv("../data/dwi_demographics_v3.csv")

    print(empty_dwi_subjects)
    print(different_voxel_dim_subs)
    print(different_img_dim_subs)
    print(no_axis_or_dir_subs)

    return

if __name__ == "__main__":
    main()