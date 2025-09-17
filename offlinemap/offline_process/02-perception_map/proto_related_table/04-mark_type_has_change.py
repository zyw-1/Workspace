# -*- coding: UTF-8 -*-
"""
判断pm_lane_lines中通一个line id下的lane mark的type是否发生变化
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map as pg
import pandas as pd

df_lane_lines = pg.get('pm_lane_lines')
l=[]
for line_id, group in df_lane_lines.groupby('line_id'):
    type_length = len(set(group['line_type'].tolist()))
    if type_length == 1:
        has_change = 0
    else:
        has_change = 1
    for index,row in group.iterrows():
        lane_line_id = row['lane_line_id']
        l.append({'lane_line_id':lane_line_id,'type_has_change':has_change})

df=pd.DataFrame(l)
sql = "drop table if exists df;"
pg.execute(sql)
pg.df_to_pg(df,'df')
sql = ("alter table pm_lane_lines drop column if exists type_has_change;"
       "alter table pm_lane_lines add column type_has_change int;"
       "update pm_lane_lines a set type_has_change = b.type_has_change from df b where a.lane_line_id = b.lane_line_id;"
       "drop table if exists df;")
pg.execute(sql)