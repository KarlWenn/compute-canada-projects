#!/bin/bash

#SBATCH --account=def-adagher
#SBATCH --time=2:59:00
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=2G
#SBATCH --array=1-253

module load StdEnv/2023 gcc/12.3 2> /dev/null
module load ants/2.5.0 2> /dev/null
module load fsl 2> /dev/null

# Set number of threads for antsRegistratyionSyN call
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=$SLURM_JOB_CPUS_PER_NODE

# Defining directories to make use of over the course of the script
TAR_FILE_DIR="/home/karlwenn/projects/rrg-adagher/public_data/ABCD_51/imaging/fmriresults01/abcd-mproc-release5"
TMP_DATA_DIR="/home/karlwenn/scratch/ABCD_data"
OUTPUT_DIR="/home/karlwenn/scratch/ABCD_data_output"

# Defining paths to template images
REF_MASK="/home/karlwenn/projects/def-adagher/karlwenn/ABCD/data/templates/nihpd_asym_07.5-13.5_mask.nii"
REF_BRAIN="/home/karlwenn/projects/def-adagher/karlwenn/ABCD/data/templates/nihpd_asym_07.5-13.5_t1w_brain.nii.gz"

# Defining subject ID and session ID from subject list
SUBJECT_LIST="../data/abcd_subjects.txt"

SUBJECT_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $1}')
echo "SUBJECT ID: $SUBJECT_ID"

SESSION_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" $SUBJECT_LIST | awk '{print $2}')
echo "SESSION ID: $SESSION_ID"

# Untarring subject T1w and T2w into temporary (working?) data directory
tar --wildcards -xvzf "$TAR_FILE_DIR"/"$SUBJECT_ID"_"$SESSION_ID"_ABCD-MPROC-T1_*.tgz -C $TMP_DATA_DIR
tar --wildcards -xvzf "$TAR_FILE_DIR"/"$SUBJECT_ID"_"$SESSION_ID"_ABCD-MPROC-T2_*.tgz -C $TMP_DATA_DIR

# Grabbing subject T1w's and T2w's from untarred directory
# This could probably just be hard coded, but this works
TMP_ANAT_ROOT="$TMP_DATA_DIR"/sub-"$SUBJECT_ID"/ses-"$SESSION_ID"/anat

T1W_IMAGE=$(echo "$TMP_ANAT_ROOT"/*T1w.nii)
T2W_IMAGE=$(echo "$TMP_ANAT_ROOT"/*T2w.nii)

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

# Only run deepbet on the T1w, since we will use the mask generated from this brain extraction to skull strip the T2w
# Do this since deepbet was only trained on T1w images, and T1w and T2w image are in the same space
deepbet-cli -i "$T1W_IMAGE" -o "$BRAINS_DIR"/"$t1w_image_name" -m "$MASK_DIR"/"$t1w_image_name" -t 0.4

# Don't actually need the brain, just make use of the mask
t1w_mask=$MASK_DIR/$t1w_image_name

# Now we have our subject T1w, T2w, and the template
# Run N4 Bias Field Correction, using the masks produced by deepbet
# First define output locations, as well as the path to the mask previously generated from deepbet
t1w_n4_bc=$TMP_ANAT_ROOT/sub-${SUBJECT_ID}_ses-${SESSION_ID}_T1w_N4_bc.nii.gz
t2w_n4_bc=$TMP_ANAT_ROOT/sub-${SUBJECT_ID}_ses-${SESSION_ID}_T2w_N4_bc.nii.gz

N4BiasFieldCorrection -i "$T1W_IMAGE" -x "$t1w_mask" -d 3 -v 1 -s 3 -b [180] -c [50x50x50x50, 1e-7] -o [$t1w_n4_bc]
N4BiasFieldCorrection -i "$T2W_IMAGE" -x "$t1w_mask" -d 3 -v 1 -s 3 -b [180] -c [50x50x50x50, 1e-7] -o [$t2w_n4_bc]

# Now we have our bias-corrected images, can register them to standard space
t1w_n4_bc_brain=$TMP_ANAT_ROOT/t1w_n4_bc_brain.nii.gz
t2w_n4_bc_brain=$TMP_ANAT_ROOT/t2w_n4_bc_brain.nii.gz

fslmaths "$t1w_n4_bc" -mas "$t1w_mask" "$t1w_n4_bc_brain"
fslmaths "$t2w_n4_bc" -mas "$t1w_mask" "$t2w_n4_bc_brain"

sub_output_dir=${OUTPUT_DIR}/sub-${SUBJECT_ID}/ses-${SESSION_ID}

# Create output directory and output names
mkdir -p "${sub_output_dir}"

t1w_to_template_output=${sub_output_dir}/sub-${SUBJECT_ID}_ses-${SESSION_ID}_registered_T1w_
registered_bc_t2w=${sub_output_dir}/sub-${SUBJECT_ID}_ses-${SESSION_ID}_registered_T2w.nii.gz

# First compute transformation for T1w to standard space
echo "Running T1w to template registration"
antsRegistrationSyN.sh -d 3 \
    -m "${t1w_n4_bc_brain}" \
    -f ${REF_BRAIN} \
    -t 'b' \
    -o "${t1w_to_template_output}"

echo "Applying transforms to T2w image"
antsApplyTransforms -d 3 -i ${t2w_n4_bc} -r ${REF_BRAIN} --verbose \
    -n BSpline \
    -t "${t1w_to_template_output}1Warp.nii.gz" \
	-t "${t1w_to_template_output}0GenericAffine.mat" \
    -o "${registered_bc_t2w}"

registered_bc_t1w=${t1w_to_template_output}Warped.nii.gz

fslmaths "${registered_bc_t1w}" -abs "${registered_bc_t1w}" -odt float

fslmaths "${registered_bc_t2w}" -abs "${registered_bc_t2w}" -odt float

# Mask images using brain mask output by fMRIprep
fslmaths "${registered_bc_t1w}" -mas ${REF_MASK} "${registered_bc_t1w}"

fslmaths "${registered_bc_t2w}" -mas ${REF_MASK} "${registered_bc_t2w}"

# Create myelin maps
wb_command -volume-math "clamp(T1w/T2w,0,100)" "${sub_output_dir}/T1wDividedByT2w.nii.gz" -var T1w "${registered_bc_t1w}" -var T2w "${registered_bc_t2w}"

wb_command -volume-palette "${sub_output_dir}/T1wDividedByT2w.nii.gz" MODE_AUTO_SCALE_PERCENTAGE -pos-percent 4 96 -interpolate true -palette-name videen_style -disp-pos true -disp-neg false -disp-zero false

fslmaths "${sub_output_dir}/T1wDividedByT2w.nii.gz" -nan "${sub_output_dir}/T1wDividedByT2w.nii.gz"

fslmaths "${sub_output_dir}/T1wDividedByT2w.nii.gz" -uthr 5 "${sub_output_dir}/T1wDividedByT2w.nii.gz"

rm -r "$TMP_ANAT_ROOT"