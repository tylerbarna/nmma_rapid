'''
Contains all functions used for fitting lightcurves.
'''
import subprocess
import os

import numpy as np
import pandas as pd
from astropy.time import Time
 
from utils.tools import current_time, get_filters


def make_object_directory(object):
    os.makedirs(object, exist_ok=True)
    
def trigger_time(object, settings):
    '''
    evaluates fit trigger time based on settings
    
    Args:
        object (str): path to object lightcurve
        settings (dict): dictionary of settings from settings.json
    
    Returns:
        trigger_time (float): trigger time to be used for fitting
    '''
    fit_trigger_time = settings['fit_trigger_time']
    trigger_time_heuristic = settings['trigger_time_heuristic']
    t0 = settings['t0']
    
    # Set the trigger time
    # data = parse_csv(object) ## this may be a point of failure if the file is not formatted correctly
    ## alternate option is to use pandas to read the file, but trigger time will need to be reworked in that case
    data = pd.read_csv(object, sep=' ', header=None, names=['time','filter','mag','mag_err'])
    data = data[data['mag_err'] != np.inf].sort_values(by=['time'])
    if fit_trigger_time:
        # Set to earliest detection in preparation for fit
        # Need to search the whole file since they are not always ordered.
        trigger_time = Time(data['time'].iloc[0], format='isot').mjd

    elif trigger_time_heuristic:
        # One day before the first non-zero point
        trigger_time = Time(data[data['mag'] != 0]['time'].iloc[0], format='isot').mjd - 1
    else:
        # Set the trigger time manually in settings (in this case, 1)
        trigger_time = t0
    return trigger_time

def generate_job(object, model, settings):
    '''
    intakes general settings and model settings to create a bash script to be submitted to the cluster
    
    Args:
        object (str): path to object lightcurve
        model (dict): dictionary of model, including job settings from settings.json (the value corresponding to the model key from the models dictionary in settings.json)
        settings (dict): dictionary of settings from settings.json
        
    Returns:
    Path to generated bash script
    '''
    object_name = object.split('/')[-1].split('.')[0]
    job = model['job']
    outdir = os.path.join(settings['fit_directory'], object, model['name'])
    make_object_directory(outdir)
    
    job_file = os.path.join(outdir, model['name'] + '.sh')
    with open(job_file, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('#SBATCH --name={}\n'.format(object+'_'+model['name']))
        f.write('#SBATCH --time={}\n'.format(job['time']))
        f.write('#SBATCH --nodes={}\n'.format(job['nodes']))
        f.write('#SBATCH --ntasks={}\n'.format(job['ntasks']))
        f.write('#SBATCH --cpus-per-task={}\n'.format(job['cpus-per-task']))
        f.write('#SBATCH --mem{}\n'.format(job['mem']))
        f.write('#SBATCH --output={}\n'.format(os.path.join(outdir, model['name'] + '.out')))
        f.write('#SBATCH --error={}\n'.format(os.path.join(outdir, model['name'] + '.err')))
        
        f.write('source {} {}\n'.format(settings['env']['path'], settings['env']['name']))
        command_string = cmd_str = [#'mpiexec -np',str(args.cpus),
                'light_curve_analysis',
                '--data', object,
                '--model', model['name'],
                '--label', object_name+'_'+model['alias'],
                '--prior', model['prior'],
                '--svd-path', settings['svd_path'],
                '--filters', ','.join(get_filters(object)),
                '--tmin', str(model['tmin']),
                '--tmax', str(model['tmax']),
                '--dt', str(model['dt']),
                '--trigger-time', str(trigger_time(object, settings)),
                '--error-budget', settings['error_budget'],
                '--nlive', str(model['nlive']),
                '--Ebv-max', str(settings['Ebv_max']),
                '--outdir', outdir,
                # '--plot', 
                '--verbose',
                '--detection-limit \"{\'r\':21.5, \'g\':21.5, \'i\':21.5}\"'
                ]
        command_string = ' '.join(command_string)
        f.write(command_string)
        
        print('[{}] Generated {}'.format(current_time(), job_file))

    return job_file


def submit_job(job_file):
    '''
    submits a job to the cluster
    
    Args:
        job_file (str): path to bash script to be submitted
        
    Returns:
        None
    '''
    subprocess.run(' '.join(['sbatch', job_file]), shell=True)
    print('[{}] Submitted {}'.format(current_time(), job_file))
    