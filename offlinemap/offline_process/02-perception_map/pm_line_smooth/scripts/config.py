# -*- coding: UTF-8 -*-
import os
import sys
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path)
import re
import networkx as nx
from lib.database.pg import PostgreSQL
from lib.geometry.coord_trans import CoordTransformer


pg_map = PostgreSQL('postgres:qidi@123@10.203.3.61:5432/cl2_map')






