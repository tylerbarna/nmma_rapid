'''
Primary script, used to scan through the candidate directory to find new objects, and then submit jobs to the cluster to fit those objects.
'''
import os
import sys
import time
 
from utils.files import scan_objects, check_fit_completion, get_settings
from utils.tools import current_time
from utils.fitting import generate_job, submit_job
from utils.plotting import plot_lightcurves
from utils.git_tools import git_pull, git_push

git_pull() ## pull from github to get latest version of code

settings_file = './settings.json'

models_dicts, settings_dict = get_settings(settings_file)
    
lc_path = settings_dict['candidate_directory']
fit_path = settings_dict['fit_directory']

assert os.path.exists(lc_path), 'Candidate directory does not exist'

new_objects = scan_objects(lc_path, fit_path) ## will return False if no new objects found

sys.exit() if new_objects == False else None ## exit if no new objects found
    
num_fits = len(models_dicts.keys()) *  len(new_objects) ## total number of fits to be performed

## to do: implement check for formatting of lightcurve files and have them be corrected if necessary (basic function is in utils/fileChecks.py as parse_csv)

anticipated_fit_count = 0 ## counter for number of fits that have been submitted
for object in new_objects:
    for model in models_dicts.keys():
        jobFile = generate_job(object, model, settings_dict)
        submit_job(jobFile)
        anticipated_fit_count += 1
        print('[{}] {} of {} fits submitted'.format(current_time(), anticipated_fit_count, num_fits))
print('[{}] All fits submitted'.format(current_time()))
t0 = time.time()
while True:
        time.sleep(60)
        elapsed_time = (time.time() - t0)/60/60 ## elapsed time in hours
        completion_state = check_fit_completion(new_objects, models_dicts, settings_dict, elapsed_time)
        if completion_state == True: break
        
## plot lightcurves
for object in new_objects:
    plot_lightcurves(object, settings_file)
time.sleep(60) ## wait 1 minute to make sure all plots have been saved (may be unnecessary)

commit_message = 'Added fits for objects: {}'.format(', '.join(new_objects))
git_push(commit_message)
## schematically from here:
## 1. Do plotting of results (plot best fit of each of the models_dicts along with the data onto one plot, save to root directory of object fit)
## 2. Have an automated push to github of results (maybe try to automate the commit message to include the object names that have been fit in the commit)


        
