import numpy as np
import glob
import datetime
import argparse
import math
import sys
import os
import pandas as pd


def csv_to_imaging(csv_data_path, imaging_data_path, outPath):
    print("##################################################")
    print("CSV TO IMAGING")
    print("##################################################")
    for csvfile in glob.glob(csv_data_path + "/*.csv"):
        animal_name = csvfile.split("/")[-1].split(".")[0]
        csv_data = pd.read_csv(
            csvfile,
            dtype={
                "date": str,
                "experiment_number": str,
                "num_imaging_trials": np.int64,
            },
        )

        print("--------------------------------------------------")
        print(animal_name)
        print("--------------------------------------------------")

        for upi in csv_data["upi"]:
            date = csv_data.loc[csv_data["upi"] == upi, "date"].iloc[0]
            experiment_number = csv_data.loc[
                csv_data["upi"] == upi, "experiment_number"
            ].iloc[0]
            num_imaging_trials = csv_data.loc[
                csv_data["upi"] == upi, "num_imaging_trials"
            ].iloc[0]
            imaging_dir = (
                imaging_data_path
                + "/"
                + animal_name
                + "/"
                + date
                + "/"
                + experiment_number
            )

            print("**************************************************")
            print(date + "/" + experiment_number)
            print("**************************************************")

            trial_files = sorted(glob.glob(imaging_dir + "/*.tif"))
            if len(trial_files) != num_imaging_trials:
                print(len(trial_files), num_imaging_trials)
                print("SESSION_ERROR: Mismatch in number of tiff files")
            file_sizes = []
            for t, trial_file in enumerate(trial_files):
                file_sizes.append(os.stat(trial_file).st_size)

            file_sizes = np.array(file_sizes)
            if len(trial_files) > 0:
                mean_file_size = np.mean(file_sizes)
                error_t = np.where(
                    np.abs((file_sizes - mean_file_size)/mean_file_size) > 0.01
                )[0]
                for et in error_t:
                    print(
                        "TRIAL_ERROR: "
                        + trial_files[et]
                        + " file size ("
                        + str(file_sizes[et])
                        + " bytes) not close to mean ("
                        + str(mean_file_size)
                        + " bytes)"
                    )

            print()
        print()
    print()

    return


def main(**kwargs):
    imaging_data_path = kwargs["imaging_data_path"]
    behavior_data_path = kwargs["behavior_data_path"]
    csv_data_path = kwargs["csv_data_path"]
    outPath = kwargs["outPath"]

    """
        animal_paths  = glob.glob(datadir + '/G*')
    else:
        animal_paths = [datadir+'/'+ anim for anim in animals]
    for animal_path in animal_paths:
        animal_name = animal_path.split('/')[-1]
        print(animal_name)
        if animal_name in IR_animals:
            IR_flag = True
   """
    if outPath != "":
        if not (os.path.isdir(outPath)):
            os.mkdir(outPath)
    else:
        outPath = "."
    sys.stdout = open(outPath + "/file_check_output.txt", "w")

    csv_to_imaging(csv_data_path, imaging_data_path, outPath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check raw data files")
    parser.add_argument(
        "--imaging_data_path",
        "-i",
        required=True,
        help="Path to where the imaging data of all \
            animals is stored",
    )
    parser.add_argument(
        "--behavior_data_path",
        "-b",
        required=True,
        help="Path to where the behavior data of all \
            animals is stored",
    )
    parser.add_argument(
        "--csv_data_path",
        "-c",
        required=True,
        help="Path to where the csv files of all \
            animals are stored",
    )
    parser.add_argument(
        "--outPath",
        "-o",
        required=False,
        default="",
        help="Path to store results."
    )

    args = parser.parse_args()
    main(**vars(args))
