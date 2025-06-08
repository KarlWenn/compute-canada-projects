#!/bin/bash
#SBATCH --account=rrg-adagher 
#SBATCH --time=6:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=32G

source /home/karlwenn/projects/def-adagher/karlwenn/CVR_maps/CVR_env/bin/activate

python "atrophy_maps_vertexwise.py" --dataset_root "/home/karlwenn/scratch/HCP_Aging_structural/fmriresults01"