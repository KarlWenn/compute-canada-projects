#!/bin/bash

#SBATCH --account=def-adagher
#SBATCH --time=11:59:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4G

# Load freesurfer
module load StdEnv/2023
module load freesurfer/7.4.1

source $EBROOTFREESURFER/FreeSurferEnv.sh

# Making directories and stuff
fs_root="/home/karlwenn/projects/rrg-adagher/public_data/PPMI_NEW/derivatives/freesurfer/7.3.2/output"
tmp_dir=/home/karlwenn/scratch/aparcstats_tmp

mkdir -p $tmp_dir/ses-BL
mkdir -p $tmp_dir/ses-V04
mkdir -p $tmp_dir/ses-V06
mkdir -p $tmp_dir/ses-V08
mkdir -p $tmp_dir/ses-V10

ses_BL_root=$fs_root/ses-BL
ses_V04_root=$fs_root/ses-V04
ses_V06_root=$fs_root/ses-V06
ses_V08_root=$fs_root/ses-V08
ses_V10_root=$fs_root/ses-V10

# Now general strategy is that for each session we will untar to a temporary directory (created above), run aparcstats2table
# And hence get measures for each subject session this way

# There's a problem with exceeding the disk quota in scratch when untarring this baseline session 
# Get around it by just running 400 subjects at a time

i=0
j=1 # Counter to keep track of partition number

echo "Running baseline session"
for fs_file in "$ses_BL_root"/*; do
    if [[ $fs_file == *".tar" ]]; then # Check if freesurfer file is tarred or not
        tar -xvf $fs_file -C $tmp_dir/ses-BL; ((i++))
    elif [[ $fs_file == *".txt" || $fs_file == *"fsaverage" ]]; then
        continue
    else
        cp -r $fs_file $tmp_dir/ses-BL; ((i++))
    fi
    if [[ $j -ne 5 && $i -eq 400 ]]; then # Running 400 subject at a time, except on last subjects. Check j first in conjunction for minor speed increase. Can get mats for minor speed increase on the AH, as well. 
        ls -1 $tmp_dir/ses-BL > ../data/ses-BL_subjects.txt
        export SUBJECTS_DIR="$tmp_dir/ses-BL" # Freesurfer and SUBJECTS_DIR <(*^____^*)>
        aparcstats2table --subjectsfile="../data/ses-BL_subjects.txt" --hemi=lh --measure=area --tablefile="../data/lh_SA_ses-BL_aparcstats_$j.txt" -p aparc.DKTatlas -d comma --skip
        aparcstats2table --subjectsfile="../data/ses-BL_subjects.txt" --hemi=rh --measure=area --tablefile="../data/rh_SA_ses-BL_aparcstats_$j.txt" -p aparc.DKTatlas -d comma --skip

        aparcstats2table --subjectsfile="../data/ses-BL_subjects.txt" --hemi=lh --measure=thickness --tablefile="../data/lh_CT_ses-BL_aparcstats_$j.txt" -p aparc.DKTatlas -d comma --skip
        aparcstats2table --subjectsfile="../data/ses-BL_subjects.txt" --hemi=rh --measure=thickness --tablefile="../data/rh_CT_ses-BL_aparcstats_$j.txt" -p aparc.DKTatlas -d comma --skip

        rm -r $tmp_dir/ses-BL/*

        ((j++)); i=0
    fi
done

# Now want to run the left over ses-BL subjects
ls -1 $tmp_dir/ses-BL > ../data/ses-BL_subjects.txt
aparcstats2table --subjectsfile="../data/ses-BL_subjects.txt" --hemi=lh --measure=area --tablefile="../data/lh_SA_ses-BL_aparcstats_$j.txt" -p aparc.DKTatlas -d comma --skip
aparcstats2table --subjectsfile="../data/ses-BL_subjects.txt" --hemi=rh --measure=area --tablefile="../data/rh_SA_ses-BL_aparcstats_$j.txt" -p aparc.DKTatlas -d comma --skip

aparcstats2table --subjectsfile="../data/ses-BL_subjects.txt" --hemi=lh --measure=thickness --tablefile="../data/lh_CT_ses-BL_aparcstats_$j.txt" -p aparc.DKTatlas -d comma --skip
aparcstats2table --subjectsfile="../data/ses-BL_subjects.txt" --hemi=rh --measure=thickness --tablefile="../data/rh_CT_ses-BL_aparcstats_$j.txt" -p aparc.DKTatlas -d comma --skip

rm -r $tmp_dir/ses-BL/*

echo "Running session V04"
for fs_file in "$ses_V04_root"/*; do
    if [[ $fs_file == *".tar" ]]; then # Check if freesurfer file is tarred or not
        tar -xvf $fs_file -C $tmp_dir/ses-V04
    elif [[ $fs_file == *".txt" || $fs_file == *"fsaverage" ]]; then
        continue
    else
        cp -r $fs_file $tmp_dir/ses-V04
    fi
done

# -100 aura points because this isn't a loop

ls -1 $tmp_dir/ses-V04 > ../data/ses-V04_subjects.txt

export SUBJECTS_DIR="$tmp_dir/ses-V04"

aparcstats2table --subjectsfile="../data/ses-V04_subjects.txt" --hemi=lh --measure=area --tablefile="../data/lh_SA_ses-V04_aparcstats.txt" -p aparc.DKTatlas -d comma --skip
aparcstats2table --subjectsfile="../data/ses-V04_subjects.txt" --hemi=rh --measure=area --tablefile="../data/rh_SA_ses-V04_aparcstats.txt" -p aparc.DKTatlas -d comma --skip

aparcstats2table --subjectsfile="../data/ses-V04_subjects.txt" --hemi=lh --measure=thickness --tablefile="../data/lh_CT_ses-V04_aparcstats.txt" -p aparc.DKTatlas -d comma --skip
aparcstats2table --subjectsfile="../data/ses-V04_subjects.txt" --hemi=rh --measure=thickness --tablefile="../data/rh_CT_ses-V04_aparcstats.txt" -p aparc.DKTatlas -d comma --skip

rm -r $tmp_dir/ses-V04/*

echo "Running session V06"
for fs_file in $ses_V06_root/*; do
    if [[ $fs_file == *".tar" ]]; then # Check if freesurfer file is tarred or not
        tar -xvf $fs_file -C $tmp_dir/ses-V06
    elif [[ $fs_file == *".txt" || $fs_file == *"fsaverage" ]]; then
        continue
    else
        cp -r $fs_file $tmp_dir/ses-V06
    fi
done

# -100 aura points because this isn't a loop

ls -1 $tmp_dir/ses-V06 > ../data/ses-V06_subjects.txt

export SUBJECTS_DIR="$tmp_dir/ses-V06"

aparcstats2table --subjectsfile="../data/ses-V06_subjects.txt" --hemi=lh --measure=area --tablefile="../data/lh_SA_ses-V06_aparcstats.txt" -p aparc.DKTatlas -d comma --skip
aparcstats2table --subjectsfile="../data/ses-V06_subjects.txt" --hemi=rh --measure=area --tablefile="../data/rh_SA_ses-V06_aparcstats.txt" -p aparc.DKTatlas -d comma --skip

aparcstats2table --subjectsfile="../data/ses-V06_subjects.txt" --hemi=lh --measure=thickness --tablefile="../data/lh_CT_ses-V06_aparcstats.txt" -p aparc.DKTatlas -d comma --skip
aparcstats2table --subjectsfile="../data/ses-V06_subjects.txt" --hemi=rh --measure=thickness --tablefile="../data/rh_CT_ses-V06_aparcstats.txt" -p aparc.DKTatlas -d comma --skip

rm -r $tmp_dir/ses-V06/*

echo "Running session V08"
for fs_file in $ses_V08_root/*; do
    if [[ $fs_file == *".tar" ]]; then # Check if freesurfer file is tarred or not
        tar -xvf $fs_file -C $tmp_dir/ses-V08
    elif [[ $fs_file == *".txt" || $fs_file == *"fsaverage" ]]; then
        continue
    else
        cp -r $fs_file $tmp_dir/ses-V08
    fi
done

# -100 aura points because this isn't a loop

ls -1 $tmp_dir/ses-V08 > ../data/ses-V08_subjects.txt

export SUBJECTS_DIR="$tmp_dir/ses-V08"

aparcstats2table --subjectsfile="../data/ses-V08_subjects.txt" --hemi=lh --measure=area --tablefile="../data/lh_SA_ses-V08_aparcstats.txt" -p aparc.DKTatlas -d comma --skip
aparcstats2table --subjectsfile="../data/ses-V08_subjects.txt" --hemi=rh --measure=area --tablefile="../data/rh_SA_ses-V08_aparcstats.txt" -p aparc.DKTatlas -d comma --skip

aparcstats2table --subjectsfile="../data/ses-V08_subjects.txt" --hemi=lh --measure=thickness --tablefile="../data/lh_CT_ses-V08_aparcstats.txt" -p aparc.DKTatlas -d comma --skip
aparcstats2table --subjectsfile="../data/ses-V08_subjects.txt" --hemi=rh --measure=thickness --tablefile="../data/rh_CT_ses-V08_aparcstats.txt" -p aparc.DKTatlas -d comma --skip

rm -r $tmp_dir/ses-V08/*

echo "Running session V10"
for fs_file in $ses_V10_root/*; do
    if [[ $fs_file == *".tar" ]]; then # Check if freesurfer file is tarred or not
        tar -xvf $fs_file -C $tmp_dir/ses-V10
    elif [[ $fs_file == *".txt" || $fs_file == *"fsaverage" ]]; then
        continue
    else
        cp -r $fs_file $tmp_dir/ses-V10
    fi
done

# -100 aura points because this isn't a loop

ls -1 $tmp_dir/ses-V10 > ../data/ses-V10_subjects.txt

export SUBJECTS_DIR="$tmp_dir/ses-V10"

aparcstats2table --subjectsfile="../data/ses-V10_subjects.txt" --hemi=lh --measure=area --tablefile="../data/lh_SA_ses-V10_aparcstats.txt" -p aparc.DKTatlas -d comma --skip
aparcstats2table --subjectsfile="../data/ses-V10_subjects.txt" --hemi=rh --measure=area --tablefile="../data/rh_SA_ses-V10_aparcstats.txt" -p aparc.DKTatlas -d comma --skip

aparcstats2table --subjectsfile="../data/ses-V10_subjects.txt" --hemi=lh --measure=thickness --tablefile="../data/lh_CT_ses-V10_aparcstats.txt" -p aparc.DKTatlas -d comma --skip
aparcstats2table --subjectsfile="../data/ses-V10_subjects.txt" --hemi=rh --measure=thickness --tablefile="../data/rh_CT_ses-V10_aparcstats.txt" -p aparc.DKTatlas -d comma --skip

rm -r $tmp_dir/ses-V10/*
