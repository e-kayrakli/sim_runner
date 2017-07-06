import os
import util

home_folder = os.getenv('HOME') + '/'

if util.get_hostname() == 'cray':
    default_result_folder = home_folder + 'work/results/'
else:
    default_result_folder = home_folder + 'projects/results/'

