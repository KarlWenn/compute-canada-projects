#!/bin/bash
#SBATCH --account=rrg-adagher 
#SBATCH --time=1:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16G

source /home/karlwenn/projects/def-adagher/karlwenn/CVR_maps/CVR_env/bin/activate

python "homa_ir_scatterplots.py" --dataset_root "/home/karlwenn/scratch/HCP_aging/fmriresults01"