#!/usr/bin/env python

import sys
sys.path.insert(0, '..')

import os
import readline
from pprint import pprint

from flask import *
from app import *

from georefine.app.projects.models import *

os.environ['PYTHONINSPECT'] = 'True'
