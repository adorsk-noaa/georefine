import sys
sys.path.insert(0, '..')

import os
import readline
from pprint import pprint

from flask import *
from app import *

os.environ['PYTHONINSPECT'] = 'True'
