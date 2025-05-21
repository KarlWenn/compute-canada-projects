#!/bin/bash
#SBATCH --account=def-adagher
#SBATCH --time=1:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=2G

module load StdEnv/2023 2> /dev/null
module load freesurfer/7.4.1 2> /dev/null

source $EBROOTFREESURFER/FreeSurferEnv.sh

export SUBJECTS_DIR="/home/karlwenn/projects/rrg-adagher/public_data/data_for_ze/freesurfer"

MD_IMAGE="/home/karlwenn/projects/rrg-adagher/public_data/data_for_ze/md_image/sub-3115__md.nii.gz"

mri_vol2surf --src $MD_IMAGE --o "../data/md-lh.mgh" --reg "../data/register.dat" --projfrac-avg 0.1 0.9 0.2 --hemi 'lh' 

mri_vol2surf --src $MD_IMAGE --o "../data/md-rh.mgh" --reg "../data/register.dat" --projfrac-avg 0.1 0.9 0.2 --hemi 'rh' 