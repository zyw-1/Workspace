"""
按照relative map的pb协议，处理junction数据，生成新表rm_juncitons，包含pb中需要的必须字段
"""

import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

sys.path.append(path)

import pandas as pd
import numpy as np
from shapely import wkt,wkb
from shapely.geometry import Point, LineString
from lib.config import pg_map,ctf,srid


def is_clockwise(polygon):
    # 获取多边形的顶点坐标
    coords = list(polygon.exterior.coords)
    n = len(coords) - 1  # 去掉最后一个重复的起点

    # 计算有向面积
    area = 0.0
    for i in range(n):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        area += (x2 - x1) * (y2 + y1)
    
    # 如果面积为负，说明点序是顺时针（CW），面积为正则为逆时针（CCW）
    return area > 0


df_junction = pg_map.get('rns_junction_polygon')
df_stopline = pg_map.get('rm_stop_lines')
df_cwalk = pg_map.get('rm_cross_walks')
df_panel = pg_map.get('rm_light_panels')
l = []
for index,row in df_junction.iterrows():
    id = int(row['inters_id'])
    inters_code =  int(row['inters_code'])
    utm =wkb.loads(row['utm'],hex=True)
    coords = list(utm.exterior.coords)
    ll = []
    if is_clockwise(utm):
        coords = coords[:-1][::-1]
    else:
        coords = coords[:-1]
    for i in coords:
        ll.append(f"{i[0]},{i [1]}")
    points = ':'.join(ll)
    type = 0 # TODO: 地图中没有type信息，都先默认为未知
    stop_line_ids = ':'.join(df_stopline[df_stopline.junction_id==id]['id'].astype(str).tolist())
    cross_walk_ids = ':'.join(df_cwalk[df_cwalk.junction_id==id]['id'].astype(str).tolist())
    traffic_light_ids = ':'.join(list(set(df_panel[df_panel.junction_id==id]['traffic_light_id'].astype(str).tolist())))
    l.append({'id':inters_code,'junction_polygon':points,'type':type,'stop_line_ids':stop_line_ids,'cross_walk_ids':cross_walk_ids,
              'traffic_light_ids':traffic_light_ids,'geom':ctf.lonlat(utm).wkt,'utm':utm.wkt})
    
df=pd.DataFrame(l)
df.replace('',None,inplace=True)
sql = ("drop table if exists rm_junctions;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'rm_junctions')
sql = ("alter table rm_junctions alter column geom type geometry;"
       "alter table rm_junctions alter column utm type geometry;"
       f"select UpdateGeometrySRID('rm_junctions', 'utm', {srid});"
       f"select UpdateGeometrySRID('rm_junctions', 'geom', 4326);")
pg_map.execute(sql)

index_name = 'spetial_rm_junctions_on_utm'
table_name = index_name.split('spetial_')[1].split('_on')[0]
sql = f"SELECT * FROM pg_indexes WHERE schemaname = 'public' AND indexname = '{index_name}'; "
data = pg_map.execute(sql,True)
if len(data) == 0:
    sql = f"create index {index_name} on {table_name} using gist(utm);"
    pg_map.execute(sql)

