#!/bin/bash

#SBATCH --account=rrg-adagher
#SBATCH --time=11:59:00
#SBATCH --mem-per-cpu=8G
#SBATCH --cpus-per-task=4
#SBATCH --array=1-1000

module load mrtrix
module load ants
module load fsl
module load StdEnv/2023
module load freesurfer/7.4.1
source $EBROOTFREESURFER/FreeSurferEnv.sh
module load afni
module load minc-toolkit
module load apptainer

MICAPIPE_FUNCTIONS_PATH="/lustre03/project/6006490/karlwenn/micapipe/micapipe/functions"
MICAPIPE_IMAGE_PATH="/lustre03/project/6004787/public_data/apptainer_images/micapipe-v0.2.3.simg"

THREADS=$SLURM_JOB_CPUS_PER_NODE

SUBJECT_LIST=../data/abcd_subjects.txt

SUBJECT_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $1}')
echo "SUBJECT ID: $SUBJECT_ID"

SESSION_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $2}')
echo "SESSION ID: $SESSION_ID"

t1w=run-01_T1w

# Need to make temporary BIDS directory to work with micapipe and the fact that our data is tarred

TAR_FILE_DIR="/lustre03/project/6004787/public_data/ABCD_51/imaging/fmriresults01/abcd-mproc-release5"
TMP_DATA_DIR="/lustre04/scratch/karlwenn/ABCD_data"

bids=$TMP_DATA_DIR
output_dir=/lustre04/scratch/karlwenn/abcd_micapipe_outputs
tmp_dir=/lustre04/scratch/karlwenn/micapipe

tar --wildcards -xvzf "$TAR_FILE_DIR"/"$SUBJECT_ID"_"$SESSION_ID"_ABCD-MPROC-T1_*.tgz -C $TMP_DATA_DIR
tar --wildcards -xvzf "$TAR_FILE_DIR"/"$SUBJECT_ID"_"$SESSION_ID"_ABCD-MPROC-T2_*.tgz -C $TMP_DATA_DIR

TMP_ANAT_ROOT="$TMP_DATA_DIR"/sub-"$SUBJECT_ID"/ses-"$SESSION_ID"/anat

T1W_IMAGE=$(echo "$TMP_ANAT_ROOT"/*T1w.nii)

t1w_image_name=$(basename "$T1W_IMAGE")

MASK_DIR=$TMP_ANAT_ROOT/masks
BRAINS_DIR=$TMP_ANAT_ROOT/brains

# If mask directory or brain directory already exist, remove them so that we can put new images in
if [ -d "$MASK_DIR" ]; then
    rm -r "$MASK_DIR"
fi

if [ -d "$BRAINS_DIR" ]; then
    rm -r "$BRAINS_DIR"
fi

mkdir -p "$MASK_DIR"
mkdir -p "$BRAINS_DIR"

# Using deepbet to brain extract T1w which will later be used when calling 03_MPC.sh
deepbet-cli -i "$T1W_IMAGE" -o "$BRAINS_DIR"/"$t1w_image_name" -m "$MASK_DIR"/"$t1w_image_name" -t 0.4
# Just need brain
t1w_brain=$BRAINS_DIR/$t1w_image_name
SESSION_ID=ses-${SESSION_ID}

# Run structural processing, including surface processing and post structural processing
${MICAPIPE_FUNCTIONS_PATH}/01_proc-structural.sh $bids $SUBJECT_ID $output_dir $SESSION_ID FALSE $THREADS $tmp_dir $t1w # Looks good
apptainer exec $MICAPIPE_IMAGE_PATH ${MICAPIPE_FUNCTIONS_PATH}/01_proc-surf.sh $bids $SUBJECT_ID $output_dir $SESSION_ID FALSE $THREADS $tmp_dir FALSE FALSE /home/karlwenn/.licenses/freesurfer.lic DEFAULT # Looks good
${MICAPIPE_FUNCTIONS_PATH}/02_post-structural.sh $bids $SUBJECT_ID $output_dir $SESSION_ID FALSE $THREADS $tmp_dir aparc FALSE

# Define path to myelin map and path to image to register with
myelin_map=/lustre04/scratch/karlwenn/ABCD_data_output/sub-${SUBJECT_ID}/$SESSION_ID/T1wDividedByT2w_native.nii.gz

# Run Microstructural Profile Covariance (MPC) processing
${MICAPIPE_FUNCTIONS_PATH}/03_MPC.sh $bids $SUBJECT_ID $output_dir $SESSION_ID FALSE $THREADS $tmp_dir $myelin_map $t1w_brain myelin

# Now have to squash results immediately or scratch will fill up
# Remove original files if the command runs correctly
if mksquashfs $output_dir/sub-${SUBJECT_ID}/${SESSION_ID} $output_dir/sub-${SUBJECT_ID}/${SESSION_ID}.sqsh; then
    rm -r $output_dir/sub-${SUBJECT_ID}/${SESSION_ID}
fi

if mksquashfs $output_dir/fastsurfer/sub-${SUBJECT_ID}_${SESSION_ID} $output_dir/fastsurfer/sub-${SUBJECT_ID}_${SESSION_ID}.sqsh; then
    rm -r $output_dir/fastsurfer/sub-${SUBJECT_ID}_${SESSION_ID}
fi

rm -r "$TMP_DATA_DIR"/sub-"$SUBJECT_ID"/"$SESSION_ID"