#!/bin/bash
#SBATCH --account=rrg-adagher 
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16G

source /home/karlwenn/projects/def-adagher/karlwenn/CVR_maps/CVR_env/bin/activate

python "image_resampling.py" --cbf_dataset_root  "/home/karlwenn/projects/rrg-adagher/public_data/HCP_aging_perfusion"