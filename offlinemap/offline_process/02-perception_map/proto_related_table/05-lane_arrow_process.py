# -*- coding: UTF-8 -*-
"""
按照perception map的pb协议，处理lane arrow数据，生成新表pm_lane_arrows，包含pb中需要的必须字段
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map as pg,ctf
import pandas as pd
from shapely import wkt,wkb
from shapely.geometry import Polygon
import warnings
warnings.filterwarnings('ignore')



'''
UNKNOWN = 0;
UTURN = 1; //掉头
LEFT = 2; //左转
STRAIGHT = 3; //直行
RIGHT = 4; //右转
LEFT_UTURN = 5; //左转+掉头
STRAIGHT_UTURN = 6; //直行+掉头
FORBID_UTURN = 7; //禁止掉头
STRAIGHT_LEFT = 8; //直行+左转
LEFT_RIGHT = 9; //左转+右转
FORBID_LEFT = 10; //禁止左转
LEFT_RIGHT_STRAIGHT = 11; //左转+右转+直行
STRAIGHT_RIGHT = 12; //直行+右转
FORBID_RIGHT = 13; //禁止右转
LEFT_MERGE = 14; //向左合流
RIGHT_MERGE = 15; //向右合流
'''

def lane_in_which_alane(lane_id):
    alane_id = None
    lanes = df_alane[df_alane['lane_ids'].str.contains(lane_id)]
    for index,row in lanes.iterrows():
        lane_ids = row['lane_ids'].split(':')
        if lane_id in lane_ids:
            alane_id = row['alane_id']
            break
    print(alane_id)
    return alane_id


df_arrow = pg.get('rns_object_arrow')
df_lane = pg.get('mod_lane')
df_rm_arrow = pg.get('rm_lane_arrows')
df_alane = pg.get('alane')



new_id = 1
l=[]
for index,row in df_arrow.iterrows():
    arrow_id = row['obj_id']
    geom = wkb.loads(row['geom'], hex=True)
    lane_id = df_rm_arrow[df_rm_arrow.id==arrow_id]['lane_id'].values[0]
    utm = ctf.utm(geom)
    box = utm.minimum_rotated_rectangle.exterior
    poly = Polygon(list(box.coords))
    x = poly.representative_point().x
    y = poly.representative_point().y
    exit_confidence = None
    arrow_heading = df_lane[df_lane['lane_id'] == lane_id]['heading'].values[0]
    link_id = df_lane[df_lane.lane_id==lane_id]['link_id'].values[0]
    direction = row['direction']
    arrow_type = df_rm_arrow[df_rm_arrow.id==arrow_id]['type'].values[0]
    alane_id = lane_in_which_alane(lane_id)
    dic = {'lane_arrow_id': new_id, 'x': x, 'y': y, 'exit_confidence': exit_confidence,
            'arrow_heading': arrow_heading,
            'arrow_type': arrow_type, 'geometry': geom.wkt, 'link_id': link_id, 'lane_id': lane_id, 'alane_id':alane_id}
    l.append(dic)
    new_id += 1
df=pd.DataFrame(l)
sql = "drop table if exists pm_lane_arrows;"
pg.execute(sql)
pg.df_to_pg(df,'pm_lane_arrows')
sql = ("alter table pm_lane_arrows add column geom geometry;"
       "update pm_lane_arrows set geom = st_geomfromtext(geometry,4326);"
       "delete from pm_lane_arrows where alane_id is null;")
pg.execute(sql)







