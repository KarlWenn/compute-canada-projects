#!/bin/bash

#SBATCH --account=rrg-adagher
#SBATCH --time=2:59:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4G

module load python

python dwi_demographics.py