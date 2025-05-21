import os

DATA_DIR = "/home/karlwenn/scratch/ppmi_micapipe_outputs"

def main():

    subjects = os.listdir(DATA_DIR)

    # For every session, we want the subjects that have underwent scanning for this session (i.e. the ones we have data for)
    # Make a dictionary to store these
    session_subjects = {}

    # To get the subjects in every session we need to isolate the session by iterating through them
    for subject in subjects:
        # Skip files names that aren't subjects
        if 'sub-' not in subject:
            continue
        sessions = os.listdir(f"{DATA_DIR}/{subject}")

        for session in sessions:
            # Now append cleaned subject name to list of subjects for this session
            # Make a list if this dictionary entry doesn't exist yet
            if subject not in session_subjects:
                session_subjects[subject] = [session]
            else:
                session_subjects[subject].append(session)
    
    # Now we'll have a dictoinary mapping session to lists of cleaned
    # Now we want to write these to a file

    with open("../data/ppmi_md_sessions.txt", 'w') as f:
        for subject in session_subjects:
            for session in session_subjects[subject]:
                f.write(f"{subject} {session}\n")

if __name__ == "__main__":
    main()