"""
按照relative map的pb协议，处理lane arrow数据，生成新表rm_lane_arrows，包含pb中需要的必须字段
"""

import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

sys.path.append(path)

import pandas as pd
import numpy as np
from shapely import wkt,wkb
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from lib.config import pg_map,ctf,srid


# TODO: 补全arrow中的lane_ids, 视地图数据而定
def arrow_info(arrow_id,arrow_utm):
    sql = f"select b.lane_id,b.vt_type from rns_object_arrow a, mod_lane b where a.obj_id = '{arrow_id}' and st_intersects(a.geom,b.geom) = true;"
    data = pg_map.execute(sql,True)
    if len(data) == 0: # 箭头不在lane上，手动绑定
        sql = f"select b.lane_id,b.utm from rns_object_arrow a, mod_lane b where a.obj_id = '{arrow_id}' ORDER BY a.geom <-> b.geom LIMIT 1"
        data1 = pg_map.execute(sql,True)
        lane_id = data1[0][0]
        lane = wkb.loads(data1[0][1],hex=True)
        arrow_center = arrow_utm.minimum_rotated_rectangle.representative_point()
        nearest_point = nearest_points(arrow_center, lane)[1]  # 1表示位于lane上的点

        return nearest_point.x, nearest_point.y, lane_id
    elif len(data) == 1:
        lane_id = data[0][0]
        arrow_center = arrow_utm.minimum_rotated_rectangle.representative_point()

        return arrow_center.x, arrow_center.y, lane_id
    else: # arrow与多个lane相交，选择一个非虚拟lane绑定
        arrow_center = arrow_utm.minimum_rotated_rectangle.representative_point()
        for i in data:
            vt_type = i[1]
            lane_id = i[0]
            if vt_type == 0:
                break
        
        return arrow_center.x, arrow_center.y, lane_id
                


df_arrow = pg_map.get('rns_object_arrow')
df_lane = pg_map.get('mod_lane')

'''
UNKNOWN_ARROW_TYPE = 0;
UTURN = 1; //掉头  map: 8
LEFT = 2; //左转  map: 3
STRAIGHT = 3; //直行  map: 1
RIGHT = 4; //右转  map: 2
LEFT_UTURN = 5; //左转+掉头  map: 10
STRAIGHT_UTURN = 6; //直行+掉头  map: 30
FORBID_UTURN = 7; //禁止掉头  map: 101
STRAIGHT_LEFT = 8; //直行+左转  map: 5
LEFT_RIGHT = 9; //左转+右转  map: 6
FORBID_LEFT = 10; //禁止左转  map: 102
LEFT_RIGHT_STRAIGHT = 11; //左转+右转+直行  map: 7
STRAIGHT_RIGHT = 12; //直行+右转  map: 4
FORBID_RIGHT = 13; //禁止右转  map: 103
LEFT_MERGE = 14; //向左合流  map: 16
RIGHT_MERGE = 15; //向右合流  map: 15
'''

dic_direction = {8:1,3:2,1:3,2:4,10:5,30:6,101:7,5:8,6:9,102:10,7:11,4:12,103:13,15:15,16:14}
l = []
for index,row in df_arrow.iterrows():
    arrow_id = row['obj_id']
    arrow_utm = wkb.loads(row['utm'])
    x,y,lane_id = arrow_info(arrow_id,arrow_utm)
    direction = dic_direction.get(int(row['direction']),0)
    heading = df_lane[df_lane.lane_id==lane_id]['heading'].values[0]
    l.append({'id':arrow_id,'point':f"{x},{y}",'type':direction,'heading':heading,'lane_id':lane_id,'geom':wkb.loads(row['geom'],hex=True).wkt,'utm':row['utm']})

df=pd.DataFrame(l)
df.replace('',None,inplace=True)
sql = ("drop table if exists rm_lane_arrows;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'rm_lane_arrows')
sql = ("alter table rm_lane_arrows alter column geom type geometry;"
       "alter table rm_lane_arrows alter column utm type geometry;"
       f"select UpdateGeometrySRID('rm_lane_arrows', 'utm', {srid});"
       f"select UpdateGeometrySRID('rm_lane_arrows', 'geom', 4326);")
pg_map.execute(sql)

    


