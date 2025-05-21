#!/bin/bash

#SBATCH --time=11:59:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=8G
#SBATCH --account=def-adagher

python concatenate_appa_dwis.py