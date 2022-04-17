import numpy as np
from skimage import io
import glob
import datetime
import argparse
import math
import os
import pandas as pd


def extract_data_lines(frame_stack, fmt="%Y-%m-%dT%H:%M:%S.%f"):
    camera_ts = []
    arduino_ts = []
    proto = []
    trial_num = []
    puff = []
    tone = []
    light = []
    scope = []
    cam = []
    t_phase = []
    prob = 0
    eye_int = []
    for frame in frame_stack:
        bin_line = frame[0, :]
        data_line = ("".join(([chr(x) for x in bin_line]))).rstrip()
        tokens = data_line.split(",")
        try:
            camera_ts.append(datetime.datetime.strptime(tokens[0], fmt))
        except ValueError:
            fmt1 = "%Y-%m-%dT%H:%M:%S"
            camera_ts.append(datetime.datetime.strptime(tokens[0], fmt1))
        try:
            arduino_ts.append(datetime.datetime.strptime(tokens[1], fmt))
        except ValueError:
            fmt1 = "%Y-%m-%dT%H:%M:%S"
            arduino_ts.append(datetime.datetime.strptime(tokens[1], fmt1))
        proto.append(tokens[3])
        trial_num.append(np.uint16(tokens[4]))
        puff.append(np.uint8(tokens[5]))
        tone.append(np.uint8(tokens[6]))
        light.append(np.uint8(tokens[7]))
        scope.append(np.uint8(tokens[8]))
        cam.append(np.uint8(tokens[9]))
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
            prob = 1
        elif tokens[10] == "NONE":
            t_phase.append(4)
        elif tokens[10] == "POST":
            t_phase.append(5)
        else:
            print(f"ERROR: Can't interpret {tokens[10]} in trial {trial_num}")
            t_phase.append(math.nan)
        eye_int.append(np.double(tokens[-1]))
    return (
        camera_ts,
        arduino_ts,
        proto,
        trial_num,
        puff,
        tone,
        light,
        scope,
        cam,
        t_phase,
        prob,
        eye_int,
    )


def get_baseline(t_phase, eye_int):
    # print(t_phase)
    try:
        cs_start_frame = t_phase.index(2)
    except ValueError:
        cs_start_frame = len(t_phase)

    baseline_start_frame = int(0.1 * cs_start_frame)
    baseline_end_frame = baseline_start_frame + int(0.2 * cs_start_frame)
    while baseline_end_frame <= cs_start_frame:
        baseline_window = np.array(eye_int[baseline_start_frame:baseline_end_frame])
        baseline_mean = np.mean(baseline_window)
        baseline_std = np.std(baseline_window)
        overshoot_index = np.where(baseline_window > baseline_mean + 2 * baseline_std)[
            0
        ]
        if len(overshoot_index) > 0:
            # print(f"overshoot_index = {overshoot_index}")
            # print(f"blink in baseline")
            # print(baseline_start_frame, baseline_end_frame)
            # print(baseline_window)
            # print(baseline_mean, baseline_std)
            baseline_start_frame = baseline_start_frame + overshoot_index[0] + 1
            baseline_end_frame = baseline_start_frame + int(0.2 * cs_start_frame)
        else:
            # print(baseline_window)
            # print(f"no eyelid flicker")
            break
    return baseline_mean, baseline_std


def measure_eye_blink_response(t_phase, eye_int, ir_flag):
    """
    Returns the score of eye-blink response, where
    score = (intensity - mean(baseline_intensity)) / std(baseline_intensity)
    Note: If the ROI was imaged with an IR camera, -score is returned
    """
    baseline_mean, baseline_std = get_baseline(t_phase, eye_int)
    if ir_flag:
        return -(eye_int - baseline_mean) / baseline_std
    else:
        return (eye_int - baseline_mean) / baseline_std


def calc_frac_eye_closure(frame_stack, eye_coords, percentile, ir_flag):
    """
    Returns the fraction eye closure, i.e, fec
    The ROI intensities are thresholded and binarized and fec is calculated as:
    fec = #black pixels in ROI / total #pixels in ROI
    """
    x_min, y_min, x_max, y_max = eye_coords
    threshold = np.percentile(frame_stack[0], percentile)
    eye_openness = []

    for frame in frame_stack:
        eye_ROI = frame[x_min:x_max, y_min:y_max]
        if ir_flag:
            binarized_ROI = eye_ROI < threshold
            eye_openness.append(np.sum(binarized_ROI) / len(binarized_ROI))
        else:
            binarized_ROI = eye_ROI > threshold
            eye_openness.append(np.sum(np.logical_not(binarized_ROI)) / len(binarized_ROI))
    # TODO take max only in pre stim period
    # print(type(eye_openness))
    fec = [1 - (eye_openness[i] / np.max(eye_openness)) for i in range(len(eye_openness))]
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
                'behaviour_code': str,
                'behaviour_session_number': str,
                'xmin:ymin': str,
                'xmax:ymax': str,
            },
        )

        for _, session in csv_data.iterrows():
            session_name = animal_name + "_" + session["behaviour_code"] + "_" + session["behaviour_session_number"]
            session_path = animal_path + "/" + session_name
            if not (os.path.isdir(session_path)):
                continue
            print(session_name)

            x_min, y_min = [int(i) for i in session["xmin:ymin"].split(":")]
            x_max, y_max = [int(i) for i in session["xmax:ymax"].split(":")]
            eye_coords = (x_min, y_min, x_max, y_max)

            data_dict = {
                "camera_timestamp": [],
                "arduino_timestamp": [],
                "protocol": [],
                "trial_num": [],
                "puff_US": [],
                "tone_CS": [],
                "light_CS": [],
                "microscope": [],
                "camera": [],
                "trial_phase": [],
                "probe_flag": [],
                "eye_intensity": [],
                "blink_response": [],
                "frac_eye_closure": [],
            }

            for t, trial_video in enumerate(
                sorted(glob.glob(session_path + "/*.tif*"))
            ):
                try:
                    frame_stack = io.imread(trial_video)
                    (
                        camera_ts,
                        arduino_ts,
                        proto,
                        t_num,
                        puff,
                        tone,
                        light,
                        scope,
                        cam,
                        t_phase,
                        prob,
                        eye_int,
                    ) = extract_data_lines(frame_stack)
                except Exception:
                    print(
                        f"Issue with TIFF File {trial_video}.\nSkipping session {session_name}"
                    )
                    break
                data_dict["camera_timestamp"].append(camera_ts)
                data_dict["arduino_timestamp"].append(arduino_ts)
                data_dict["protocol"].append(proto)
                data_dict["trial_num"].append(t_num)
                data_dict["puff_US"].append(puff)
                data_dict["tone_CS"].append(tone)
                data_dict["light_CS"].append(light)
                data_dict["microscope"].append(scope)
                data_dict["camera"].append(cam)
                data_dict["trial_phase"].append(t_phase)
                data_dict["probe_flag"].append(prob)
                data_dict["eye_intensity"].append(eye_int)
                data_dict["blink_response"].append(
                    measure_eye_blink_response(t_phase, eye_int, ir_flag)
                )

                fec = calc_frac_eye_closure(frame_stack, eye_coords, percentile=45, ir_flag=ir_flag)
                data_dict["frac_eye_closure"].append(fec)

            if output_path == "":
                output_path = data_path
            outpath = output_path + "/" + animal_name
            if not (os.path.isdir(outpath)):
                os.mkdir(outpath)
            outfile = outpath + "/" + session_name + "_behaviour_data.npy"
            # print(outfile)
            np.save(outfile, data_dict)
            # break
        # break


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
