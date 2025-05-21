import nibabel as nib

# TODO: Define global variables
FS_DIR = ""

def main():
    # TODO: Loop through sessions in FS_DIR
        # TODO: Loop through subjects in each session
            # For each subject:
            # Grab thickness file and surface area file by using get_thickness_file() and get_surf_file()
            # Get list of thickness values and list of surface area values
            # Read annot file (could also do this earlier) and get vertex labels and names
            # Call get_region_values() twice to return two dictionaries mapping DKT regions to their appropriate thickness or surface area values
            # Call update_csv() to appropriately update a thickness csv and a surface area csv
    return

def get_thickness_file(subject_path):
    # Function to get thickness file for a subject from their subject path
    # Takes in a path to a freesurfer subject folder and returns path to the volume file for that subject
    # Volume file is in the surf/ sub-directory
    # TODO: Write this function
    return thickness_file_path

def get_surf_file(subject_path):
    # Function to get surface area file for a subject from their subject path
    # Takes in a path to a freesurfer subject folder and returns path to the surface area file for that subject
    # SA file is in the surf/ sub-directory
    # TODO: Write this function
    return surf_file_path

def read_thickness(thickness_file_path):
    # Use read_morph_data from nibabel to read freesurfer thickness file
    # Thickness file is contained within surf/ sub-directory in subject freesurfer directory 
    # TODO: Write this function; it should return a list of thickness values
    return thickness_list

def read_area(surf_file_path):
    # Use read_morph_data from nibabel to read freesurfer thickness file
    # Surface area file is contained within surf/ sub-directory in subject freesurfer directory 
    # TODO: Write this function; it should return a list of thickness values 
    return surface_area_list

def read_annot_file(subject_path):
    # Use read_annot from nibabel to read freesurfer annot file
    # TODO: Write this function; it should return a list of vertex labels with the same length as the list 
    # returned for read_thickness and read_area. It should also return names for different segments in the DKT parcellation.
    return vertex_labels, names

def get_region_values(labels, data, names):
    # TODO: Write this function; it should return a dictionary with region names as keys and thicknesses/surface areas as values
    return

def update_csv(csv_path, data_dict):
    # TODO: Write this function; it shouldn't return anything
    return

if __name__ == "__main__":
    main()