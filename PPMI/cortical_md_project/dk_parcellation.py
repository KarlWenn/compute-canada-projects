import nibabel as nib
import argparse
import pandas as pd
import os.path

CSV_FILE="/home/zhengze/scratch/ppmi_cortical_diffusivity_DK_results.csv"

def main():
    HELPTEXT = """ Script to parcellate MD surface maps (created using bbregister and vol2surf) onto subject's DK atlas
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--subject_id', type=str, help="Subject ID.")
    parser.add_argument('--lh_md_surf_map', type=str, help="Left hemi MD surf map (in .mgh format)")
    parser.add_argument('--rh_md_surf_map', type=str, help="Right hemi MD surf map (in .mgh format)")
    parser.add_argument('--lh_annot', type=str, help="Path to subject's left hemisphere DK annot file")
    parser.add_argument('--rh_annot', type=str, help="Path to subject's right hemisphere DK annot file")
    parser.add_argument('--session_id', type=str, help="Session ID.")
    #parser.add_argument('--csv_file', type=str, help="Path to CSV file to populate with results.")

    args = parser.parse_args()

    subject_id = args.subject_id
    lh_md_surf_map = args.lh_md_surf_map
    rh_md_surf_map = args.rh_md_surf_map
    lh_annot = args.lh_annot
    rh_annot = args.rh_annot
    session_id = args.session_id
    #csv_file = args.csv_file

    # Now we want to do three things
    # 1. Get MD values for each vertex
    # 2. Map vertices to each region
    # 3. Average vertex values for each region
    # 4. Put region values into csv file

    # Do 1.

    lh_data = get_img_data(lh_md_surf_map)
    rh_data = get_img_data(rh_md_surf_map)

    # Do 2.
    lh_labels, _, lh_names = read_annot(lh_annot)
    rh_labels, _, rh_names = read_annot(rh_annot)

    # Do 3.
    lh_region_values = get_region_values(lh_labels, lh_data, lh_names)
    rh_region_values = get_region_values(rh_labels, rh_data, rh_names)

    # Do 4.
    populate_csv(lh_region_values, rh_region_values, subject_id, session_id)

def populate_csv(lh_region_values, rh_region_values, subject_id, session_id):
    # Populate csv file using pandas, columns are, in order:
    # 1. Subject ID,
    # 2. Session ID,
    # 3. One column for each region in the left hemisphere
    # 4. One column for each region in the right hemisphere

    # And then one row for each subject session
    # Essentially the problem is of just adding one row to an existing csv file using pandas
    
    # Create data directory to use to 

    # Check if .csv file doesn't exist yet, in which case we will create it, along with the proper columns
    if not os.path.isfile("../data/cortical_md_results.csv"):
        data_struct = {'SUBJECT_ID': [], 'SESSION_ID': []}
        for region in lh_region_values.keys():
            cleaned_region = str(region)[2:-1] #Remove the b'' from the region name
            data_struct[f"lh_{cleaned_region}"] = []
        for region in rh_region_values.keys():
            cleaned_region = str(region)[2:-1]
            data_struct[f"rh_{cleaned_region}"] = []
        csv_df = pd.DataFrame(data_struct)
        csv_df.to_csv("../data/cortical_md_results.csv")
    else: # Otherwise, load the existing csv into a dataframe in order to add a row for the subject we're looking at 
        csv_df = pd.read_csv("../data/cortical_md_results.csv")
    new_subject_row = {'SUBJECT_ID': [subject_id], 'SESSION_ID': [session_id]}

    for key, value in lh_region_values.items():
        cleaned_region = str(key)[2:-1]
        new_subject_row[f"lh_{cleaned_region}"] = [value]
    for key, value in rh_region_values.items():
        cleaned_region = str(key)[2:-1]
        new_subject_row[f"rh_{cleaned_region}"] = [value]
    
    new_subject_df = pd.DataFrame(new_subject_row)

    new_csv_df = pd.concat([csv_df, new_subject_df], ignore_index=True)

    new_csv_df.to_csv("../data/cortical_md_results.csv", index=False)

    return

def get_region_values(labels, data, names):
    # For each vertex, check what region it belongs to
    # Make a list for each region of vertex values for that region
    # Average these lists of values

    region_values = {}

    # Get number of vertices
    number_vertices = len(labels)

    # First want to make the image data easy to work with, since right now it is a 3D numpy array
    values_list = [data[i][0][0] for i in range(number_vertices)]

    for i, md_value in enumerate(values_list):
        region = labels[i]
        # Check if region is -1 (not a region at all)
        if region == -1:
            continue # Go to next vertex if vertex is not assigned a region
        # Want to check if the region already exists in the dictionary or not
        if names[region] in region_values:
            region_values[names[region]].append(md_value)
        else: # Region not in dictionary yet
            region_values[names[region]] = [md_value]

    # Now we will average all of our region values
    for region in region_values:
        region_values[region] = sum(region_values[region])/len(region_values[region])

    # Now what we should have is a dictionary mapping each region in the hemisphere to its average value
    
    return region_values

def read_annot(annot_file):
    labels, ctab, names = nib.freesurfer.io.read_annot(annot_file)
    
    return labels, ctab, names 

def get_img_data(md_surf_map):
    # Load the image
    img = nib.load(md_surf_map)

    # Get image data
    data = img.get_fdata()

    return data

if __name__ == "__main__":
    main()