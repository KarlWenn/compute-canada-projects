#!/bin/bash
#SBATCH --account=def-adagher 
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=32G

source /home/karlwenn/projects/def-adagher/karlwenn/CVR_maps/CVR_env/bin/activate

python "cbf_scatterplots.py" --dataset_root "/home/karlwenn/scratch/HCP_aging/fmriresults01" --cbf_dataset_root "../data/HCP_aging_perfusion"