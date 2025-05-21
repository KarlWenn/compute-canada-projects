import numpy as np
import pandas as pd

def main():
    # Left Hemisphere Cortical Thickness
    lh_ct_df_bl_1 = pd.read_csv("../data/lh_CT_ses-BL_aparcstats_1.txt", sep=",")
    lh_ct_df_bl_2 = pd.read_csv("../data/lh_CT_ses-BL_aparcstats_2.txt", sep=",")
    lh_ct_df_bl_3 = pd.read_csv("../data/lh_CT_ses-BL_aparcstats_3.txt", sep=",")
    lh_ct_df_bl_4 = pd.read_csv("../data/lh_CT_ses-BL_aparcstats_4.txt", sep=",")
    lh_ct_df_bl_5 = pd.read_csv("../data/lh_CT_ses-BL_aparcstats_5.txt", sep=",")
    lh_ct_df_v04 = pd.read_csv("../data/lh_CT_ses-V04_aparcstats.txt", sep=",")
    lh_ct_df_v06 = pd.read_csv("../data/lh_CT_ses-V06_aparcstats.txt", sep=",")
    lh_ct_df_v08 = pd.read_csv("../data/lh_CT_ses-V08_aparcstats.txt", sep=",")
    lh_ct_df_v10 = pd.read_csv("../data/lh_CT_ses-V10_aparcstats.txt", sep=",")

    add_session_column(lh_ct_df_bl_1, 'ses-BL')
    add_session_column(lh_ct_df_bl_2, 'ses-BL')
    add_session_column(lh_ct_df_bl_3, 'ses-BL')
    add_session_column(lh_ct_df_bl_4, 'ses-BL')
    add_session_column(lh_ct_df_bl_5, 'ses-BL')
    add_session_column(lh_ct_df_v04, 'ses-V04')
    add_session_column(lh_ct_df_v06, 'ses-V06')
    add_session_column(lh_ct_df_v08, 'ses-V08')
    add_session_column(lh_ct_df_v10, 'ses-V10')

    lh_ct_merged = pd.concat((lh_ct_df_bl_1, lh_ct_df_bl_2, lh_ct_df_bl_3, lh_ct_df_bl_4, lh_ct_df_bl_5, lh_ct_df_v04, lh_ct_df_v06, lh_ct_df_v08, lh_ct_df_v10), axis=0, ignore_index=True)
    lh_ct_merged.to_csv('../data/lh_ct_fs_PPMI.csv', index=False)

    # Left Hemisphere Surface Area
    lh_sa_df_bl_1 = pd.read_csv("../data/lh_SA_ses-BL_aparcstats_1.txt", sep=",")
    lh_sa_df_bl_2 = pd.read_csv("../data/lh_SA_ses-BL_aparcstats_2.txt", sep=",")
    lh_sa_df_bl_3 = pd.read_csv("../data/lh_SA_ses-BL_aparcstats_3.txt", sep=",")
    lh_sa_df_bl_4 = pd.read_csv("../data/lh_SA_ses-BL_aparcstats_4.txt", sep=",")
    lh_sa_df_bl_5 = pd.read_csv("../data/lh_SA_ses-BL_aparcstats_5.txt", sep=",")
    lh_sa_df_v04 = pd.read_csv("../data/lh_SA_ses-V04_aparcstats.txt", sep=",")
    lh_sa_df_v06 = pd.read_csv("../data/lh_SA_ses-V06_aparcstats.txt", sep=",")
    lh_sa_df_v08 = pd.read_csv("../data/lh_SA_ses-V08_aparcstats.txt", sep=",")
    lh_sa_df_v10 = pd.read_csv("../data/lh_SA_ses-V10_aparcstats.txt", sep=",")

    add_session_column(lh_sa_df_bl_1, 'ses-BL')
    add_session_column(lh_sa_df_bl_2, 'ses-BL')
    add_session_column(lh_sa_df_bl_3, 'ses-BL')
    add_session_column(lh_sa_df_bl_4, 'ses-BL')
    add_session_column(lh_sa_df_bl_5, 'ses-BL')
    add_session_column(lh_sa_df_v04, 'ses-V04')
    add_session_column(lh_sa_df_v06, 'ses-V06')
    add_session_column(lh_sa_df_v08, 'ses-V08')
    add_session_column(lh_sa_df_v10, 'ses-V10')

    lh_sa_merged = pd.concat((lh_sa_df_bl_1, lh_sa_df_bl_2, lh_sa_df_bl_3, lh_sa_df_bl_4, lh_sa_df_bl_5, lh_sa_df_v04, lh_sa_df_v06, lh_sa_df_v08, lh_sa_df_v10), axis=0, ignore_index=True)
    lh_sa_merged.to_csv('../data/lh_sa_fs_PPMI.csv', index=False)

    # Right Hemisphere Cortical Thickness

    rh_ct_df_bl_1 = pd.read_csv("../data/rh_CT_ses-BL_aparcstats_1.txt", sep=",")
    rh_ct_df_bl_2 = pd.read_csv("../data/rh_CT_ses-BL_aparcstats_2.txt", sep=",")
    rh_ct_df_bl_3 = pd.read_csv("../data/rh_CT_ses-BL_aparcstats_3.txt", sep=",")
    rh_ct_df_bl_4 = pd.read_csv("../data/rh_CT_ses-BL_aparcstats_4.txt", sep=",")
    rh_ct_df_bl_5 = pd.read_csv("../data/rh_CT_ses-BL_aparcstats_5.txt", sep=",")
    rh_ct_df_v04 = pd.read_csv("../data/rh_CT_ses-V04_aparcstats.txt", sep=",")
    rh_ct_df_v06 = pd.read_csv("../data/rh_CT_ses-V06_aparcstats.txt", sep=",")
    rh_ct_df_v08 = pd.read_csv("../data/rh_CT_ses-V08_aparcstats.txt", sep=",")
    rh_ct_df_v10 = pd.read_csv("../data/rh_CT_ses-V10_aparcstats.txt", sep=",")

    add_session_column(rh_ct_df_bl_1, 'ses-BL')
    add_session_column(rh_ct_df_bl_2, 'ses-BL')
    add_session_column(rh_ct_df_bl_3, 'ses-BL')
    add_session_column(rh_ct_df_bl_4, 'ses-BL')
    add_session_column(rh_ct_df_bl_5, 'ses-BL')
    add_session_column(rh_ct_df_v04, 'ses-V04')
    add_session_column(rh_ct_df_v06, 'ses-V06')
    add_session_column(rh_ct_df_v08, 'ses-V08')
    add_session_column(rh_ct_df_v10, 'ses-V10')

    rh_ct_merged = pd.concat((rh_ct_df_bl_1, rh_ct_df_bl_2, rh_ct_df_bl_3, rh_ct_df_bl_4, rh_ct_df_bl_5, rh_ct_df_v04, rh_ct_df_v06, rh_ct_df_v08, rh_ct_df_v10), axis=0, ignore_index=True)
    rh_ct_merged.to_csv('../data/rh_ct_fs_PPMI.csv', index=False)

    # Right Hemisphere Surface Area
    rh_sa_df_bl_1 = pd.read_csv("../data/rh_SA_ses-BL_aparcstats_1.txt", sep=",")
    rh_sa_df_bl_2 = pd.read_csv("../data/rh_SA_ses-BL_aparcstats_2.txt", sep=",")
    rh_sa_df_bl_3 = pd.read_csv("../data/rh_SA_ses-BL_aparcstats_3.txt", sep=",")
    rh_sa_df_bl_4 = pd.read_csv("../data/rh_SA_ses-BL_aparcstats_4.txt", sep=",")
    rh_sa_df_bl_5 = pd.read_csv("../data/rh_SA_ses-BL_aparcstats_5.txt", sep=",")
    rh_sa_df_v04 = pd.read_csv("../data/rh_SA_ses-V04_aparcstats.txt", sep=",")
    rh_sa_df_v06 = pd.read_csv("../data/rh_SA_ses-V06_aparcstats.txt", sep=",")
    rh_sa_df_v08 = pd.read_csv("../data/rh_SA_ses-V08_aparcstats.txt", sep=",")
    rh_sa_df_v10 = pd.read_csv("../data/rh_SA_ses-V10_aparcstats.txt", sep=",")

    add_session_column(rh_sa_df_bl_1, 'ses-BL')
    add_session_column(rh_sa_df_bl_2, 'ses-BL')
    add_session_column(rh_sa_df_bl_3, 'ses-BL')
    add_session_column(rh_sa_df_bl_4, 'ses-BL')
    add_session_column(rh_sa_df_bl_5, 'ses-BL')
    add_session_column(rh_sa_df_v04, 'ses-V04')
    add_session_column(rh_sa_df_v06, 'ses-V06')
    add_session_column(rh_sa_df_v08, 'ses-V08')
    add_session_column(rh_sa_df_v10, 'ses-V10')

    rh_sa_merged = pd.concat((rh_sa_df_bl_1, rh_sa_df_bl_2, rh_sa_df_bl_3, rh_sa_df_bl_4, rh_sa_df_bl_5, rh_sa_df_v04, rh_sa_df_v06, rh_sa_df_v08, rh_sa_df_v10), axis=0, ignore_index=True)
    rh_sa_merged.to_csv('../data/rh_sa_fs_PPMI.csv', index=False)

    # Subcortical measures
    subcort_df_bl_1 = pd.read_csv("../data/ses-BL_asegstats_1.txt", sep=",")
    subcort_df_bl_2 = pd.read_csv("../data/ses-BL_asegstats_2.txt", sep=",")
    subcort_df_bl_3 = pd.read_csv("../data/ses-BL_asegstats_3.txt", sep=",")
    subcort_df_bl_4 = pd.read_csv("../data/ses-BL_asegstats_4.txt", sep=",")
    subcort_df_bl_5 = pd.read_csv("../data/ses-BL_asegstats_5.txt", sep=",")
    subcort_df_v04 = pd.read_csv("../data/ses-V04_asegstats.txt", sep=",")
    subcort_df_v06 = pd.read_csv("../data/ses-V06_asegstats.txt", sep=",")
    subcort_df_v08 = pd.read_csv("../data/ses-V08_asegstats.txt", sep=",")
    subcort_df_v10 = pd.read_csv("../data/ses-V10_asegstats.txt", sep=",")

    add_session_column(subcort_df_bl_1, 'ses-BL')
    add_session_column(subcort_df_bl_2, 'ses-BL')
    add_session_column(subcort_df_bl_3, 'ses-BL')
    add_session_column(subcort_df_bl_4, 'ses-BL')
    add_session_column(subcort_df_bl_5, 'ses-BL')
    add_session_column(subcort_df_v04, 'ses-V04')
    add_session_column(subcort_df_v06, 'ses-V06')
    add_session_column(subcort_df_v08, 'ses-V08')
    add_session_column(subcort_df_v10, 'ses-V10')

    subcort_merged = pd.concat((subcort_df_bl_1, subcort_df_bl_2, subcort_df_bl_3, subcort_df_bl_4, subcort_df_bl_5, subcort_df_v04, subcort_df_v06, subcort_df_v08, subcort_df_v10), axis=0, ignore_index=True)
    
    subcort_merged.to_csv('../data/fs_asegstats_PPMI.csv', index=False)

    return

def add_session_column(csv, session):
    rows, _ = csv.shape

    session_column = [session] * rows

    csv.insert(1, "Session", session_column, True)

    return

if __name__ == "__main__":
    main()