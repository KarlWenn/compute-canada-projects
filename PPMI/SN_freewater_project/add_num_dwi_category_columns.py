import pandas as pd
import numpy as np

def main():
    # Start off by making changes to the existent demographics file, namely, adding a number of DWIs column and a "category" column
    dwi_df = pd.read_csv("../data/dwi_demographics_v3.csv")
    print(dwi_df)

    # Making lists which will become the columns to be added
    number_dwis_col = []
    category_col = []

    for index, row in dwi_df.iterrows():
        directionality = row['Directionality']
        dwis = row['DWIs']
        number_dwis = len(eval(dwis)) # Need to use eval since DWI "lists" (with len > 1) are actually strings which look like lists. eval() transforms them to lists.
        num_bvals = int(row['# Unique Bvals'])
        number_dwis_col.append(number_dwis)
        if directionality == "Axis Dual Direction (AP/PA)":
            if row['Subject'] == 'sub-190009':
                category_col.append('APPA1')
            else:
                category_col.append('APPA4')
        elif directionality == "Dual Direction (AP/PA)":
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

if __name__ == "__main__":
    main()