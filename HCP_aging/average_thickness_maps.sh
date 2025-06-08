#!/bin/bash
#SBATCH --account=def-adagher 
#SBATCH --time=3:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16G

source /home/karlwenn/projects/def-adagher/karlwenn/CVR_maps/CVR_env/bin/activate

python "average_thickness_maps.py" --dataset_root "/home/karlwenn/scratch/HCP_Aging_structural/fmriresults01" --parcellation "regional"