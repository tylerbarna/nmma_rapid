'''
includes git functions for pulling and pushing to github
'''
from git import Repo

from utils.files import current_time, get_settings


def get_repo():
    '''
    get the repo object from the settings.json file
    
    Args:
        None (uses settings.json)
    
    Returns:
        repo (git.Repo): git repository object
    '''
    _, settings_dict = get_settings()
    repo_path = settings_dict['repo_directory']
    repo = Repo(repo_path)
    return repo

def git_pull():
    '''
    pulls from github repo
    
    Args:
        None (uses settings.json)
    
    Returns:
        None
    '''
    repo = get_repo()
    repo.remotes.origin.pull()
    
def git_add():
    '''
    adds all files from the fit_directory to the github repo. Adds a commit message of the current time and new folders in the fit_directory
    
    Args:
        None (uses settings.json)
        
    Returns:
        None
    '''
    repo = get_repo()
    _, settings_dict = get_settings()
    fit_directory = settings_dict['fit_directory']
    repo.git.add(fit_directory)
    
    
def git_push(commit_message=None):
    '''
    pushes to github repo
    
    Args:
        commit_message (str): commit message to add to the push
    
    Returns:
        None
        
    To-Do:
        - add commit message with what objects were added automatically
    '''
    repo = get_repo()
    git_add()
    if commit_message is not None:
        timed_commit_message = '[{}] {}'.format(current_time(), commit_message)
        print(timed_commit_message)
        repo.git.commit('-m', timed_commit_message)
    try:
        repo.remotes.origin.push()
    except:
        print('[{}] push has failed, attempting automatic merge'.format(current_time()))
        try:
            repo.git.push('--set-upstream', 'origin', 'main')
        except:
            print('[{}] automatic merge has failed, please resolve manually'.format(current_time()))