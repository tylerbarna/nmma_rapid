# nmma_rapid
The goal of this repo is to have a set of scripts that will allow for nmma and ztf collaborators to drop in a set of light curves and get back a set of fits to various models without additional coding.

The actual fitting is intended to be done on a slurm-based cluster, which has a copy of the repository cloned locally. On the cluster, there is a crontab or scrontab job that runs every 5 minutes and checks for new light curves. If there are new light curves, it will run the fitting script on them.

## Usage
To initiate a fit, you will need to have a light curve object in the standard .dat format. 

## Installation
For those interested in setting it up on their own slurm based system, you will need a functional nmma environment as well as a cron type job that runs the scanner.sh script on the desired interval (will also need to set the environment in scanner.sh). You will also need to modify the settings.json file to point to the correct directories.