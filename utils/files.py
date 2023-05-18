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

def scan_objects(lc_path, fits_path):
    '''
    scans directory for lightcurves and compares against the list of directories in the fits folder
    
    Args:
        lc_path (str): path to lightcurve ingest directory
        fits_path (str): path to fits directory
        
    Returns:
        new_objects (list): list of new objects found in lightcurve directory that are not in fits directory
        Note: this does not include the full path, just the object name
    
    To Do: May be better to rework so it uses gitpython to check for newly added objects rather than checking for folders
    '''
    _, settings_dict = get_settings()
    objects = os.listdir(lc_path) ## list of objects in lightcurve directory
    object_names = np.array([object.split('.')[0] for object in objects]) ## list of object names in lightcurve directory
    object_names = np.unique(object_names) ## unique object names in lightcurve directory (accounts for file conversion)
    
    
    fits_objects = os.listdir(fits_path) ## list of objects in fits directory (will be folders)
    
    new_objects_idx = [i for i, object_name in enumerate(object_names) if object_name not in fits_objects] ## indices of new objects
    new_objects = [objects[i] for i in new_objects_idx] ## list of new objects (including the extension)
    new_object_names = [object_names[i] for i in new_objects_idx] ## list of new object names (no extension)
    ## potential concern: could be a problem if there are multiple files for the same object (ie if the dat file has been made prior to this being run)
    if len(new_objects) > 0:
        print('[{}] New objects found: {}'.format(new_objects,current_time()))
        return new_objects ## returns list of new objects with extension
    else:
        print('[{}] No new objects found'.format(current_time()))
        return False
    
def check_correct_file_format(lc_path):
    '''
    checks that the file is in the correct format. Anticipated format is a .dat file with the following columns: [t, filter, mag, mag_unc] where t is in isot format and filters are part of the standard filter set in nmma (u,g,r,i,z,y,J,H,K)
    
    Args:
        lc_path (str): path to lightcurve file
    
    Returns:
       dataframe if file is in correct format, False otherwise
    
    To-Do:
        - make sure it actually works
        - implement into scanner
    '''
    correct_columns = ['t', 'filter', 'mag', 'mag_unc']
    correct_filters = ['u','g','r','i','z','y','J','H','K']
    
    df = pd.read_csv(lc_path, sep=' ', header=None, names=correct_columns)
    detected_filters = np.unique(df['filter'])
    try: ## tries to convert t to isot format. If broken, not in correct format
        Time(pd.to_datetime(df['t']), format='isot')
    except:
        raise Exception('[{}] Incorrect time format detected. Detected time format: {}. Accepted time format: isot'.format(current_time(),df['t'].dtype))
    if df.shape[1] != len(correct_columns): ## check for correct number of columns
        raise Exception('[{}] Incorrect number of columns detected. Detected columns: {}. Accepted columns: {}'.format(current_time(),df.columns, correct_columns))
    elif any(filter not in correct_filters for filter in detected_filters): ## check for correct filters
        raise Exception('[{}] Incorrect filters detected. Detected filters: {}. Accepted filters: {}'.format(current_time(),detected_filters, correct_filters))
    else: ## if all checks pass, return True
        return check_correct_file_format

    
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
    object_name = os.path.basename(data_file).split('.')[0]
    
    df['t'] = Time(pd.to_datetime(df['t'])).mjd ## convert to mjd
    ## would it break the nmma fit to include a column with the original mjd values?
    df['t'] = df['t'] - df['t'].min() ## set t=0 to first observation
    df['model'] = 'data'
    df['alias'] = object_name ## change this to be the object name
    if tmax:
        df = df[df['t'] < tmax]
    df = df[df['mag_unc'] != np.inf] if remove_nondetections else df
    return df

def check_fit_completion(objects, models, settings, elapsed_time):
    '''
    Checks for completion status of fits by looking for results.json files in the directory of the object
    
    Args:
        objects (list): path to directories of objects
        models (dict): dictionary of models and their settings
        settings (dict): settings dictionary from settings.json
        elapsed_time (float): time elapsed since start of fit in hours
        
    Returns:
        boolean: True if all fits are complete or hit timeout, False otherwise
    
    To-Do:
        - add an argument for the number of anticipated fits to account for any failures in job creation and/or submission (would be a try/except in the scanner.py file)
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