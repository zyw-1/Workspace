# -*- coding: UTF-8 -*-
import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map as pg,ctf
import pandas as pd
from shapely import wkt,wkb
from shapely.geometry import LineString

import warnings
warnings.filterwarnings('ignore')


a = [ [ 109.786524712367466, 39.593775576495077 ], [ 109.786526830375209, 39.593772256800932 ], [ 109.786532248636561, 39.593763092989462 ], [ 109.786539563508882, 39.593749277966445 ], [ 109.786547371349599, 39.59373200463758 ], [ 109.786554268515914, 39.593712465908993 ], [ 109.786558851365314, 39.59369185468789 ], [ 109.786559716255013, 39.593671363882791 ], [ 109.786555459542456, 39.593652186403595 ], [ 109.786544677584942, 39.593635515161473 ], [ 109.786525966739802, 39.593622543068548 ] ]

line = LineString(a[::-1])
print(line.wkt)

