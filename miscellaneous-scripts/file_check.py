import numpy as np
import glob
import datetime
import argparse
import math
import sys
import os
import pandas as pd


def cross_check_with_csv(csv_path, imaging_path, behaviour_path, animals):

    for animal_name in animals:
        csv_data = pd.read_csv(
            csv_path + "/" + animal_name + ".csv",
            dtype={
                'upi': np.int64,
                'date': str,
                'experiment_number': str,
                'missing_imaging_trials': str,
                'skip_imaging_trials': str,
                'missing_behaviour_trials': str,
                'skip_behaviour_trials': str,
            },
        )
        print("--------------------------------------------------")
        print(animal_name)
        print("--------------------------------------------------")

        img_sess_paths = glob.glob(imaging_path + "/" + animal_name + "/20*/[0-9]")
        img_dates = [x.split("/")[-2] for x in img_sess_paths]

        bhvr_sess_paths = glob.glob(
            behaviour_path + "/" + animal_name + "/" + animal_name + "*"
        )
        bhvr_sess_names = [x.split("/")[-1] for x in bhvr_sess_paths]

        for index, session in csv_data.iterrows():

            print("**************************************************")
            print(
                f"{session['date']}/{session['experiment_number']}\t\
                {session['behaviour_code']}_{session['behaviour_session_number']}"
            )
            print("**************************************************")

            if session["num_imaging_trials"] > 0:
                if session["date"] in img_dates:
                    img_expt_nums = [
                        x.split("/")[-1]
                        for x in glob.glob(
                            imaging_path
                            + "/"
                            + animal_name
                            + "/"
                            + session["date"]
                            + "/[0-9]"
                        )
                    ]
                    if session["experiment_number"] in img_expt_nums:
                        trial_files = sorted(
                            glob.glob(
                                imaging_path
                                + "/"
                                + animal_name
                                + "/"
                                + session["date"]
                                + "/"
                                + session["experiment_number"]
                                + "/*.tif*"
                            )
                        )
                        if len(trial_files) != session["num_imaging_trials"]:
                            print("ERROR: Mismatch in number of imaging tiff files")
                        else:
                            csv_error_trials = set()
                            if pd.notna(session['skip_imaging_trials']):
                                csv_error_trials.update([int(x) for x in session['skip_imaging_trials'].split(';')])
                            if pd.notna(session['missing_imaging_trials']):
                                csv_error_trials.update(int(x) for x in session['missing_imaging_trials'].split(';'))

                            file_sizes = []
                            for trial_file in trial_files:
                                file_sizes.append(os.stat(trial_file).st_size)
                            file_sizes = np.array(file_sizes)
                            max_file_size = np.max(file_sizes)

                            if session['behaviour_code'] == 'Hr7':
                                small_file_size = np.percentile(file_sizes, 40)
                                error_t = np.where(np.logical_and(
                                    ((max_file_size - file_sizes) / max_file_size) > 0.01,
                                    np.abs((small_file_size - file_sizes) / small_file_size) > 0.01
                                ))[0]
                            else:
                                error_t = np.where(
                                    ((max_file_size - file_sizes) / max_file_size) > 0.01
                                )[0]
                            for et in error_t:
                                et_t_num = int(trial_files[et].split('-')[-3])
                                if et_t_num not in csv_error_trials:
                                    print(
                                        'ERROR: '
                                        + trial_files[et].split('/')[-1]
                                        + ' file size not close to max file size'
                                    )

                    else:
                        print("ERROR: Imaging session not found")
                        continue
                else:
                    print("ERROR: Imaging session not found")
                    continue

            bhvr_sess_name = f"{animal_name}_{session['behaviour_code']}_{session['behaviour_session_number']}"

            if session["num_behaviour_trials"] > 0:
                if bhvr_sess_name in bhvr_sess_names:
                    trial_files = sorted(
                        glob.glob(
                            behaviour_path
                            + "/"
                            + animal_name
                            + "/"
                            + bhvr_sess_name
                            + "/"
                            + "/*.tif*"
                        )
                    )
                    if len(trial_files) != session["num_behaviour_trials"]:
                        print("ERROR: Mismatch in number of behaviour tiff files")
                    else:
                        csv_error_trials = set()
                        if pd.notna(session['skip_behaviour_trials']):
                            csv_error_trials.update([int(x) for x in session['skip_behaviour_trials'].split(';')])
                        if pd.notna(session['missing_behaviour_trials']):
                            csv_error_trials.update(int(x) for x in session['missing_behaviour_trials'].split(';'))

                        file_sizes = []
                        for trial_file in trial_files:
                            file_sizes.append(os.stat(trial_file).st_size)
                        file_sizes = np.array(file_sizes)
                        max_file_size = np.max(file_sizes)

                        if session['behaviour_code'] == 'Hr7':
                            small_file_size = np.percentile(file_sizes, 40)
                            error_t = np.where(np.logical_and(
                                ((max_file_size - file_sizes) / max_file_size) > 0.01,
                                np.abs((small_file_size - file_sizes) / small_file_size) > 0.01
                            ))[0]
                        else:
                            error_t = np.where(
                                ((max_file_size - file_sizes) / max_file_size) > 0.01
                            )[0]
                        for et in error_t:
                            et_t_num = int(trial_files[et].split('/')[-1].split('.')[-2])
                            if et_t_num not in csv_error_trials:
                                print(
                                    'ERROR: '
                                    + trial_files[et].split('/')[-1]
                                    + ' file size not close to max file size'
                                )
                else:
                    print(
                        f"ERROR: Behaviour session {bhvr_sess_name} not found"
                    )
                    continue
            print()
        print()
        print()


def main(**kwargs):
    imaging_path = kwargs["imaging_path"]
    behaviour_path = kwargs["behaviour_path"]
    csv_path = kwargs["csv_path"]
    output_path = kwargs["output_path"]
    animals = kwargs["animals"].split(",")
    if output_path != "":
        if not (os.path.isdir(output_path)):
            os.mkdir(output_path)
    else:
        output_path = "."
    sys.stdout = open(output_path + "/file_check_output.txt", "w")

    # csv_with_imaging(csv_path, imaging_path, animals)
    # csv_with_behaviour(csv_path, behaviour_path, animals)
    cross_check_with_csv(csv_path, imaging_path, behaviour_path, animals)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check raw data files")
    parser.add_argument(
        "-i",
        "--imaging_path",
        required=True,
        help="Path to where the imaging data of all \
            animals is stored",
    )
    parser.add_argument(
        "-b",
        "--behaviour_path",
        required=True,
        help="Path to where the behaviour data of all \
            animals is stored",
    )
    parser.add_argument(
        "-c",
        "--csv_path",
        required=True,
        help="Path to where the csv files of all \
            animals are stored",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        required=False,
        default=".",
        help="Path to store results.",
    )
    parser.add_argument(
        "-a",
        "--animals",
        required=True,
        default="",
        help="Comma separated list of animals to analyze",
    )

    args = parser.parse_args()
    main(**vars(args))
