#!/bin/bash

#SBATCH --account=def-adagher
#SBATCH --time=2:59:00
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=4G
#SBATCH --array=1-530

module load StdEnv/2023 gcc/12.3
module load ants/2.5.0
module load fsl

export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=$SLURM_JOB_CPUS_PER_NODE

SUBJECT_LIST=../data/lrrl1_subs.txt

SUBJECT_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $1}')
echo "SUBJECT ID: $SUBJECT_ID"

SESSION_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $2}')
echo "SESSION ID: $SESSION_ID"

FREEWATER_DIR=/home/karlwenn/scratch/PPMI_micapipe_freewater_results_v2
MICAPIPE_OUTPUT_DIR=/home/karlwenn/scratch/ppmi_micapipe_outputs_v2
RESULTS_DIR=/home/karlwenn/scratch/ppmi_micapipe_registered_freewater_fonov
template_mask=../data/atlases/SN_ROI_symmetric_three_subdivisions.nii.gz

# Registrations:
# 1. Subject B0 to Subject T1w (rigid, linear)
# 2. Non-linear warp subject t1w to template t1w
# 3. Inverse warp of 2 applied to mask in template space 
# 4. Inverse warp of 1 applied to mask in template space
# In total:
# Two antsRegistrationSyN calls (1 and 2)
# Two antsApplyTransforms calls (3 and 4)

freewater_map_b0_space=$FREEWATER_DIR/$SUBJECT_ID/$SESSION_ID/${SUBJECT_ID}_FW.nii.gz
t1w_nativepro_image=$MICAPIPE_OUTPUT_DIR/$SUBJECT_ID/$SESSION_ID/anat/${SUBJECT_ID}_${SESSION_ID}_space-nativepro_T1w.nii.gz
template_img=/home/karlwenn/projects/def-adagher/karlwenn/PPMI/data/atlases/average_nonlin_10_brain.nii.gz
subject_b0=$MICAPIPE_OUTPUT_DIR/$SUBJECT_ID/$SESSION_ID/dwi/${SUBJECT_ID}_${SESSION_ID}_space-dwi_desc-b0.nii.gz

mkdir -p "$RESULTS_DIR"/"$SUBJECT_ID"/"$SESSION_ID"
deepbet_t1w="$RESULTS_DIR"/"$SUBJECT_ID"/"$SESSION_ID"/${SUBJECT_ID}_${SESSION_ID}_t1w-deepbet.nii.gz
deepbet_t1w_mask="$RESULTS_DIR"/"$SUBJECT_ID"/"$SESSION_ID"/${SUBJECT_ID}_${SESSION_ID}_t1w-deepbet_mask.nii.gz
deepbet-cli -i "$t1w_nativepro_image" -o $deepbet_t1w -m $deepbet_t1w_mask

b0_to_t1w_output=$RESULTS_DIR/$SUBJECT_ID/$SESSION_ID/${SUBJECT_ID}_${SESSION_ID}_b0-to-nativepro_

# Rigidly register subject B0 to the deepbetted T1w
antsRegistrationSyN.sh -d 3 \
    -m ${subject_b0} \
    -f ${deepbet_t1w} \
    -t 'r' \
    -o $b0_to_t1w_output

# Have to check if Freewater image is all 1.0s to account for random failures
# Wasn't that hard to do :P
python freewater_map_check.py -i $freewater_map_b0_space

failed_freewater=$?

if [ $failed_freewater -eq 1 ]; then
    echo "$SUBJECT_ID $SESSION_ID" >> ../data/failed_freewater_subs.txt
    exit 1
fi

mkdir -p ${RESULTS_DIR}/$SUBJECT_ID/$SESSION_ID

t1w_to_template_output=${RESULTS_DIR}/${SUBJECT_ID}/${SESSION_ID}/${SUBJECT_ID}_${SESSION_ID}_nativepro-to-biondetti_

# Register T1w in nativepro space to mask template image.
echo "Registering T1w in nativepro to mask template image"
antsRegistrationSyN.sh -d 3 \
    -m ${deepbet_t1w} \
    -f ${template_img} \
    -o $t1w_to_template_output

nativepro_mask=${RESULTS_DIR}/${SUBJECT_ID}/${SESSION_ID}/${SUBJECT_ID}_${SESSION_ID}_mask_space-nativepro.nii.gz

# Apply inverse of nativepro->template transform to mask, generating mask in nativepro space
antsApplyTransforms -d 3 \
    -i $template_mask \
    -r $deepbet_t1w \
    -t [ ${t1w_to_template_output}0GenericAffine.mat, 1 ] \
    -t ${t1w_to_template_output}1InverseWarp.nii.gz \
    -n GenericLabel \
    -o $nativepro_mask

b0_mask=${RESULTS_DIR}/${SUBJECT_ID}/${SESSION_ID}/${SUBJECT_ID}_${SESSION_ID}_mask_space-b0.nii.gz

# Apply inverse of b0->nativepro transform to mask, generating mask in b0 (i.e. freewater) space
antsApplyTransforms -d 3 \
    -i $nativepro_mask \
    -r $subject_b0 \
    -t [ ${b0_to_t1w_output}0GenericAffine.mat, 1 ] \
    -n GenericLabel \
    -o $b0_mask