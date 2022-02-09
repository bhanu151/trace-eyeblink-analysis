import numpy as np
from skimage import io
import glob
import datetime
import argparse
import math
import os


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
        bin_line  = frame[0,:]
        data_line = (''.join(([chr(x) for x in bin_line]))).rstrip()
        tokens = data_line.split(',')
        # print(data_line, data_line[0])
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
        if tokens[10] == 'PRE_':
            t_phase.append(1)
        elif tokens[10] == 'CS+':
            t_phase.append(2)
        elif tokens[10] == 'NOCS':
            t_phase.append(2)
        elif tokens[10] == 'TRAC':
            t_phase.append(3)
        elif tokens[10] == 'PUFF': 
            t_phase.append(4)
        elif tokens[10] == 'PROB':
            t_phase.append(4)
            prob = 1
        elif tokens[10] == 'POST':
            t_phase.append(5)
        elif tokens[10] == 'NONE':
            t_phase.append(5)
        else:
            t_phase.append(math.nan)
        eye_int.append(np.double(tokens[-1]))
    return camera_ts, arduino_ts, proto, trial_num, puff, tone, light, scope,\
            cam, t_phase, prob, eye_int


def get_baseline(t_phase, eye_int):
    # print(t_phase)
    try:
        cs_start_frame = t_phase.index(2)
    except ValueError:
        cs_start_frame = len(t_phase)
        
    baseline_start_frame = int(0.1*cs_start_frame)
    baseline_end_frame = baseline_start_frame + int(0.2*cs_start_frame)
    while(baseline_end_frame <= cs_start_frame):
        baseline_window = np.array(eye_int[baseline_start_frame:baseline_end_frame])
        baseline_mean = np.mean(baseline_window)
        baseline_std= np.std(baseline_window)
        overshoot_index = np.where(baseline_window > baseline_mean+2*baseline_std)[0]
        if len(overshoot_index) > 0:
            # print(f"overshoot_index = {overshoot_index}")
            # print(f"blink in baseline")
            # print(baseline_start_frame, baseline_end_frame)
            # print(baseline_window)
            # print(baseline_mean, baseline_std)
            baseline_start_frame = baseline_start_frame + overshoot_index[0] + 1
            baseline_end_frame = baseline_start_frame + int(0.2*cs_start_frame)
        else: 
            # print(baseline_window)
            # print(f"no eyelid flicker")
            break
    return baseline_mean, baseline_std



def measure_eye_blink_response(t_phase, eye_int, IR_flag):
    '''
    Returns the score of eye-blink response, where 
    score = (intensity - mean(baseline_intensity)) / std(baseline_intensity)
    Note: If the ROI was imaged with an IR camera, -score is returned
    '''
    baseline_mean, baseline_std = get_baseline(t_phase, eye_int)
    if IR_flag:
        return -(eye_int - baseline_mean)/baseline_std
    else:
        return (eye_int - baseline_mean)/baseline_std



def main(**kwargs):
    datadir = kwargs['datadir']
    outdir = kwargs['outdir']
    IR_animals = kwargs['IR_animals']
    animals = kwargs['animals'].split(',')
    if animals == '':
        animal_paths  = glob.glob(datadir + '/G*')
    else:
        animal_paths = [datadir+'/'+ anim for anim in animals]
    for animal_path in animal_paths:
        animal_name = animal_path.split('/')[-1]
        print(animal_name)
        if animal_name in IR_animals:
            IR_flag = True
        else:
            IR_flag = False
        if not(os.path.isdir(animal_path)):
            print(f"{animal_name}'s data not found")
            continue
        for session_path in glob.glob(animal_path +'/'+ animal_name +'*[All|An|So|Hr]*'):
            session_name = session_path.split('/')[-1]
            print(session_name)
            if not(os.path.isdir(session_path)):
                continue
            data_dict = {
                'camera_timestamp' : [],
                'arduino_timestamp' : [],
                'protocol' : [],
                'trial_num' : [],
                'puff_US' : [],
                'tone_CS' : [],
                'light_CS' : [],
                'microscope' : [],
                'camera' : [],
                'trial_phase' : [],
                'probe_flag' : [],
                'eye_intensity' : [],
                'blink_response' : []
            }
            for t, trial_video in enumerate(sorted(glob.glob(session_path+'/*.tif*'))):
                try:
                    # print(t, trial_video)
                    frame_stack = io.imread(trial_video)
                    # fec.append([])
                    # camera_timestamp.append([])
                    # arduino_timestamp.append([])
                    # protocol.append([])
                    # trial_num.append([])
                    # puff_US.append([])
                    # tone_CS.append([])
                    # light_CS.append([])
                    # microscope.append([])
                    # camera.append([])
                    # eye_intensity.append([])
                    # camera_timestamp[t], arduino_timestamp[t], protocol[t],\
                            # trial_num[t], puff_US[t], tone_CS[t], light_CS[t],\
                            # microscope[t], camera[t], eye_intensity[t] = \
                            # extract_data_lines(frame_stack)
                    camera_ts, arduino_ts, proto, t_num, puff, tone, light, scope,\
                            cam, t_phase, prob, eye_int = \
                            extract_data_lines(frame_stack)
                    data_dict['camera_timestamp'].append(camera_ts)
                    data_dict['arduino_timestamp'].append(arduino_ts)
                    data_dict['protocol'].append(proto)
                    data_dict['trial_num'].append(t_num)
                    data_dict['puff_US'].append(puff)
                    data_dict['tone_CS'].append(tone)
                    data_dict['light_CS'].append(light)
                    data_dict['microscope'].append(scope)
                    data_dict['camera'].append(cam)
                    data_dict['trial_phase'].append(t_phase)
                    data_dict['probe_flag'].append(prob)
                    data_dict['eye_intensity'].append(eye_int)
                    data_dict['blink_response'].append(measure_eye_blink_response(\
                            t_phase, eye_int, IR_flag))
                except Exception:
                    print(f"Issue with TIFF File {trial_video}.\nSkipping session {session_name}")
                    break
            if outdir=='':
                outdir = datadir
            outpath = outdir + '/' + animal_name 
            if not(os.path.isdir(outpath)):
                os.mkdir(outpath)
            outfile = outpath + '/' + session_name + '_behaviour_data.npy'
            # print(outfile)
            np.save(outfile, data_dict)
            # break
        # break

                



if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Parse behaviour data')
    parser.add_argument('--datadir', '-d'
            , required=True, help='Directory where the behaviour data of all \
            animals\' is stored'
            )
    parser.add_argument('--outdir', '-o'
            , required=False, default='', help='Where to store results.'
            )
    parser.add_argument('--animals', '-a'
            , required=False, default='', help='Comma separated list of \
            animals to analyze'
            )
    parser.add_argument('--IR_animals', '-i'
            , required=False, default='', help='List of animals imaged using \
            IR camera'
            )

    # class Args:
        # pass
    # args = Args()
    # parser.parse_args(namespace=args)
    args = parser.parse_args()
    main(**vars(args))
    