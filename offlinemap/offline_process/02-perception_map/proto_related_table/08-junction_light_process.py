# -*- coding: UTF-8 -*-
"""
按照perception map的pb协议，处理junction light数据，生成新表pm_juncion_lights，包含pb中需要的必须字段
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


def lane_in_which_alane(lane_id):
    alane_id = None
    lanes = df_alane[df_alane['lane_ids'].str.contains(lane_id)]
    for index,row in lanes.iterrows():
        lane_ids = row['lane_ids'].split(':')
        if lane_id in lane_ids:
            alane_id = row['alane_id']
            break
    return alane_id




df_rm_light = pg.get('rm_light_panels')
df_alane = pg.get('alane')
df_junction = pg.get('rm_junctions')
df_lane = pg.get('mod_lane')
df_sl = pg.get('pm_stop_lines')


l = []
for traffic_light_id,group in df_rm_light.groupby('traffic_light_id'):
    junc_id = group['junction_id'].values[0]
    junc_utm = wkb.loads(df_junction[df_junction.id==junc_id]['utm'].values[0],hex=True)
    junc_geom = list(junc_utm.exterior.coords)
    points = []
    for i in junc_geom:
        points.append((i[0],i[1]))
    polygon_point = []
    for i in list(Polygon(points).minimum_rotated_rectangle.exterior.coords)[:-1]:
        s = f"{i[0]} {i[1]}"
        polygon_point.append(s)
    
    for index,row in group.iterrows():
        lane_ids = row['lane_ids']
        type = row['type']
        stop_line_ids = row['stop_line_ids']
        # TODO: 先不考虑非机动车信号灯关联的人行道
        alane_ids = []
        # 信号灯关联的lane可能会忽略右转，感知地图里手动添加上，使用路口停止线关联的lane id
        for sl_id in stop_line_ids.split(':'):
            sl_row = df_sl[df_sl.stop_line_id==int(sl_id)].iloc[0]
            for alane_id in sl_row['alane_ids'].split(':'):
                alane_ids.append(alane_id)


        link_id = df_lane[df_lane.lane_id==lane_ids.split(':')[0]]['link_id'].values[0]
        dic= {'junction_light_id':traffic_light_id,'link_id':link_id,'lane_id':lane_ids.split(':')[0],'geometry':wkb.loads(df_junction[df_junction.id==junc_id]['geom'].values[0],hex=True).wkt,
        'junction_position':','.join(polygon_point),'alane_ids':':'.join(alane_ids),'inters_id':junc_id,'type':type,
        'stop_line_id':stop_line_ids} 
        l.append(dic) 

            
            
        


df=pd.DataFrame(l)
sql = "drop table if exists pm_junction_lights;"
pg.execute(sql)
pg.df_to_pg(df,'pm_junction_lights')
sql = ("alter table pm_junction_lights add column geom geometry;"
       "update pm_junction_lights set geom = st_geomfromtext(geometry,4326);"
)
pg.execute(sql)



