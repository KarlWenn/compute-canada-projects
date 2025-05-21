#!/bin/bash

#SBATCH --account=def-adagher
#SBATCH --time=2:59:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16G
#SBATCH --array=1-883

module load mrtrix

SUBJECT_LIST=../data/sd1_subs.txt

MICAPIPE_OUTPUT_DIR=/home/karlwenn/scratch/ppmi_micapipe_outputs_v2

SUBJECT_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $1}')
echo "SUBJECT ID: $SUBJECT_ID"

SESSION_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $2}')
echo "SESSION ID: $SESSION_ID"

OUTPUT_DIR="/home/karlwenn/scratch/PPMI_micapipe_freewater_results_v2/$SUBJECT_ID/$SESSION_ID"

mkdir -p $OUTPUT_DIR

tmp_dir=/home/karlwenn/scratch/micapipe_freewater_tmp/$SUBJECT_ID/$SESSION_ID
mkdir -p $tmp_dir

preproc_dwi_mif=$MICAPIPE_OUTPUT_DIR/$SUBJECT_ID/$SESSION_ID/dwi/${SUBJECT_ID}_${SESSION_ID}_space-dwi_desc-preproc_dwi.mif

output_dwi_nifti=$tmp_dir/dwi.nii.gz
output_dwi_bval=$tmp_dir/dwi.bval
output_dwi_bvec=$tmp_dir/dwi.bvec
brain_mask=$MICAPIPE_OUTPUT_DIR/$SUBJECT_ID/$SESSION_ID/dwi/${SUBJECT_ID}_${SESSION_ID}_space-dwi_desc-brain_mask.nii.gz

mrconvert $preproc_dwi_mif $output_dwi_nifti -force --export_grad_fsl $output_dwi_bvec $output_dwi_bval

module load matlab

cd /home/karlwenn/projects/rrg-adagher/freewater/Free-Water

matlab -nodisplay -r "FreeWater_OneCase('$SUBJECT_ID', '$output_dwi_nifti', '$output_dwi_bval', '$output_dwi_bvec', '$brain_mask', '$OUTPUT_DIR')"