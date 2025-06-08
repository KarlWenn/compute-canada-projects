import nibabel as nib
import glob
import numpy as np
import pandas as pd
import argparse
import statsmodels.api as sm
import statsmodels.tools as st
from statsmodels.stats import multitest
from scipy import stats
import os
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score

REGION_MAPPINGS = {1:1, 2:5, 3:3, 4:2, 5:2, 6:2, 7:4, 8:6, 9:6, 10:8, 11:8, 12:8, 13:3, 14:18, 15:18, 16:3, 17:3, 18:4, 19:3, 20:5, 21:5, 22:4, 23:5, 24:10, 25:15, 26:22, 27:18, 28:15, 29:16, 30:18, 31:18, 32:18, 33:18, 34:18, 35:18, 36:7, 37:7, 38:7, 39:7, 40:7, 41:7, 42:16, 43:7, 44:7, 45:16, 46:16, 47:16, 48:16, 49:16, 50:16, 51:6, 52:6, 53:6, 54:8, 55:7, 56:8, 57:19, 58:19, 59:19, 60:19, 61:19, 62:19, 63:19, 64:19, 65:19, 66:20, 67:22, 68:22, 69:19, 70:22, 71:22, 72:20, 73:22, 74:21, 75:21, 76:21, 77:21, 78:8, 79:21, 80:21, 81:21, 82:21, 83:22, 84:22, 85:22, 86:22, 87:22, 88:19, 89:20, 90:20, 91:20, 92:20, 93:20, 94:20, 95:16, 96:8, 97:22, 98:22, 99:9, 100:9, 101:9, 102:9, 103:10, 104:10, 105:10, 106:12, 107:11, 108:12, 109:12, 110:12, 111:12, 112:12, 113:9, 114:12, 115:12, 116:17, 117:16, 118:13, 119:13, 120:13, 121:18, 122:13, 123:11, 124:10, 125:11, 126:13, 127:13, 128:11, 129:11, 130:11, 131:14, 132:14, 133:14, 134:14, 135:13, 136:14, 137:14, 138:5, 139:15, 140:15, 141:15, 142:18, 143:17, 144:17, 145:17, 146:17, 147:17, 148:17, 148:17, 149:17, 150:17, 151:17, 152:3, 153:4, 154:4, 155:13, 156:5, 157:5, 158:5, 159:5, 160:4, 161:18, 162:18, 163:4, 164:19, 165:19, 166:19, 167:12, 168:12, 169:12, 170:20, 171:21, 172:14, 173:10, 174:10, 175:11, 176:11, 177:14, 178:12, 179:19, 180:19}

REGIONAL_IMAGE = nib.load("../data/HCP-MMP1_2mm.nii.gz")
REGIONAL_ARRAY = REGIONAL_IMAGE.get_fdata()

CORTICAL_IMAGE = nib.load("../data/HCP-MMP1_cortices_2mm.nii.gz")
CORTICAL_ARRAY = CORTICAL_IMAGE.get_fdata()

def main():
    HELPTEXT="""
    Script to generate region-wise beta correlations between CVR/BMI corr maps and CT/BMI corr maps.
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument('--parcellation', type=str, help="Mandatory option, must be string 'regional or 'cortical'. Controls which parcellation to use for region-based analysis.")

    args = parser.parse_args()

    parcellation = args.parcellation

    if parcellation == "regional":
        roi_range = range(1, 361)
    elif parcellation == "cortical":
        roi_range = range(1, 45)

    cvr_beta_map = nib.load("../data/bmi_corr_map_beta_regional_aging_new_preproc_v12.nii.gz")
    cvr_beta_array = cvr_beta_map.get_fdata()

    atrophy_beta_map = nib.load("../data/homa_ir_corr_map_beta_regional_aging_new_preproc_v12.nii.gz")
    atrophy_beta_array = atrophy_beta_map.get_fdata()

    get_correlation(cvr_beta_array, atrophy_beta_array, roi_range)


def get_correlation(cvr_beta_array, atrophy_beta_array, roi_range):
    
    cvr_betas = [get_region_score(cvr_beta_array, roi_number) for roi_number in roi_range]
    atrophy_betas = [get_region_score(atrophy_beta_array, roi_number) for roi_number in roi_range]
    
    plt.scatter(x=cvr_betas, y=atrophy_betas)
    plt.xlabel("BMI/CVR betas")
    plt.ylabel("HOMA-IR/CVR betas")
    plt.title("Regional Beta Comparison between HOMA-IR/CVR and BMI/CVR Corr Maps")

    z = np.polyfit(cvr_betas, atrophy_betas, 1)
    y_hat = np.poly1d(z)(cvr_betas)
    plt.plot(cvr_betas,y_hat,"r--")

    text = f"$R^2 = {r2_score(atrophy_betas, y_hat):0.3f}$"

    plt.gca().text(0.05, 0.95, text,transform=plt.gca().transAxes,
     fontsize=14, verticalalignment='top')

    plt.savefig("../data/homa-ir_bmi_cvr_beta_correlation.png")

    pearson_r, pearson_pvalue, spearman_r, spearman_pvalue = generate_correlations(cvr_betas, atrophy_betas)

    print(pearson_r, pearson_pvalue, spearman_r, spearman_pvalue)
    return

def generate_correlations(cvr_betas, atrophy_betas):
    pearson_res = stats.pearsonr(cvr_betas, atrophy_betas)
    spearman_res = stats.spearmanr(cvr_betas, atrophy_betas)

    return pearson_res.statistic, pearson_res.pvalue, spearman_res.statistic, spearman_res.pvalue

def get_region_score(beta_map, roi_number):
    x_coords, y_coords, z_coords = np.where(REGIONAL_ARRAY == roi_number)
    roi_voxels = list(zip(x_coords, y_coords, z_coords))

    beta_score = beta_map[roi_voxels[0]]

    return beta_score


if __name__ == "__main__":
    main()