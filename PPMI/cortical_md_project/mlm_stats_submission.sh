#!/bin/bash

#SBATCH --account=def-adagher
#SBATCH --time=11:59:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=1G

python mlm_stats.py