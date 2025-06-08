#!/bin/bash

#SBATCH --account=rrg-adagher
#SBATCH --time=11:59:00
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=4G
#SBATCH --array=1-200
#SBATCH --output=/home/karlwenn/scratch/PPMI_slurm_output_files/slurm-%A-%a.out

module load mrtrix
module load ants
module load fsl
module load StdEnv/2023
module load freesurfer/7.4.1
source $EBROOTFREESURFER/FreeSurferEnv.sh
module load afni

MICAPIPE_FUNCTIONS_PATH="/lustre03/project/6006490/karlwenn/micapipe/micapipe/functions"

THREADS=$SLURM_JOB_CPUS_PER_NODE

SUBJECT_LIST=../data/appa1_subs.txt

SUBJECT_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $1}')
echo "SUBJECT ID: $SUBJECT_ID"

SESSION_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $2}')
echo "SESSION ID: $SESSION_ID"

t1w=run-01_T1w

bids=/home/karlwenn/projects/rrg-adagher/public_data/PPMI_NEW/bids
concatenated_pa_dir=/home/karlwenn/scratch/concatenated_PPMI_appa_data
output_dir=/home/karlwenn/scratch/ppmi_micapipe_outputs_v2
tmp_dir=/home/karlwenn/scratch/micapipe

dwi_directory=$bids/$SUBJECT_ID/$SESSION_ID/dwi

for file in $(find $dwi_directory -name '*_acq-B1000_dir-PA_run-01_dwi.nii.gz');
do
    dwi_main=$file
done

for file in $(find $dwi_directory -name '*_acq-B0_dir-AP_run-01_dwi.nii.gz');
do
    dwi_rpe=$file
done

${MICAPIPE_FUNCTIONS_PATH}/01_proc-structural.sh $bids $SUBJECT_ID $output_dir $SESSION_ID FALSE $THREADS $tmp_dir $t1w
${MICAPIPE_FUNCTIONS_PATH}/02_proc-dwi.sh $bids $SUBJECT_ID $output_dir $SESSION_ID FALSE $THREADS $tmp_dir $dwi_main $dwi_rpe FALSE FALSE
