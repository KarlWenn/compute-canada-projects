#!/bin/bash

#SBATCH --account=def-adagher
#SBATCH --time=11:59:00
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=4G
#SBATCH --array=1-883

module load mrtrix
module load ants
module load fsl
module load StdEnv/2023
module load freesurfer/7.4.1
source $EBROOTFREESURFER/FreeSurferEnv.sh
module load afni

MICAPIPE_FUNCTIONS_PATH="/lustre03/project/6006490/karlwenn/micapipe/micapipe/functions"

THREADS=$SLURM_JOB_CPUS_PER_NODE

SUBJECT_LIST=../data/sd1_subs.txt

SUBJECT_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $1}')
echo "SUBJECT ID: $SUBJECT_ID"

SESSION_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $2}')
echo "SESSION ID: $SESSION_ID"

t1w=run-01_T1w

bids=/home/karlwenn/projects/rrg-adagher/public_data/PPMI_NEW/bids
output_dir=/home/karlwenn/scratch/ppmi_micapipe_outputs_v2
tmp_dir=/home/karlwenn/scratch/micapipe

dwi_main=("$bids"/"${SUBJECT_ID}"/"${SESSION_ID}"/dwi/"${SUBJECT_ID}"_"${SESSION_ID}"*_run-01_dwi.nii.gz)

${MICAPIPE_FUNCTIONS_PATH}/01_proc-structural.sh $bids $SUBJECT_ID $output_dir $SESSION_ID TRUE $THREADS /home/karlwenn/scratch/micapipe $t1w
${MICAPIPE_FUNCTIONS_PATH}/02_proc-dwi.sh $bids $SUBJECT_ID $output_dir $SESSION_ID TRUE $THREADS $tmp_dir $dwi_main FALSE