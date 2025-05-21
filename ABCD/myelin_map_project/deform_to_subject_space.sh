#!/bin/bash
# Script to transform myelin maps in template space to subject space.
# Since micapipe wants to work with maps in subject space.

myelin_map_directory=/home/karlwenn/scratch/ABCD_data_output

for subject_path in $myelin_map_directory/*; do
    subject=$(basename $subject_path)
    echo $subject_path
    for session_path in $subject_path/*; do
        session=$(basename $session_path)
        myelin_map=$session_path/T1wDividedByT2w.nii.gz
        original_space_t1w=$session_path/${subject}_${session}_registered_T1w_InverseWarped.nii.gz
        inverse_warp=$session_path/${subject}_${session}_registered_T1w_1InverseWarp.nii.gz
        affine_xfm=$session_path/${subject}_${session}_registered_T1w_0GenericAffine.mat
        output=$session_path/T1wDividedByT2w_native.nii.gz
        antsApplyTransforms \
        -d 3 \
        -i $myelin_map \
        -r $original_space_t1w \
        -t [ $affine_xfm, 1 ] \
        -t $inverse_warp \
        -o $output
    done
done