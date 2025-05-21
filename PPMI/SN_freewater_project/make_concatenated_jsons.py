import shutil

INPUT_DIR = "/home/karlwenn/projects/rrg-adagher/public_data/PPMI_NEW/bids"
OUTPUT_DIR = "/home/karlwenn/scratch/concatenated_PPMI_appa_data"
SUBJECT_LIST = "../data/appa1_subs.txt"

def main():
    with open(SUBJECT_LIST) as f:
        for subject in f:
            subject, session = subject.rstrip().split()
            copy_json(subject, session)
    return

def copy_json(subject, session):
    json_in = f"{INPUT_DIR}/{subject}/{session}/dwi/{subject}_{session}_acq-B1000_dir-PA_run-01_dwi.json"
    json_out = f"{OUTPUT_DIR}/{subject}/{session}/dwi/{subject}_{session}_acq-concatenated_dir-PA_run-01_dwi.json"
    
    shutil.copyfile(json_in, json_out)
    
    return

if __name__ == "__main__":
    main()