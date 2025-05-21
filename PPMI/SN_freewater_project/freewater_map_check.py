import nibabel as nib
import numpy as np
import sys
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--image_path', type=str)

    args = parser.parse_args()

    image_path = args.image_path

    img_data = nib.load(image_path).get_fdata()

    if np.all(img_data == 1.0):
        sys.exit(1)
    else:
        sys.exit()

if __name__ == "__main__":
    main()