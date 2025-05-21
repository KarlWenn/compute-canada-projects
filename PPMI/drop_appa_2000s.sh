#!/bin/bash

#SBATCH --account=def-adagher
#SBATCH --time=11:59:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=8G

module load mrtrix

python drop_appa_2000s.py