"""
基于scatter_in_mark生成新表mark_scatters，给散点添加必要的信息，如散点heading、width、offset，curvature
"""
import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)

import pandas as pd
import numpy as np
from shapely import wkt,wkb
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from lib.config import pg_map,srid
from math import hypot, atan2, sqrt
from typing import List, Tuple
import numpy as np
import math


def compute_path_profile(x: List, y: List) -> Tuple[List, List]:
    assert len(x) == len(y), "x and y must be equal"
    headings, kappa, dkappa = [], [], []
    dxs, dys = [], []
    ddys, ddxs = [], []
    dddys, dddxs = [], []
    num = len(x)
    for i in range(num):
        delta_x = 0.0
        delta_y = 0.0
        if i == 0:
            delta_x = x[i + 1] - x[i]
            delta_y = y[i + 1] - y[i]
        elif i == num - 1:
            delta_x = x[i] - x[i - 1]
            delta_y = y[i] - y[i - 1]
        else:
            delta_x = 0.5 * (x[i + 1] - x[i - 1])
            delta_y = 0.5 * (y[i + 1] - y[i - 1])
        dxs.append(delta_x)
        dys.append(delta_y)
        
    for i in range(num):
        headings.append(atan2(dys[i], dxs[i]))
    
    distance = 0.0    
    accumulated_s = [distance]
    fx = x[0]
    fy = y[0]
    nx = 0.0
    ny = 0.0
    for i in range(1, num):
        nx = x[i]
        ny = y[i]
        end_segment_s = hypot(fx - nx, fy - ny)
        accumulated_s.append(end_segment_s + distance)
        distance += end_segment_s
        fx = nx
        fy = ny
        
    for i in range(num):
        xds = 0.0
        yds = 0.0
        if i == 0:
            xds = (x[i + 1] - x[i]) / (accumulated_s[i + 1] - accumulated_s[i])
            yds = (y[i + 1] - y[i]) / (accumulated_s[i + 1] - accumulated_s[i])
        elif i == num - 1:
            xds = (x[i] - x[i - 1]) / (accumulated_s[i] - accumulated_s[i - 1])
            yds = (y[i] - y[i - 1]) / (accumulated_s[i] - accumulated_s[i - 1])
        else:
            xds = (x[i + 1] - x[i - 1]) / (accumulated_s[i + 1] - accumulated_s[i - 1])
            yds = (y[i + 1] - y[i - 1]) / (accumulated_s[i + 1] - accumulated_s[i - 1])
        ddxs.append(xds)
        ddys.append(yds)
        
    for i in range(num):
        xdds = 0.0
        ydds = 0.0
        if i == 0:
            xdds = (ddxs[i + 1] - ddxs[i]) / (accumulated_s[i + 1] - accumulated_s[i])
            ydds = (ddys[i + 1] - ddys[i]) / (accumulated_s[i + 1] - accumulated_s[i])
        elif i == num - 1:
            xdds = (ddxs[i] - ddxs[i - 1]) / (accumulated_s[i] - accumulated_s[i - 1])
            ydds = (ddys[i] - ddys[i - 1]) / (accumulated_s[i] - accumulated_s[i - 1])
        else:
            xdds = (ddxs[i + 1] - ddxs[i - 1]) / (accumulated_s[i + 1] - accumulated_s[i - 1])
            ydds = (ddys[i + 1] - ddys[i - 1]) / (accumulated_s[i + 1] - accumulated_s[i - 1])
        
        dddxs.append(xdds)
        dddys.append(ydds)
    
    for i in range(num):
        xds = ddxs[i]
        yds = ddys[i]
        xdds = dddxs[i]
        ydds = dddys[i]
        k = (xds * ydds - yds * xdds) / (hypot(xds, yds) * (xds ** 2 + yds ** 2) + 1e-6)
        # print(k)
        kappa.append(k)
        
    return headings, kappa


def scatter_offset_on_lane(pnt,marking_id):
    row = df_lane[(df_lane.lmkg_id==marking_id)|(df_lane.rmkg_id==marking_id)].iloc[0]
    geom = wkb.loads(row['utm'],hex=True)
    project = nearest_points(pnt,geom)[1]
    distance_along_line = geom.project(project)

    return distance_along_line



def add_scatter_info(marking_id):
    '''返回一个mark下的所有散点的曲率、航向、宽度、s offset'''
    scatters = df_scatter[df_scatter.marking_id==marking_id]
    scatters = scatters.reset_index()
    mark_utm = wkb.loads(df_mark[df_mark.marking_id == marking_id]['utm'].values[0])
    # first_point = Point(list(mark_utm.coords)[0])
    x,y = [],[]
    # x.append(first_point.x)
    # y.append(first_point.y)
    for index,row in scatters.iterrows():
        geom = wkb.loads(row['utm'],hex=True)
        x.append(geom.x)
        y.append(geom.y)
    try:
        headings, kappas = compute_path_profile(x,y)
        headings = headings[:]
        kappas = kappas[:]
    except Exception as e:
        print(e + f"marking id {marking_id}")

    s_offset = 0
    l = []
    for index,row in scatters.iterrows():
        marking_id = row['marking_id']
        utm = wkb.loads(row['utm'],hex=True)
        heading = round(headings[index],3)
        kappa = round(kappas[index],3)
        s_offset = round(scatter_offset_on_lane(utm,marking_id),3)
        l.append({'marking_id':row['marking_id'],'sequence':row['sequence'],'s_offset':s_offset,
                  'heading':heading,'curvature':kappa,'utm':row['utm'],'geom':row['geom']})
    
    return l 


df_lane = pg_map.get('mod_lane')
df_mark = pg_map.get('rns_road_mark')
df_scatter = pg_map.get('scatter_in_mark')
# df_mark = df_mark[df_mark.marking_id=='2166']
l = []
for index,row in df_mark.iterrows():
    marking_id = row['marking_id']
    print(marking_id)
    ll = add_scatter_info(marking_id)
    l+=ll

df=pd.DataFrame(l)
sql = ("drop table if exists mark_scatters;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'mark_scatters')
sql = ("alter table mark_scatters alter column geom type geometry;"
       "alter table mark_scatters alter column utm type geometry;"
      f"select UpdateGeometrySRID('mark_scatters', 'utm', {srid});")
pg_map.execute(sql)