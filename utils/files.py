'''
checks for existence of files and retreiving files in various capacities
'''
import os
import json
import glob

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from astropy.time import Time

from utils.tools import current_time
from utils.plotting import combine_dataframes


def scan_objects(lc_path, fits_path):
    '''
    scans directory for lightcurves and compares against the list of directories in the fits folder
    
    Args:
        lc_path (str): path to lightcurve directory
        fits_path (str): path to fits directory
        
    Returns:
        new_objects (list): list of new objects found in lightcurve directory that are not in fits directory
        Note: this does not include the full path, just the object name
    
    To Do: May be better to rework so it uses gitpython to check for newly added objects rather than checking for folders
    '''
    objects = os.listdir(lc_path) ## list of objects in lightcurve directory
    object_names = [object.split('.')[0] for object in objects] ## list of object names in lightcurve directory
    
    fits_objects = os.listdir(fits_path) ## list of objects in fits directory (will be folders)
    
    new_objects_idx = [i for i, object in enumerate(object_names) if object not in fits_objects] ## indices of new objects
    new_objects = [objects[i] for i in new_objects_idx] ## list of new objects (including the extension)
    ## potential concern: could be a problem if there are multiple files for the same object (ie if the dat file has been made prior to this being run)
    if len(new_objects) > 0:
        print('[{}] New objects found: {}'.format(new_objects,current_time()))
        return new_objects
    else:
        print('[{}] No new objects found'.format(current_time()))
        return False
    

def check_fit_completion(objects, models, settings, elapsed_time):
    '''
    Checks for completion status of fits by looking for results.json files in the directory of the object
    
    Args:
        objects (list): path to directories of objects
        models (dict): dictionary of models and their settings
        settings (dict): settings dictionary from settings.json
    '''
    timeout = settings['timeout'] ## timeout in hours (default of 8 hours)
    object_completed_jobs = {object:[] for object in objects} ## dictionary of objects and their completed jobs
    object_uncompleted_jobs = {object:[] for object in objects} ## dictionary of objects and their uncompleted jobs
    for object in objects:
        for model, model_settings in models.items():
            object_directory = os.path.join(settings['fit_directory'], object, model)
            results_file = os.path.join(object_directory, '*_result.json')
            if os.path.exists(results_file):
                object_completed_jobs[object].append(model)
            elif not os.path.exists(results_file):
                object_uncompleted_jobs[object].append(model)
            else:
                continue
    num_completed = sum([len(object_completed_jobs[object]) for object in object_completed_jobs.keys()])
    num_fits = len(models.keys()) * len(objects)
    #print('[{}] {} of {} fits completed'.format(current_time(), num_completed, num_fits))
    if num_completed == num_fits:
        print('[{}] All fits completed'.format(current_time()))
        return True
    elif num_completed < num_fits:
        print('[{}] {} of {} fits remaining ({:.2f} hours elapsed)'.format(current_time(), num_fits - num_completed, num_fits, elapsed_time))
        return False
    elif elapsed_time > timeout:
        print('[{}] Timeout reached'.format(current_time()))
        return True

def get_settings(settings_path='./settings.json'):
    '''
    Retreive the settings from the settings file and split into models and settings
    
    Args:
        settings_path (str): path to settings file (default: './settings.json')
        
    Returns:
        models (dict): dictionary of models and their settings
        settings (dict): dictionary of general settings
    '''
    with open(settings_path, 'r') as f:
        settings_json = json.load(f)
    
    models = settings_json['models']
    settings = settings_json['settings']
    
    return models, settings

def get_results_json_path(settings, object, model):
    '''
    retreive the path to the results.json file from a completed fit
    
    Args:
        settings (dict): dictionary of settings from settings.json
        object (str): name of object
        model (dict): dictionary of model, including job settings from settings.json (see fitting.generate_job for better idea of intended structure)
    
    Returns:
        results_json_path (str): path to results.json file
    '''
    results_json_path = os.path.join(settings['fit_directory'], object, model['model'], '*result.json')
    results_json_path_search = glob.glob(results_json_path)
    if results_json_path_search == 1:
        return results_json_path_search[0]
    elif results_json_path_search == 0:
        print('[{}] No results.json file found for {} {}'.format(current_time(), object, model['model']))
        return None
    return results_json_path

def get_lightcurve_data(data_file, tmax=False,remove_nondetections=False):
    '''
    imports dat file for lightcurve as a pandas dataframe
    
    Args:
        file (str): path to dat file
        tmax (float): maximum time to include in lightcurve
        remove_nondetections (bool): whether to remove nondetections from lightcurve
    
    Returns:
        df (pandas dataframe): dataframe containing lightcurve data (columns: t, filter, mag, mag_unc, model, alias)
    '''
    df = pd.read_csv(data_file, sep=' ', header=None, names=['t', 'filter', 'mag', 'mag_unc'])
    
    df['t'] = Time(pd.to_datetime(df['t'])).mjd ## convert to mjd
    df['t'] = df['t'] - df['t'].min() ## set t=0 to first observation
    df['model'] = 'data'
    df['alias'] = 'data'
    if tmax:
        df = df[df['t'] < tmax]
    df = df[df['mag_unc'] != np.inf] if remove_nondetections else df
    return df

def save_combined_dataframes(data_file, settings_file, sample_times=np.linspace(0.01, 7, 100)):
    '''
    takes the combined lightcurve dataframe and saves it to a csv file located in the lightcurve fit directory
    
    Args:
        data_file (str): path to dat file
        settings_file (str): path to settings file
        sample_times (array): array of times to sample the lightcurve at (default: np.linspace(0.01, 7, 100))
    
    Returns:
        None
    
    To-Do:
        - add option to save to different directory/file
        - add option to save to different file format
        - Currently, I believe it will save all filters to the csv, could cut down on file size by only saving the filters that are observed in the data
    '''
    combined_df = combine_dataframes(data_file, settings_file, sample_times=sample_times)
    object_name = os.path.basename(data_file).split('.')[0]
    output_file = os.path.join(settings_file['fit_directory'],object_name, 'combined_fits.csv')
    os.makedirs(os.path.dirname(output_file), exist_ok=True) ## just to be safe
    
    combined_df.to_csv(output_file, index=False)