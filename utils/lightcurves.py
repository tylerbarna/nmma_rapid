'''
functions related to generating lightcurves
'''
import bilby
import nmma

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from astropy.time import Time
import seaborn as sns

from nmma.em.model import *

from utils.tools import read_results_json, get_lightcurve_model, get_absolute_magnitude

def get_best_params(json_path):
    '''
    retrieves the best fit parameters from a results.json file
    
    Args:
        json_path (str): path to results.json file from nmma fitting
    
    Returns:
        best_params (dict): dictionary of best fit parameters
        likelihood_dict (dict): dictionary of likelihood values
    '''
    results = read_results_json(json_path)
    posterior = results['posterior']
    posterior_keys = list(posterior.keys())
    
    best_log_likelihood_idx = np.argmin(np.abs(posterior['log_likelihood']))
    best_log_likelihood = posterior['log_likelihood'][best_log_likelihood_idx]
    log_evidence = results['log_evidence']
    log_evidence_err = results['log_evidence_err']
    log_bayes_factor = results['log_bayes_factor']
    
    likelihood_dict = {'log_evidence':log_evidence, 'log_evidence_err':log_evidence_err, 'log_bayes_factor':log_bayes_factor, 'log_likelihood':best_log_likelihood}
    best_parameters_dict = dict(zip(posterior_keys, [posterior[key][best_log_likelihood_idx] for key in posterior_keys]))
    return best_parameters_dict, likelihood_dict

def generate_best_fit_lightcurve(json_path, model, sample_times=np.linspace(0.01, 7, 100), **kwargs):
    '''
    Generate the best fit lightcurve from a given nmma results.json file
    
    Args:
        json_path (str): path to results.json file
        model (dict): dictionary of model, including job settings from settings.json (see fitting.generate_job for better idea of intended structure)
        sample_times (np.array): array of times to sample the lightcurve at (default is 100 samples from 0.01 to 7 days)
        
    Returns:
        lightcurve_df (pandas dataframe): dataframe containing best fit lightcurve data
    
    Todo:
        - have some consistent method for generating uncertainties on best fit lightcurves
        - check about lightcurve filters, as I think it might be generating them all
        - similarly, the case where there's no filter (ie the absolute magnitude is not a dictionary), there's no way to tell what the filter is. Maybe have a kwarg for filter?
    '''
    
    if json_path == None: ## double check this won't break when plotting (specifically thinking about the columns)
        return pd.DataFrame({'t':sample_times,
                             'filter':np.full_like(sample_times, np.nan),
                             'mag':np.full_like(sample_times, np.nan),
                             'mag_unc':np.full_like(sample_times, np.nan), 
                             'model':np.full_like(sample_times, model['model']),
                             'alias':np.full_like(sample_times, model['alias']),})
    
    best_parameters_dict, likelihood_dict = get_best_params(json_path)
    luminosity_distance = best_parameters_dict['luminosity_distance']

    lightcurve_model = get_lightcurve_model(model)(sample_times) ## assumes the initialization of sample times is done twice in nmma (see related issue/pr in nmma)
    
    _, apparent_magnitude = lightcurve_model.generate_lightcurve(sample_times, parameters=best_parameters_dict)
    absolute_magnitude = get_absolute_magnitude(luminosity_distance, apparent_magnitude)
    
    lightcurve_df = pd.DataFrame(columns=['t', 'filter', 'mag', 'mag_unc', 'model', 'alias'])
    
    if type(absolute_magnitude) == dict: ## will be a dictionary if there are multiple filters
        filters = list(absolute_magnitude.keys())
        for filter in filters:
            filter_df = pd.DataFrame({'t':sample_times, 
                                      'filter':filter, 'mag':absolute_magnitude[filter], 
                                      'mag_unc':0.0, 
                                      'model':model['name'], 
                                      'alias':model['alias'], 
                                      'log_likelihood':likelihood_dict['log_likelihood'], 
                                      'log_evidence':likelihood_dict['log_evidence'], 
                                      'log_evidence_err':likelihood_dict['log_evidence_err'], 
                                      'log_bayes_factor':likelihood_dict['log_bayes_factor']})
            lightcurve_df = pd.concat([lightcurve_df, filter_df], axis=0, ignore_index=True)
    else:
        assert kwargs['filter'] != None, 'Need to specify filter when passing only one band'
        lightcurve_df = pd.DataFrame({'t':sample_times, 
                                      'filter':kwargs['filter'], 
                                      'mag':absolute_magnitude, 
                                      'mag_unc':0.0, 
                                      'model':model['name'], 
                                      'alias':model['alias'], 
                                      'log_likelihood':likelihood_dict['log_likelihood'], 
                                      'log_evidence':likelihood_dict['log_evidence'], 
                                      'log_evidence_err':likelihood_dict['log_evidence_err'], 
                                      'log_bayes_factor':likelihood_dict['log_bayes_factor']})
    
    return lightcurve_df