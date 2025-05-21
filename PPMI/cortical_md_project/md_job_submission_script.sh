#!/bin/bash

#SBATCH --account=def-adagher
#SBATCH --time=2:59:00
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=16G
#SBATCH --array=1-737%49

# Loading packages, namely, freesurfer
module load StdEnv/2023 
module load freesurfer/7.4.1 

source $EBROOTFREESURFER/FreeSurferEnv.sh

# To avoid conflicts when writing to the csv (don't want two subjects writing to csv at exact same time)
# Sort of an abundance of caution, IDK if this would actually cause issues not having this, but better safe than sorry
# It does cause issues, actually, will rectify by manually adding subjects that got caught in the crossfire back later
sleep $(($SLURM_ARRAY_TASK_ID % 50 * 20))

# Define relevant directories
MICAPIPE_OUTPUT_DIR=/home/karlwenn/scratch/ppmi_micapipe_outputs
TMP_DIR=/home/karlwenn/scratch/cortical_diffusivity_tmp_files
fs_root="/home/karlwenn/projects/rrg-adagher/public_data/PPMI_NEW/derivatives/freesurfer/7.3.2/output"

SUBJECT_LIST=../data/micapipe_def_subjects.txt

SUBJECT_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $1}')
echo "SUBJECT ID: $SUBJECT_ID"

SESSION_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $2}')
echo "SESSION ID: $SESSION_ID"

# Check if freesurfer results for this particular subject session are tarred or not
# Simply check if a tar file exists or not for this subject session to do so
if [ -f "$fs_root/$SESSION_ID/${SUBJECT_ID}.tar" ]; then
    # If tar file exists for a subject, we'll untar it to a temporary directory, and set this temporary directory
    # As SUBJECTS_DIR for freesurfer to recognize
    if [ "$SESSION_ID" == "ses-BL" ]; then
        export SUBJECTS_DIR="$TMP_DIR/freesurfer/ses-BL"
        tar -xvf "$fs_root/$SESSION_ID/${SUBJECT_ID}.tar" -C $TMP_DIR/freesurfer/ses-BL
    elif [ "$SESSION_ID" == "ses-V04" ]; then
        export SUBJECTS_DIR="$TMP_DIR/freesurfer/ses-V04"
        tar -xvf "$fs_root/$SESSION_ID/${SUBJECT_ID}.tar" -C $TMP_DIR/freesurfer/ses-V04
    elif [ "$SESSION_ID" == "ses-V06" ]; then
        export SUBJECTS_DIR="$TMP_DIR/freesurfer/ses-V06"
        tar -xvf "$fs_root/$SESSION_ID/${SUBJECT_ID}.tar" -C $TMP_DIR/freesurfer/ses-V06
    elif [ "$SESSION_ID" == "ses-V08" ]; then
        export SUBJECTS_DIR="$TMP_DIR/freesurfer/ses-V08"
        tar -xvf "$fs_root/$SESSION_ID/${SUBJECT_ID}.tar" -C $TMP_DIR/freesurfer/ses-V08
    elif [ "$SESSION_ID" == "ses-V10" ]; then
        export SUBJECTS_DIR="$TMP_DIR/freesurfer/ses-V10"
        tar -xvf "$fs_root/$SESSION_ID/${SUBJECT_ID}.tar" -C $TMP_DIR/freesurfer/ses-V10
    fi
else # If FS data is not tarred, will define SUBJECTS_DIR based on session
    if [ "$SESSION_ID" == "ses-BL" ]; then
        export SUBJECTS_DIR="$fs_root/ses-BL"
    elif [ "$SESSION_ID" == "ses-V04" ]; then
        export SUBJECTS_DIR="$fs_root/ses-V04"
    elif [ "$SESSION_ID" == "ses-V06" ]; then
        export SUBJECTS_DIR="$fs_root/ses-V06"
    elif [ "$SESSION_ID" == "ses-V08" ]; then
        export SUBJECTS_DIR="$fs_root/ses-V08"
    elif [ "$SESSION_ID" == "ses-V10" ]; then
        export SUBJECTS_DIR="$fs_root/ses-V10"
    fi
fi

# What do we want to do now?
# 1. Run bbregister
# 2. Run vol2surf
# 3. Run parcellation

md_image=$MICAPIPE_OUTPUT_DIR/$SUBJECT_ID/$SESSION_ID/dwi/${SUBJECT_ID}_${SESSION_ID}_space-dwi_model-DTI_map-ADC.nii.gz

if [ ! -f $md_image ]; then
    echo "MD IMAGE: $md_image, doesn't exist!"
    exit 1
fi

# Run bbregister

bbregister_output_reg=$TMP_DIR/registration_files/${SUBJECT_ID}_${SESSION_ID}_register.dat

bbregister --s $SUBJECT_ID --mov $md_image --reg $bbregister_output_reg --dti

# Run vol2surf

vol2surf_lh_output=$TMP_DIR/vol2surf_output/${SUBJECT_ID}_${SESSION_ID}_md-lh.mgh
vol2surf_rh_output=$TMP_DIR/vol2surf_output/${SUBJECT_ID}_${SESSION_ID}_md-rh.mgh

# For left hemisphere
mri_vol2surf --src $md_image --out $vol2surf_lh_output --reg $bbregister_output_reg --projfrac-avg 0.1 0.9 0.2 --hemi 'lh' 

# For right hemisphere
mri_vol2surf --src $md_image --out $vol2surf_rh_output --reg $bbregister_output_reg --projfrac-avg 0.1 0.9 0.2 --hemi 'rh'

# Run parcellation
python dk_parcellation.py --lh_md_surf_map $vol2surf_lh_output \
                          --rh_md_surf_map $vol2surf_rh_output \
                          --lh_annot $SUBJECTS_DIR/$SUBJECT_ID/label/lh.aparc.DKTatlas.annot \
                          --rh_annot $SUBJECTS_DIR/$SUBJECT_ID/label/rh.aparc.DKTatlas.annot \
                          --subject_id $SUBJECT_ID \
                          --session_id $SESSION_ID 

# Remove intermediate files, since results are already stored in CSV
rm $bbregister_output_reg
rm $vol2surf_lh_output
rm $vol2surf_rh_output

# And clean up untarred freesurfer temporary directory, if it exists
if [ -f "$fs_root/$SESSION_ID/${SUBJECT_ID}.tar" ]; then
    if [ "$SESSION_ID" == "ses-BL" ]; then
        rm -r $TMP_DIR/freesurfer/ses-BL/$SUBJECT_ID
    elif [ "$SESSION_ID" == "ses-V04" ]; then
        rm -r $TMP_DIR/freesurfer/ses-V04/$SUBJECT_ID/
    elif [ "$SESSION_ID" == "ses-V06" ]; then
        rm -r $TMP_DIR/freesurfer/ses-V06/$SUBJECT_ID/
    elif [ "$SESSION_ID" == "ses-V08" ]; then
        rm -r $TMP_DIR/freesurfer/ses-V08/$SUBJECT_ID/
    elif [ "$SESSION_ID" == "ses-V10" ]; then
        rm -r $TMP_DIR/freesurfer/ses-V10/$SUBJECT_ID/
    fi
fi