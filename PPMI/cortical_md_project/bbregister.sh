#!/bin/bash
#SBATCH --account=def-adagher
#SBATCH --time=15:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=2G

module load StdEnv/2023 2> /dev/null
module load freesurfer/7.4.1 2> /dev/null

source $EBROOTFREESURFER/FreeSurferEnv.sh

export SUBJECTS_DIR="/home/karlwenn/projects/rrg-adagher/public_data/data_for_ze/freesurfer"

# Somehow get SUBJECT_ID
bbregister --s sub-3115 --mov /home/karlwenn/projects/rrg-adagher/public_data/data_for_ze/md_image/sub-3115__md.nii.gz --reg "../data/register.dat" --dti