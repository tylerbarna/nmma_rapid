'''
contains functions related to plotting completed fits
'''
import json
import bilby
import numpy as np

from tools import current_time, read_results_json

def get_absolute_magnitude(distance, mag):
    '''
    converts apparent magnitude to absolute magnitude
    
    Args:
        distance (float): distance to object in Mpc
        mag (float): apparent magnitude of object
        
    Returns:
        absolute_magnitude (float): absolute magnitude of object
    '''
    return mag + 5 * np.log10(distance * 1e6 /10.0)

