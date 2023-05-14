'''
Primary script, used to scan through the candidate directory to find new objects, and then submit jobs to the cluster to fit those objects.
'''
import subprocess
import sys
import os
import argparse
import json
import time

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from astropy.time import Time
 
from utils.fileChecks import scan_objects, check_fit_completion
from utils.tools import current_time, generate_job
from utils.fitting import make_object_directory, trigger_time, generate_job, submit_job

import seaborn as sns

with open('settings.json') as f:
    json_file = json.load(f)
    models = json_file['models'] ## list of models to be fit and specific model settings
    settings = json_file['settings'] ## general settings for the project
    
lc_path = settings['candidate_directory']
fit_path = settings['fit_directory']

new_objects = scan_objects(lc_path, fit_path) ## will return False if no new objects found

sys.exit() if new_objects == False else None ## exit if no new objects found
    
num_fits = len(models.keys()) *  len(new_objects) ## total number of fits to be performed

## to do: implement check for formatting of lightcurve files and have them be corrected if necessary (basic function is in utils/fileChecks.py as parse_csv)

anticipated_fit_count = 0 ## counter for number of fits that have been submitted
for object in new_objects:
    for model in models.keys():
        
        jobFile = generate_job(object, model, settings)
        submit_job(jobFile)
        anticipated_fit_count += 1
        print('[{}] {} of {} fits submitted'.format(current_time(), anticipated_fit_count, num_fits))
print('[{}] All fits submitted'.format(current_time()))
t0 = time.time()
while True:
        time.sleep(60)
        elapsed_time = (time.time() - t0)/60/60 ## elapsed time in hours
        completion_state = check_fit_completion(new_objects, models, settings, elapsed_time)
        if completion_state == True: break
        


        
