# -*- coding: UTF-8 -*-
"""
按照perception map的pb协议，处理feature point数据，生成新表pm_feature_points，包含pb中需要的必须字段
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map,ctf
import pandas as pd
from shapely import wkt

import warnings
warnings.filterwarnings('ignore')

'''
● UNKNOWN_TYPE  0
● MERGE_START //合并起始点  1
● MERGE_END //合并结束点  2
● SPLIT_START //分叉起始点  3
● SPLIT_END //分叉结束点  4
'''

df_feature = pg_map.get('feature_points')

new_id = 1
l = []
for index,row in df_feature.iterrows():
    geometry = row['geometry']
    geom = wkt.loads(geometry)
    utm = ctf.utm(geom)
    x = utm.x
    y = utm.y
    is_split = row['is_split']
    is_merge = row['is_merge']
    start_or_end = row['start_or_end']
    if is_split == 1 and start_or_end == 'start':
        feature_type = 3
    if is_split == 1 and start_or_end == 'end':
        feature_type = 4
    if is_merge == 1 and start_or_end == 'start':
        feature_type = 1
    if is_merge == 1 and start_or_end == 'end':
        feature_type = 2

    dic = {'feature_point_id':new_id,'x':x,'y':y,'feature_type':feature_type,'geometry':geometry}
    l.append(dic)
    new_id+=1

df=pd.DataFrame(l)
print(df)
sql = "drop table if exists pm_feature_points;"
pg_map.execute(sql)
pg_map.df_to_pg(df,'pm_feature_points')
sql = ("alter table pm_feature_points add column geom geometry;"
       "update pm_feature_points set geom = st_geomfromtext(geometry,4326);")
pg_map.execute(sql)



