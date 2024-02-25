import numpy as np
from skimage import io
import datetime
import argparse
import math
import os
import pandas as pd
from scipy import signal
from cv2 import medianBlur


NUM_MAX_FRAMES = 750
MEDIAN_FILTER_SIZE = 5
SAVGOL_WINDOW_SIZE = 10
SAVGOL_POLYNOMIAL_ORDER = 2


def extract_data_lines_and_eye_pixels(
    frame_stack,
    eye_coords,
    threshold,
    filter_size,
    savgol_window_size,
    savgol_polynomial_order,
    is_white_eye=False,
    fmt="%Y-%m-%dT%H:%M:%S.%f",
):
    arduino_ts = []
    t_phase = []
    prob = False
    eye_openness = []
    x_min, y_min, x_max, y_max = eye_coords

    for frame in frame_stack:
        bin_line = frame[0, :]
        data_line = ("".join(([chr(x) for x in bin_line]))).rstrip()
        tokens = data_line.split(",")
        try:
            arduino_ts.append(datetime.datetime.strptime(tokens[1], fmt))
        except ValueError:
            fmt1 = "%Y-%m-%dT%H:%M:%S"
            arduino_ts.append(datetime.datetime.strptime(tokens[1], fmt1))
        if tokens[10] == "PRE_":
            t_phase.append(1)
        elif tokens[10] == "CS+":
            t_phase.append(2)
        elif tokens[10] == "NOCS":
            t_phase.append(2)
        elif tokens[10] == "TRAC":
            t_phase.append(3)
        elif tokens[10] == "PUFF":
            t_phase.append(4)
        elif tokens[10] == "PROB":
            t_phase.append(4)
            prob = True
        elif tokens[10] == "NONE":
            t_phase.append(4)
        elif tokens[10] == "POST":
            t_phase.append(5)
        else:
            print(f"ERROR: Can't interpret {tokens[10]} in trial {tokens[4]}")
            t_phase.append(math.nan)

        eye_roi = frame[y_min:y_max, x_min:x_max]
        blurred_roi = medianBlur(eye_roi, filter_size)
        binarized_roi = blurred_roi > threshold

        if is_white_eye:
            eye_openness.append(np.sum(binarized_roi))
        else:
            eye_openness.append(np.sum(~binarized_roi))

    smoothened_eye_pixels = list(
        signal.savgol_filter(eye_openness, savgol_window_size, savgol_polynomial_order)
    )

    return (
        arduino_ts,
        t_phase,
        prob,
        smoothened_eye_pixels,
    )


def calc_frac_eye_closure(trial_eye_pixels, cs_start_frame, min_eye_pixels):
    """
    Returns the fraction eye closure, i.e, fec
    The ROI intensities are thresholded and binarized and fec is calculated as:
    fec = #black pixels in ROI / total #pixels in ROI
    """
    baseline_eye_pixels = np.nanmean(trial_eye_pixels[:cs_start_frame])
    fec = [
        1
        - (
            (trial_eye_pixels[i] - min_eye_pixels)
            / (baseline_eye_pixels - min_eye_pixels)
        )
        for i in range(len(trial_eye_pixels))
    ]
    return fec


def main(**kwargs):
    data_path = kwargs["data_path"]
    csv_path = kwargs["csv_path"]
    output_path = kwargs["output_path"]
    ir_animals = kwargs["ir_animals"]
    animals = kwargs["animals"].split(",")
    animal_paths = [data_path + "/" + anim for anim in animals]
    for animal_path in animal_paths:
        animal_name = animal_path.split("/")[-1]
        print(animal_name)
        if animal_name in ir_animals:
            ir_flag = True
        else:
            ir_flag = False
        if not (os.path.isdir(animal_path)):
            print(f"{animal_name}'s data not found")
            continue

        csv_data = pd.read_csv(
            csv_path + "/" + animal_name + ".csv",
            dtype={
                "upi": int,
                "behaviour_code": str,
                "behaviour_session_number": str,
                "xmin:ymin": str,
                "xmax:ymax": str,
                "eye_threshold": int,
                "num_behaviour_trials": int,
            },
        )

        for _, session in csv_data.iterrows():
            session_name = (
                animal_name
                + "_"
                + session["behaviour_code"]
                + "_"
                + str(session["upi"])
            )
            session_path = animal_path + "/" + session_name
            print(session_path)
            if not (os.path.isdir(session_path)):
                continue
            tiff_file_error = False

            csv_error_trials = set()
            if pd.notna(session["skip_behaviour_trials"]):
                csv_error_trials.update(
                    [int(x) for x in session["skip_behaviour_trials"].split(";")]
                )
            if pd.notna(session["missing_behaviour_trials"]):
                csv_error_trials.update(
                    int(x) for x in session["missing_behaviour_trials"].split(";")
                )

            if session["num_behaviour_trials"] - len(csv_error_trials) > 0:
                x_min, y_min = [int(i) for i in session["xmin:ymin"].split(":")]
                x_max, y_max = [int(i) for i in session["xmax:ymax"].split(":")]
                eye_coords = (x_min, y_min, x_max, y_max)

            data_dict = {
                "upi": [],
                "protocol": [],
                "trial_num": [],
                "skip_trial": [],
                "probe_trial": [],
                "cs_start_frame": [],
                "trace_start_frame": [],
                "us_start_frame": [],
                "post_start_frame": [],
                "eye_pixels": [],
                "arduino_timestamp": [],
                "fec": [],
            }
            data_dict["upi"] = [session["upi"]] * session["num_behaviour_trials"]
            data_dict["protocol"] = [session["behaviour_code"]] * session[
                "num_behaviour_trials"
            ]

            for t in range(session["num_behaviour_trials"]):
                trial_video = session_path + f"/{(t+1):03}.tiff"
                if t + 1 in csv_error_trials:
                    data_dict["skip_trial"].append(True)
                    data_dict["arduino_timestamp"].append([np.nan] * NUM_MAX_FRAMES)
                    data_dict["trial_num"].append(t + 1)
                    data_dict["probe_trial"].append(np.nan)
                    data_dict["eye_pixels"].append(np.array([np.nan] * NUM_MAX_FRAMES))
                    data_dict["cs_start_frame"].append(np.nan)
                    data_dict["trace_start_frame"].append(np.nan)
                    data_dict["us_start_frame"].append(np.nan)
                    data_dict["post_start_frame"].append(np.nan)
                else:
                    try:
                        frame_stack = io.imread(trial_video)
                        (
                            arduino_ts,
                            t_phase,
                            prob,
                            eye_pix,
                        ) = extract_data_lines_and_eye_pixels(
                            frame_stack,
                            eye_coords=eye_coords,
                            threshold=session["eye_threshold"],
                            filter_size=MEDIAN_FILTER_SIZE,
                            savgol_window_size=SAVGOL_WINDOW_SIZE,
                            savgol_polynomial_order=SAVGOL_POLYNOMIAL_ORDER,
                            is_white_eye=ir_flag,
                        )
                        t_phase = np.array(t_phase)
                        cs_start_frame = np.where(t_phase == 2)[0][0]
                        trace_start_frame = np.where(t_phase == 3)[0][0]
                        us_start_frame = np.where(t_phase == 4)[0][0]
                        post_start_frame = np.where(t_phase == 5)[0][0]

                        data_dict["skip_trial"].append(False)
                        data_dict["arduino_timestamp"].append(
                            arduino_ts + [np.nan] * (NUM_MAX_FRAMES - len(eye_pix))
                        )
                        data_dict["trial_num"].append(t + 1)
                        data_dict["probe_trial"].append(prob)
                        data_dict["eye_pixels"].append(
                            np.array(
                                eye_pix + [np.nan] * (NUM_MAX_FRAMES - len(eye_pix))
                            )
                        )
                        data_dict["cs_start_frame"].append(cs_start_frame)
                        data_dict["trace_start_frame"].append(trace_start_frame)
                        data_dict["us_start_frame"].append(us_start_frame)
                        data_dict["post_start_frame"].append(post_start_frame)

                    except Exception:
                        print(
                            f"Issue with TIFF File {trial_video}.\nSkipping session {session_name}"
                        )
                        tiff_file_error = True
                        break

            if not tiff_file_error:
                min_eye_pixels = np.nanmin(
                    [
                        np.nanmin(data_dict["eye_pixels"][t])
                        for t in np.arange(session["num_behaviour_trials"])
                    ]
                )

                for t in range(session["num_behaviour_trials"]):
                    if t + 1 in csv_error_trials:
                        data_dict["fec"].append([np.nan] * NUM_MAX_FRAMES)
                    else:
                        data_dict["fec"].append(
                            calc_frac_eye_closure(
                                data_dict["eye_pixels"][t],
                                data_dict["cs_start_frame"][t],
                                min_eye_pixels,
                            )
                        )

                del data_dict["eye_pixels"]

                if output_path == "":
                    output_path = data_path
                outpath = output_path + "/" + animal_name
                if not (os.path.isdir(outpath)):
                    os.mkdir(outpath)
                outfile = (
                    outpath
                    + "/"
                    + f"{animal_name}_{session['upi']}"
                    + "_behaviour_data.csv"
                )

                data_df = pd.DataFrame(data_dict)
                data_df[
                    [f"timestamp_{f:03}" for f in range(NUM_MAX_FRAMES)]
                ] = pd.DataFrame(
                    data_df.arduino_timestamp.tolist(), index=data_df.index
                )
                data_df[[f"fec_{f:03}" for f in range(NUM_MAX_FRAMES)]] = pd.DataFrame(
                    data_df.fec.tolist(), index=data_df.index
                )
                data_df.drop(columns=["arduino_timestamp", "fec"], inplace=True)
                data_df.to_csv(outfile, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse behaviour data")
    parser.add_argument(
        "-d",
        "--data_path",
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
    parser.add_argument(
        "-i",
        "--ir_animals",
        required=False,
        default="",
        help="Comma separated list of animals imaged using IR camera",
    )

    args = parser.parse_args()
    main(**vars(args))
