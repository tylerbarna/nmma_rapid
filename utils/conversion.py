'''
Functions for converting non-standard file formats into the desired .dat format
.dat format should have the following columns: [t, filter, mag, mag_unc]

general idea is that the scanner will scan for
'''

import os
import pandas as pd
from astropy.time import Time
import numpy as np
from utils.files import get_settings, check_correct_file_format

def fritz_file_check(fritzFile):
    '''
    checks if file is in Fritz format. The standard Fritz file format has teh following columns:
    "obj_id","ra","dec","filter","mjd","snr","instrument_id","instrument_name","ra_unc","dec_unc","origin","id","altdata","created_at","annotations","mag","magerr","magsys","limiting_mag","Delete"
    
    Args:
        fritzFile (str): path to Fritz file, a csv
        
    Returns:
        pandas dataframe of Fritz file if in Fritz format, raises exception otherwise
    '''
    df_fritz = pd.read_csv(fritzFile, sep=',')
    fritz_columns = ["obj_id","ra","dec","filter","mjd","snr","instrument_id","instrument_name","ra_unc","dec_unc","origin","id","altdata","created_at","annotations","mag","magerr","magsys","limiting_mag","Delete"]
    if df_fritz.columns.tolist() == fritz_columns:
        return df_fritz
    else:
        raise Exception('{} is not in Fritz format'.format(fritzFile))


def convert_fritz_file(objectFile):
    '''
    intakes Fritz file and converts to .dat format
    
    Args:
        objectFile (str): path to Fritz file, a csv
    
    Returns:
        pandas dataframe of Fritz file converted to contain the following columns: [t, filter, mag, mag_unc] where t is in isot format and filters are part of the standard filter set in nmma (u,g,r,i,z,y,J,H,K)
    '''
    df_fritz = fritz_file_check(objectFile)
    desired_columns = ['t', 'filter', 'mag', 'mag_unc']
    object_name = df_fritz['obj_id'].iloc[0] ## doesn't matter if file is named tableDownload.csv (though preferable if this is not the case)
    ztf_filter_dict = {'ztfg':'g','ztfr':'r','ztfi':'i'}
    
    df_converted = pd.DataFrame(columns=desired_columns)
    df_fritz_ztf = df_fritz[df_fritz['instrument_name'].str.contains('ZTF')]
    df_converted['t'] = Time(pd.to_datetime(df_fritz_ztf['mjd']), format='mjd').isot
    df_converted['filter'] = df_fritz_ztf['filter'].map(ztf_filter_dict) ## should work, but can switch to commented out list comp if it doesn't
    #df_converted['filter'] = [ztf_filter_dict[filter] for filter in df_fritz_ztf['filter']]
    mag, mag_unc = [], []
    for mag_fritz, magerr_fritz, limmag_fritz in zip(df_fritz_ztf['mag'], df_fritz_ztf['magerr'], df_fritz_ztf['limiting_mag']):
        if mag_fritz == np.NaN:
            mag.append(limmag_fritz)
            mag_unc.append(np.inf)
        else:
            mag.append(mag_fritz)
            mag_unc.append(magerr_fritz)
    df_converted['mag'] = mag
    df_converted['mag_unc'] = mag_unc
    
    return df_converted, object_name

def save_converted_file(object_df, object_name, settings):
    '''
    saves converted file to the light curve directory
    
    Args:
        object_df (pandas dataframe): dataframe of converted file
        object_name (str): name of object
        settings (dict): dictionary of settings from settings file
        
    Returns:
        None
    '''
    
    save_path = os.path.join(settings['candidate_directory'], object_name + '.dat')
    
    object_df.to_csv(save_path, sep=' ', index=False, header=False)
    

def ingest_file(object, settings):
    '''
    attempts to do all existing conversion methods on object and saves to the light curve directory for later use
    
    Args:
        object (str): path to object file in ingest file
        settings (dict): dictionary of settings from settings file
        
    Returns:
        None (will save .dat file to settings['candidate_directory'])
    '''
    try: ## check if it's already in the correct format
        df = check_correct_file_format(object)
        object_name = os.path.basename(object).split('.')[0]
        save_converted_file(df, object_name, settings)
    except: ## if not, try to convert it
        try:
            df, object_name = convert_fritz_file(object)
            save_converted_file(df, object_name, settings)
        except:
            pass
        ## additional conversion methods will go here
    
        
            
    
    
    