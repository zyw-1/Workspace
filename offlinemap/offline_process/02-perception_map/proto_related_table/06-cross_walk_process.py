# -*- coding: UTF-8 -*-
"""
按照perception map的pb协议，处理cross walk数据，生成新表pm_cross_walks，包含pb中需要的必须字段
"""

import sys
import os
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map as pg,ctf
import pandas as pd
from shapely import wkt,wkb
from shapely.geometry import Polygon

import warnings
warnings.filterwarnings('ignore')


def lane_in_which_alane(lane_id):
    alane_id = None
    lanes = df_alane[df_alane['lane_ids'].str.contains(lane_id)]
    for index,row in lanes.iterrows():
        lane_ids = row['lane_ids'].split(':')
        if lane_id in lane_ids:
            alane_id = row['alane_id']
            break
    return alane_id


df_cross_walk = pg.get('rns_object_cwalk')

l = []
new_id = 1
df_alane = pg.get('alane')
df_lane = pg.get('mod_lane')
for index,row in df_cross_walk.iterrows():
    link_id = row['link_ids']
    lane_id = row['lane_ids']
    alane_ids = []
    for ii in lane_id.split(':'):
        df1 = df_alane[df_alane['lane_ids'].str.contains(ii)]
        if df1.shape[0] == 0:
            pass
        else:
            alane_id = lane_in_which_alane(ii)
            if alane_id not in alane_ids and alane_id is not None:
                alane_ids.append(alane_id)
                
    if len(alane_ids) !=0 :     
        link_id = df_lane[df_lane['lane_id']==ii]['link_id'].values[0]
        geom = wkb.loads(row['geom'],hex=True)
        utm = ctf.utm(geom)
        exit_confidence = None
        walk_direction = None
        polygon_point = []
        for i in list(utm.minimum_rotated_rectangle.exterior.coords)[:-1]:
            s = f"{i[0]} {i[1]}"
            polygon_point.append(s)     
        dic = {'cross_walk_id': new_id, 'exit_confidence': exit_confidence, 'walk_direction': walk_direction,
                'polygon_point': ','.join(polygon_point), 'link_id': link_id, 'lane_id': ii, 'geometry': geom.wkt,
                'alane_ids':':'.join([str(x) for x in alane_ids])}
        l.append(dic)
    new_id+=1



# l = [{'cross_walk_id': 0, 'exit_confidence': None, 'walk_direction': None,
#                        'polygon_point': None, 'link_id': None, 'lane_id': None, 'geometry': None,
#                        'alane_id':None}]
df=pd.DataFrame(l)
sql = "drop table if exists pm_cross_walks;"
pg.execute(sql)
pg.df_to_pg(df,'pm_cross_walks')
sql = ("alter table pm_cross_walks add column geom geometry;"
       "update pm_cross_walks set geom = st_geomfromtext(geometry,4326);")
pg.execute(sql)
