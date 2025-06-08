#!/bin/bash
#SBATCH --account=def-adagher 
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=24G

source /home/karlwenn/projects/def-adagher/karlwenn/CVR_maps/CVR_env/bin/activate

python "HOMA_IR_correlation.py" --dataset_root "/home/karlwenn/scratch/HCP_aging/fmriresults01" --parcellation "regional"