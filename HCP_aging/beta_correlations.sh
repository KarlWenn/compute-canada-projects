#!/bin/bash
#SBATCH --account=def-adagher 
#SBATCH --time=1:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16G

source /home/karlwenn/projects/def-adagher/karlwenn/CVR_maps/CVR_env/bin/activate

python "beta_correlations.py" --parcellation "regional"