"""
按照relative map的pb协议，处理lane mark数据，生成新表rm_lane_marks，包含pb中需要的必须字段
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


df_mark = pg_map.get('rns_road_mark')
df_scatters = pg_map.get('mark_scatters')
df_lane = pg_map.get('mod_lane')

'''
UNKNOWN_BOUNDARY = 0; // 未知类型
SINGLE_SOLID = 1; // 单实线
SINGLE_DASH = 2; // 单虚线

map: 
0: 虚拟标线
1: 单虚线
2: 双虚线
3: 单实线
4: 双实线
5: 左虚线右实线
6: 左实线右虚线
7: 短虚线
999: 其他
'''
dic_type = {0:'0',1:'2',2:'2:2',3:'1',4:'1:1',5:'2:1',6:'1:2',7:'2',999:'0'}

'''
UNKNOWN_COLOR = 0; 
WHITE = 1; 
YELLOW = 2;

map: 
1: 白色
2: 黄色
7: 左黄右白
8: 左白右黄
'''
dic_color = {1:'1',2:'2',7:'2:1',8:'1:2'}

l=[]
for mark_id,group in df_scatters.groupby('marking_id'):
    print(mark_id)
    mark_row = df_mark[df_mark.marking_id==mark_id].iloc[0]
    type = int(mark_row['type'])
    is_virtual = 1 if type == 0 else 0
    color = mark_row['color']
    types = dic_type.get(type,0)
    colors = dic_color.get(color,0)
    left_row = df_lane[df_lane.rmkg_id==mark_id]
    right_row = df_lane[df_lane.lmkg_id==mark_id]
    if left_row.shape[0] == 0:
        left_lane = None
    else:
        left_lane = int(left_row['lane_id'].values[0])

    if right_row.shape[0] == 0:
        right_lane = None
    else:
        right_lane = int(right_row['lane_id'].values[0])

    group = group.sort_values('s_offset')
    for index,row in group.iterrows():
        heading = row['heading']
        curvature = row['curvature']
        s = row['s_offset']
        pnt = wkb.loads(row['utm'])
        l.append({'id':int(mark_id),'types':types,'colors':colors,'is_virtual':is_virtual,'left_lane_id':left_lane,'right_lane_id':right_lane,
                 'point':f"{pnt.x},{pnt.y}",'s_offset':s,'heading':heading,'curvature':curvature,'geom':ctf.lonlat(pnt).wkt,'utm':pnt.wkt})

df=pd.DataFrame(l)
df.replace('',None,inplace=True)
sql = ("drop table if exists rm_lane_boundarys;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'rm_lane_boundarys')
sql = ("alter table rm_lane_boundarys alter column geom type geometry;"
       "alter table rm_lane_boundarys alter column utm type geometry;"
       f"select UpdateGeometrySRID('rm_lane_boundarys', 'utm', {srid});"
       f"select UpdateGeometrySRID('rm_lane_boundarys', 'geom', 4326);"
       "alter table rm_lane_boundarys add column lane_id int;"
       "update rm_lane_boundarys set lane_id = left_lane_id::int where left_lane_id is not null;"
       "update rm_lane_boundarys set lane_id = right_lane_id::int where lane_id is null;")
pg_map.execute(sql)





