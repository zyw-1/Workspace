# -*- coding: UTF-8 -*-
import os
import sys
path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path)
from lib.pg import PostgreSQL
from lib.config import ctf
import networkx as nx
import pandas as pd
from shapely import wkb
from shapely.geometry import Polygon
import numpy as np



# SRID=32649;LINESTRING(499739.5413198501 4383528.247108218,499738.5380393342 4383530.366193284,499735.2548263126 4383537.295925573,499732.1157932183 4383544.014739724,499729.1407905958 4383550.252869805,499726.5822140907 4383555.581872483,499724.3883543768 4383560.212445161,499722.3043961525 4383564.758085421)

p1 = (499724.3883543768, 4383560.212445161)
p2 = (499722.3043961525, 4383564.758085421)
dy = p2[1]-p1[1]
dx = p2[0]-p1[0]
rad = np.arctan2(dy, dx)
deg = np.degrees(rad)
if 22.5 > deg >= -22.5:
    azimuth = 1 # 东
if 67.5 > deg >= 22.5:
    azimuth = 5 # 东北
if 112.5 > deg >= 67.5:
    azimuth = 4 # 北
if 157.5 > deg >= 112.5:
    azimuth = 8 # 西北
if 180 >= deg >= 157.5 or -157.5 > deg >= -180:
    azimuth = 2 # 西
if -112.5 > deg >= -157.5:
    azimuth = 7 # 西南
if -67.5 > deg >= -112.5:
    azimuth = 3 # 南
if -22.5 > deg >= -67.5:
    azimuth = 6 # 东南
print(deg)
print(azimuth)