"""
按照relative map的pb协议，处理cross walk数据，生成新表rm_cross_walks，包含pb中需要的必须字段
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

def cross_walk_direction(poly,lane):
    obb = poly.minimum_rotated_rectangle.exterior
    coords = list(obb.coords)
    line1 = LineString([coords[0], coords[1]])
    line2 = LineString([coords[1], coords[2]])
    intersect1 = line1.intersects(lane)
    intersect2 = line2.intersects(lane)
    if intersect1 is True and intersect2 is False:
        long_edge =  line1
    if intersect1 is False and intersect2 is True:
        long_edge = line2
    if (intersect1 is True and intersect2 is True) or (intersect1 is False and intersect2 is False):
        if line1.length > line2.length:
            long_edge = line1
        else:
            long_edge = line2

    coords = list(long_edge.coords)
    p1 = coords[0]
    p2 = coords[-1]
    dy = p2[1]-p1[1]
    dx = p2[0]-p1[0]
    rad = np.arctan2(dy, dx)

    return rad
    

df_crosswalk = pg_map.get('rns_object_cwalk')
df_lane = pg_map.get('mod_lane')
df_junc = pg_map.get('rns_junction_polygon')
l=[]
for index,row in df_crosswalk.iterrows():
    
    id = int(row['obj_id'])
    utm = wkb.loads(row['utm'])
    coords = list(utm.exterior.coords)
    ll = []
    if is_clockwise(utm):
        coords = coords[:-1][::-1]
    else:
        coords = coords[:-1]
    for i in coords:
        ll.append(f"{i[0]},{i [1]}")
    points = ':'.join(ll)
    lane_ids = row['lane_ids']
    lane_id = lane_ids.split(':')[0]
    lane = wkb.loads(df_lane[df_lane.lane_id==lane_id]['utm'].values[0],hex=True)
    direction = cross_walk_direction(utm,lane)
    if row['inters_id'] is not None:
        junction_id = int(df_junc[df_junc.inters_id==row['inters_id']]['inters_code'].values[0])
        l.append({'id':id,'points':points,'lane_ids':lane_ids,'junction_id':junction_id,'walk_direction':direction,'geom':row['geom'],'utm':row['utm']})
    else:
         l.append({'id':id,'points':points,'lane_ids':lane_ids,'walk_direction':direction,'geom':row['geom'],'utm':row['utm']})


df=pd.DataFrame(l)
df.replace('',None,inplace=True)
sql = ("drop table if exists rm_cross_walks;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'rm_cross_walks')
sql = ("alter table rm_cross_walks alter column geom type geometry;"
       "alter table rm_cross_walks alter column utm type geometry;"
       f"select UpdateGeometrySRID('rm_cross_walks', 'utm', {srid});"
       f"select UpdateGeometrySRID('rm_cross_walks', 'geom', 4326);")
pg_map.execute(sql)



