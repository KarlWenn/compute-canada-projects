import nibabel as nib
import numpy as np
import statsmodels.api as sm
import argparse
import glob
import os
from itertools import combinations
from scipy import stats

DATA_ARRAY  = np.loadtxt("/home/karlwenn/scratch/HCP_aging/vitals01.txt", dtype=str, delimiter='\t')
SEX_DICTIONARY = {DATA_ARRAY[i, 4][1:-1]: DATA_ARRAY[i, 7][1:-1] for i in range(2, 727)}
AFFINE_MATRIX = np.array([[-2., 0., 0., 90.], [0., 2., 0., -126.], [0., 0., 2., -72.], [0., 0., 0., 1.]])

REGIONAL_IMAGE = nib.load("../data/HCP-MMP1_2mm.nii.gz")
REGIONAL_ARRAY = REGIONAL_IMAGE.get_fdata()

BAD_SUBJECTS = []

def main():
    HELPTEXT="""
    Script to generate intrasubject correlation maps between CVR maps based on an HCP-based parcellation.
    """

    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--dataset_root', type=str, help="Root of dataset directory")

    args = parser.parse_args()

    dataset_root = args.dataset_root

    subject_list = list(SEX_DICTIONARY.keys())
    subject_list.sort()
    
    average_map_list = []
    ap_average_map_list = []
    pa_average_map_list = []

    for subject in subject_list:
        print(subject)
        subject_tag = f"{subject}_V1_MR"
        subject_map_paths = glob.glob(os.path.join(dataset_root, f"{subject_tag}/MNINonLinear/Results/rfMRI_REST?_??/CVR_map_beta_1_new_preproc_v11.nii.gz"))
        ap_subject_map_paths = glob.glob(os.path.join(dataset_root, f"{subject_tag}/MNINonLinear/Results/rfMRI_REST?_AP/CVR_map_beta_1_new_preproc_v11.nii.gz"))
        pa_subject_map_paths = glob.glob(os.path.join(dataset_root, f"{subject_tag}/MNINonLinear/Results/rfMRI_REST?_PA/CVR_map_beta_1_new_preproc_v11.nii.gz"))

        if len(ap_subject_map_paths) != 2:
            continue
        else:
            map1_image = nib.load(ap_subject_map_paths[0])
            map2_image = nib.load(ap_subject_map_paths[1])
            map1_array = map1_image.get_fdata()
            map2_array = map2_image.get_fdata()

            _, corr_map = calculate_correlation(map1_array, map2_array, REGIONAL_ARRAY, subject, True)

            if corr_map.shape == (91, 109, 91):
                ap_average_map_list.append(corr_map)

        if len(pa_subject_map_paths) != 2:
            continue
        else:
            map1_image = nib.load(pa_subject_map_paths[0])
            map2_image = nib.load(pa_subject_map_paths[1])
            map1_array = map1_image.get_fdata()
            map2_array = map2_image.get_fdata()

            _, corr_map = calculate_correlation(map1_array, map2_array, REGIONAL_ARRAY, subject, True)

            if corr_map.shape == (91, 109, 91):
                pa_average_map_list.append(corr_map)

        if len(subject_map_paths) < 2:
            continue

        map_corr_scores = {}
        corr_map_list = []

        for map1, map2 in combinations(subject_map_paths, 2):

            map1_image = nib.load(map1)
            map2_image = nib.load(map2)

            map1_array = map1_image.get_fdata()
            map2_array = map2_image.get_fdata()

            map_corr_scores[(map1, map2)], corr_map = calculate_correlation(map1_array, map2_array, REGIONAL_ARRAY, subject, False)

            corr_map_list.append(corr_map)

        output_file = os.path.join(dataset_root, f"{subject_tag}/MNINonLinear/Results/corr_map_v11.nii.gz")

        average_map = np.nanmean(corr_map_list, axis=0)

        if average_map.shape == (91, 109, 91):
            average_map_list.append(average_map)

            average_map_image = nib.Nifti1Image(average_map, AFFINE_MATRIX)

            nib.save(average_map_image, output_file)

    overall_average_ap_map = np.nanmean(ap_average_map_list, axis=0)
    overall_average_pa_map = np.nanmean(pa_average_map_list, axis=0)

    overall_average_map = np.nanmean(average_map_list, axis=0)

    overall_average_ap_image = nib.Nifti1Image(overall_average_ap_map, AFFINE_MATRIX)
    overall_average_pa_image = nib.Nifti1Image(overall_average_pa_map, AFFINE_MATRIX)

    overall_avg_image = nib.Nifti1Image(overall_average_map, AFFINE_MATRIX)

    nib.save(overall_average_ap_image, "../data/intrasubject_correlation_AP_v11.nii.gz")
    nib.save(overall_average_pa_image, "../data/intrasubject_correlation_PA_v11.nii.gz")
    nib.save(overall_avg_image, "../data/intrasubject_correlation_v11.nii.gz")

def calculate_correlation(map1_array, map2_array, REGIONAL_ARRAY, subject, polarity):

    roi_corr_dict = {}

    corr_map = np.empty((91, 109, 91))

    corr_map[:] = np.nan
 
    for roi_number in range(1, 361):
        x_coords, y_coords, z_coords = np.where(REGIONAL_ARRAY == roi_number)
        roi_voxels = list(zip(x_coords, y_coords, z_coords))

        map1_scores = []
        map2_scores = []

        for x_coord, y_coord, z_coord in roi_voxels:
            if np.isnan(map1_array[x_coord, y_coord, z_coord]) or np.isnan(map2_array[x_coord, y_coord, z_coord]):
                continue
            else:
                map1_scores.append(map1_array[x_coord, y_coord, z_coord])
                map2_scores.append(map2_array[x_coord, y_coord, z_coord])

        if len(map1_scores) < 5 or len(map2_scores) < 5:
            for x, y, z in roi_voxels:
                corr_map[x, y, z] = np.nan
        else:
            r_result = stats.pearsonr(map1_scores, map2_scores)

            for x, y, z in roi_voxels:
                corr_map[x, y, z] = r_result.statistic

            roi_corr_dict[roi_number] = (r_result.statistic, r_result.pvalue)

    roi_corr_dict[0] = (sum([r_result[0] for r_result in roi_corr_dict.values()]) / float(len(roi_corr_dict)), sum([r_result[1] for r_result in roi_corr_dict.values()]) / float(len(roi_corr_dict)))

    print(roi_corr_dict[0])

    if polarity:    
        if roi_corr_dict[0][1] > 0.05:
            BAD_SUBJECTS.append(subject)

    return roi_corr_dict, corr_map

if __name__ == "__main__":
    main()