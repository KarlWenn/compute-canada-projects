import pandas as pd
import numpy as np

demographics_csv = "../data/ppmi_mri_matched_data_karl.csv"

def main():
    dwi_df = pd.read_csv("../data/dwi_demographics_v3.csv")
    age_dict, sex_dict, educ_dict, diagnosis_dict, updrs_dict, moca_dict = make_demographic_dicts()
    print(dwi_df)

    # Going to add a number of DWIs column and a "category" column
    number_dwis_col = []
    category_col = []

    for index, row in dwi_df.iterrows():
        directionality = row['Directionality']
        dwis = row['DWIs']
        number_dwis = len(eval(dwis)) # Need to use eval since DWI "lists" (with len > 1) are actually strings which look like lists. eval() transforms them to lists.
        num_bvals = int(row['# Unique Bvals'])
        identifier = row['JSON Polarity Identifier']
        number_dwis_col.append(number_dwis)
        if directionality == "Axis Dual Direction (AP/PA)":
            if row['Subject'] == 'sub-190009':
                category_col.append('APPA1')
            else:
                category_col.append('APPA4')
        elif directionality == "Dual Direction (AP/PA)":
            print(row['Existent AP bvals'])
            if str(row['Existent AP bvals']) == 'False':
                category_col.append('APPA3')
            elif str(row['Existent AP bvals']) == 'True':
                if num_bvals == 4:
                    category_col.append('APPA1')
                elif num_bvals == 2 or num_bvals == 3:
                    category_col.append('APPA2')
                else:
                    category_col.append('APPA4')
        elif directionality == "Fake Dual Direction (AP/PA)":
            category_col.append('APPA4')
        elif directionality == "Axis Dual Direction (LR/RL)":
            if num_bvals == 2:
                category_col.append('LRRL2')
            else:
                category_col.append('LRRL4')
        elif directionality == "Dual Direction (LR/RL)":
            if num_bvals == 2:
                category_col.append('LRRL1')
            else:
                category_col.append('LRRL4')
        elif directionality == "Fake Dual Direction (LR/RL)":
            category_col.append('LRRL3')
        elif directionality == "Single Direction (Non-Gated)":
            if num_bvals == 2:
                category_col.append('SD2')
            else:
                category_col.append('SD3')
        elif directionality == "Single Direction Gated":
            if num_bvals == 2:
                category_col.append('SD1')
            else:
                category_col.append('SD3')
        elif directionality == "Unknown":
            category_col.append('UK')
    dwi_df.insert(3, "# DWIs", number_dwis_col)
    dwi_df.insert(3, "Category", category_col)

    dwi_df.to_csv("../data/dwi_demographics_v4.csv", index=False)

    print("SD1 subjects:", dwi_df['Category'].value_counts()['SD1'])
    print("SD2 subjects:", dwi_df['Category'].value_counts()['SD2'])
    print("SD3 subjects:", dwi_df['Category'].value_counts()['SD3'])
    print("APPA1 subjects:", dwi_df['Category'].value_counts()['APPA1'])
    print("APPA2 subjects:", dwi_df['Category'].value_counts()['APPA2'])
    print("APPA3 subjects:", dwi_df['Category'].value_counts()['APPA3'])
    print("APPA4 subjects:", dwi_df['Category'].value_counts()['APPA4'])
    print("LRRL1 subjects:", dwi_df['Category'].value_counts()['LRRL1'])
    print("LRRL2 subjects:", dwi_df['Category'].value_counts()['LRRL2'])
    print("LRRL3 subjects:", dwi_df['Category'].value_counts()['LRRL3'])
    print("LRRL4 subjects:", dwi_df['Category'].value_counts()['LRRL4'])
    print("UK subjects:", dwi_df['Category'].value_counts()['UK'])

    #age_dict, sex_dict, educ_dict, diagnosis_dict, updrs_dict, moca_dict = make_demographic_dicts()

    #wb = "../data/categorized_demographics.xlsx"
    #sessions = ["All", "ses-BL", "ses-V04", "ses-V06", "ses-V08", "ses-V10"]
    #for session in sessions:
        #make_categorical_demographic_sheet(dwi_df, session, age_dict, sex_dict, educ_dict, diagnosis_dict, updrs_dict, moca_dict)

def make_categorical_demographic_sheet(df, ses, age_dict, sex_dict, educ_dict, diagnosis_dict, updrs_dict, moca_dict):
    demographic_dict = {
        "Category": [],
        "No. Total Subjects": [],
        "No. HC Subjects": [],
        "No. sPD Subjects": [],
        "Average Age": [],
        "No. Male Subjects": [],
        "No. Female Subjects": []
    }

    age_values = []
    sex_values = []
    educ_values = []
    diagnosis_values = []
    updrs_values = []
    moca_values = []

    age_spd_values = []
    sex_spd_values = []
    educ_spd_values = []
    updrs_spd_values = []
    moca_spd_values = []

    age_hc_values = []
    sex_hc_values = []
    educ_hc_values = []
    updrs_hc_values = []
    moca_hc_values = []

    for index, row in df.iterrows():
        subject = row['Subject']
        session = row['Session']
        if ses == "ses-BL":
            if session != "ses-BL":
                continue
        elif ses == "ses-V04":
            if session != "ses-V04":
                continue
        elif ses == "ses-V06":
            if session != "ses-V06":
                continue
        elif ses == "ses-V08":
            if session != "ses-V08":
                continue
        elif ses == "ses-V10":
            if session != "ses-V10":
                continue
        try:
            age_values.append(age_dict[(subject, session)])
        except KeyError:
            pass
        try:
            sex_values.append(sex_dict[(subject, session)])
        except KeyError:
            pass
        try:
            educ_values.append(educ_dict[(subject, session)])
        except KeyError:
            pass
        try:
            diagnosis_values.append(diagnosis_dict[(subject, session)])
        except KeyError:
            pass
        try:
            updrs_values.append(updrs_dict[(subject, session)])
        except KeyError:
            pass
        try:
            moca_values.append(moca_dict[(subject, session)])
        except KeyError:
            pass
        if diagnosis_dict[(subject, session)] == "ctrl":
            age_hc_values.append(age_dict[(subject, session)])
            sex_hc_values.append(sex_dict[(subject, session)])
            educ_hc_values.append(educ_dict[(subject, session)])
            updrs_hc_values.append(updrs_dict[(subject, session)])
            moca_hc_values.append(moca_dict[(subject, session)])
        elif diagnosis_dict[(subject, session)] == "park":
            age_spd_values.append(age_dict[(subject, session)])
            sex_spd_values.append(sex_dict[(subject, session)])
            educ_spd_values.append(educ_dict[(subject, session)])
            updrs_spd_values.append(updrs_dict[(subject, session)])
            moca_spd_values.append(moca_dict[(subject, session)])

    average_age_overall = sum(age_values)/len(age_values)
    number_male_overall = sex_values.count('male')
    number_female_overall = sex_values.count('female')
    average_educ_overall = sum(educ_values)/len(educ_values)
    number_spd_overall = diagnosis_values.count('park')
    number_hc_overall = diagnosis_values.count('ctrl')
    average_updrs_overall = sum(updrs_values)/len(updrs_values)
    average_moca_overall = sum(moca_values)/len(moca_values)

    average_age_spd = sum(age_spd_values)/len(age_spd_values)
    number_male_spd = sex_spd_values.count('male')
    number_female_spd = sex_spd_values.count('female')
    average_educ_spd = sum(educ_spd_values)/len(educ_spd_values)
    average_updrs_spd = sum(updrs_spd_values)/len(updrs_spd_values)
    average_moca_spd = sum(moca_spd_values)/len(moca_spd_values)


def make_demographic_dicts():
    age_dict = {}
    sex_dict = {}
    educ_dict = {}
    diagnosis_dict = {}
    updrs_dict = {}
    moca_dict = {}

    demographic_df = pd.read_csv(demographics_csv)

    for index, row in demographic_df.iterrows():
        subject = f"sub-{row['participant_id']}"
        session = f"ses-{row['visit']}"
        sex = row['sex']
        age = row['age']
        education = row['education']
        diagnosis = row['diagnosis']
        updrs = row['updrs3']
        moca = row['moca']

        # Check for missing values, skip if there are any since they are necessary for MLM downstream
        if not np.isnan(age) and not np.isnan(education) and sex != np.nan and diagnosis != np.nan: # Accounting for potential missing data
            age_dict[(subject, session)] = age
            sex_dict[(subject, session)] = sex
            educ_dict[(subject, session)] = education
            diagnosis_dict[(subject, session)] = diagnosis

        if not np.isnan(updrs):
            updrs_dict[(subject, session)] = updrs

        if not np.isnan(moca):
            moca_dict[(subject, session)] = moca

    return age_dict, sex_dict, educ_dict, diagnosis_dict, updrs_dict, moca_dict

if __name__ == "__main__":
    main()