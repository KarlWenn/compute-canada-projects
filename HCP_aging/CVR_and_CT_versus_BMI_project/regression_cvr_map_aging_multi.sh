#!/bin/bash
#SBATCH --account=def-adagher 
#SBATCH --time=95:00:00
#SBATCH --cpus-per-task=20
#SBATCH --mem-per-cpu=2G
#SBATCH --array=1-725

module load fsl 2> /dev/null
module load python 2> /dev/null
module load afni 2> /dev/null

source /home/karlwenn/projects/def-adagher/karlwenn/CVR_maps/CVR_env/bin/activate

SUBJECT_LIST="../data/subjects.txt"
echo "Number subjects found: `cat $SUBJECT_LIST | wc -l`"

SUBJECT_ID=`sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST`
echo "Subject ID: $SUBJECT_ID"

python "regression_cvr_map_aging_multi.py" --dataset_root "/home/karlwenn/scratch/HCP_aging/fmriresults01" --subject_number $SUBJECT_ID --track_processing "False"