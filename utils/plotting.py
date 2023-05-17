'''
contains functions related to plotting completed fits
'''
import sys
import os
import glob

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from astropy.time import Time
import seaborn as sns

from utils.tools import current_time
from utils.files import get_settings, get_results_json_path, get_lightcurve_data
from utils.lightcurves import generate_best_fit_lightcurve


def combine_dataframes(data_file, settings_file, sample_times=np.linspace(0.01, 7, 100)):
    '''
    combines the data and best fit lightcurve dataframes into one dataframe
    
    Args:
        data_file (str): path to dat file containing lightcurve data
        settings_file (dict): dictionary of settings for nmma job (see fitting.generate_job for better idea of intended structure)
        model (dict): dictionary of model, including job settings from settings.json (see fitting.generate_job for better idea of intended structure)
        sample_times (np.array): array of times to sample the lightcurve at (default is 100 samples from 0.01 to 7 days)
        
    Returns:
        combined_df (pandas dataframe): dataframe containing lightcurve data and best fit lightcurve data
    
    To-Do:
        - make this more robust to fits timing out (currently, I believe it will break if you don't have a results.json file for each model)
    '''
    models_dicts, settings_dict = get_settings(settings_file) ## both dictionaries
    data_df = get_lightcurve_data(data_file, remove_nondetections=settings_dict['remove_nondetections'])
    object_name = os.path.basename(data_file).split('.')[0] ## assumes that the output folder is not altered
    
    model_result_paths = [get_results_json_path(settings_dict, object_name, model_dict) for model_dict in models_dicts]
    model_lightcurves = [generate_best_fit_lightcurve(model_result_path, model_dict, sample_times=sample_times) for model_result_path, model_dict in zip(model_result_paths, models_dicts)]
    
    all_lightcurves = [data_df] + model_lightcurves
    combined_df = pd.concat(all_lightcurves, axis=0, ignore_index=True)
    
    return combined_df
    

def plot_lightcurves(data_file, settings_file, sample_times=np.linspace(0.01,7,100)):
    '''
    Retrieve the best fit lightcurves from all models and plot them together with the data
    
    Args:
        data_file (str): path to dat file containing lightcurve data
        settings_file (dict): dictionary of settings for nmma job (see fitting.generate_job for better idea of intended structure)
        sample_times (np.array): array of times to sample the lightcurve at (default is 100 samples from 0.01 to 7 days)
        
    Returns:
        fig, axs (matplotlib figure and axis objects): figure and axis objects for the plot
        
    To-Do:
        - add an option to calculate and plot residuals (may need to be a seperate function since the models are not sampled at the same times as the data)
    '''
    settings_dict, models_dicts = get_settings(settings_file)
    object_name = os.path.basename(data_file).split('.')[0]
    lightcurve_df = combine_dataframes(data_file, settings_file, sample_times=sample_times)
    observed_filters = lightcurve_df[(lightcurve_df['mag_err'] != np.inf) & (lightcurve_df['model'] == 'data')]['filter'].unique() ## finds the filters in the real data that have observations, used to filter the models
    if len(observed_filters) == 0:
        print("[{}] No observations in the data file, cannot plot lightcurves".format(current_time()))
        return None, None
    
    unfit_models = lightcurve_df[lightcurve_df['filter'].all() == np.nan]['model'].unique().tolist() ## list of models that have not been fit to the data
    unfit_models_and_data = unfit_models + ['data']
    fit_models = lightcurve_df['model'].unique().tolist() ## list of models (includes data and any that weren't fit to the data)
    fit_models = [model for model in fit_models if model not in unfit_models_and_data] ## list of models that were fit to the data
    if len(fit_models) == 0:
        print("[{}] No models were fit to the data, cannot plot lightcurves".format(current_time()))
        return None, None
    data_df = lightcurve_df[lightcurve_df['model'] == 'data'] ## only data lightcurve
    models_df = lightcurve_df[lightcurve_df['model'].isin(fit_models)] ## only successfully fit model lightcurves
    ## probably a more elegant way to do the above
    
    
    fig, axs = plt.subplots(1,len(observed_filters), figsize=(len(8, observed_filters)*4), sharex=True, facecolor='w', edgecolor='k')
    for filter, ax in zip(observed_filters, axs):
        filtered_data_df = data_df[data_df['filter'] == filter]
        filtered_data_detections_df = filtered_data_df[filtered_data_df['mag_err'] != np.inf]
        filtered_data_df_non_detections_df = filtered_data_df[filtered_data_df['mag_err'] == np.inf]
        filtered_models_df = models_df[models_df['filter'] == filter]

        ax.scatter(filtered_data_detections_df['time'], filtered_data_detections_df['mag'], c='k', marker='o', label='data', zorder=101)
        ax.scatter(filtered_data_df_non_detections_df['time'], filtered_data_df_non_detections_df['mag'], c='k', marker='v', label=None, zorder=100)
        
        for model in filtered_models_df['model'].unique():
            filtered_model_df = filtered_models_df[filtered_models_df['model'] == model]
            model_label = model + ' ({})'.format(filtered_model_df['alias'].unique()[0])
            model_color = models_dicts[model]['color']
            ax.plot(filtered_model_df['time'], filtered_model_df['mag'], label=model_label,c=model_color)
        
        ax.set_ylim(22,12)
        ax.grid()
        ax.set_ylabel(f'{filter}',rotation=0, labelpad=12, fontsize=16)
        ax.legend() if ax == axs[0] else None
        ax.set_xlabel('Time (days)', fontsize=16) if ax == axs[-1] else None
        ax.set_title(f'{object_name}', fontsize=16)
     
    fig.tight_layout()
    for ext in ['png', 'pdf']:
        fig_save_path = os.path.join(settings_dict['output_folder'], 'lightcurve_plots', f'{object_name}_lightcurve.{ext}')
        os.makedirs(os.path.dirname(fig_save_path), exist_ok=True)
        fig.savefig(fig_save_path)
        
    return fig, axs
    