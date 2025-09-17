"""
基于scatter_in_lane生成新表lane_scatters，给散点添加必要的信息，如散点heading、width、offset，curvature
"""

import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

sys.path.append(path)

import pandas as pd
import numpy as np
from shapely import wkt,wkb
from shapely.geometry import Point, LineString
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

        kappa.append(k)

    return headings, kappa


def cal_scatter_width(pnt,heading,lmkg,rmkg):
    k = math.tan(heading)
    if k == 0:
        line = LineString([(pnt.x,pnt.y-5),(pnt.x,pnt.y+5)])
    else:
        k = -1/k
        dx = 5 / math.sqrt(1 + k**2)
        dy = k*dx
        x1 = pnt.x + dx
        y1 = pnt.y + dy
        x2 = pnt.x - dx
        y2 = pnt.y - dy
        line = LineString([(x1, y1), (x2, y2)])
    lpnt = line.intersection(lmkg)
    rpnt = line.intersection(rmkg)
    left_width = pnt.distance(lpnt)
    right_width = pnt.distance(rpnt)
    if math.isnan(left_width):
        left_width = pnt.distance(lmkg)
    if math.isnan(right_width):
        right_width = pnt.distance(rmkg)
    return [left_width, right_width]


def add_scatter_info(lane_id):
    '''返回一个lane下的所有散点的曲率、航向、宽度、s offset'''
    scatters = df_scatter[df_scatter.lane_id==lane_id]
    scatters = scatters.sort_values('sequence')
    scatters = scatters.reset_index()
    lane_utm = wkb.loads(df_lane[df_lane.lane_id == lane_id]['utm'].values[0],hex=True)
    # first_point = Point(list(lane_utm.coords)[0])
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
        print(e + f"lane id {lane_id}")

    # import copy
    # first_heading = copy.copy(headings[1])
    # headings[0] = first_heading
    l = []
    s_offset = 0
    lmkg_id = df_lane[df_lane.lane_id == lane_id]['lmkg_id'].values[0]
    rmkg_id = df_lane[df_lane.lane_id == lane_id]['rmkg_id'].values[0]
    lmkg = wkb.loads(df_mark[df_mark.marking_id == lmkg_id]['utm'].values[0])
    rmkg = wkb.loads(df_mark[df_mark.marking_id == rmkg_id]['utm'].values[0])
    for index,row in scatters.iterrows():
        heading = round(headings[index],3)
        angle_deg = math.degrees(heading)
        # angle_deg = (90 - angle_deg) % 360 # 转化为角度(0,360), 正北为0, 顺时针
        angle_deg = angle_deg % 360 # 转化为角度(0,360), 正东为0, 逆时针
        kappa = round(kappas[index],3)
        if pd.isna(kappa):
            kappa = 0
        pnt = wkb.loads(row['utm'],hex=True)
        left_width,right_width = cal_scatter_width(pnt,heading,lmkg,rmkg)
        left_width = round(left_width,3)
        right_width = round(right_width,3)
        # width = df_lane[df_lane.lane_id == lane_id]['width'].values[0]  # 这里先用原始的车道宽度
        
        l.append({'lane_id':row['lane_id'],'sequence':row['sequence'],'s_offset':s_offset,'angle':angle_deg,
                'heading':heading,'curvature':kappa,'left_width':left_width,'right_width':right_width,'width':left_width+right_width,'utm':row['utm'],'geom':row['geom']})
        s_offset += row['interval']
    # except:
    #     l.append({'lane_id':row['lane_id'],'sequence':row['sequence'],'s_offset':0,'angle':0,
    #                 'heading':0,'curvature':0,'left_width':0,'right_width':0,'width':0,'utm':row['utm'],'geom':row['geom']})
    

    return l 


df_lane = pg_map.get('mod_lane')
df_mark = pg_map.get('rns_road_mark')
df_scatter = pg_map.get('scatter_in_lane')
# df_lane = df_lane[df_lane.lane_id=='1279']
l = []
for index,row in df_lane.iterrows():
    lane_id = row['lane_id']
    print(lane_id)
    ll = add_scatter_info(lane_id)
    l+=ll

df=pd.DataFrame(l)
sql = ("drop table if exists lane_scatters;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'lane_scatters')
sql = ("alter table lane_scatters alter column geom type geometry;"
       "alter table lane_scatters alter column utm type geometry;"
       f"select UpdateGeometrySRID('lane_scatters', 'geom', 4326);"
       f"select UpdateGeometrySRID('lane_scatters', 'utm', {srid});")
pg_map.execute(sql)

index_name = 'spetial_lane_scatters_on_utm'
table_name = index_name.split('spetial_')[1].split('_on')[0]
sql = f"SELECT * FROM pg_indexes WHERE schemaname = 'public' AND indexname = '{index_name}'; "
data = pg_map.execute(sql,True)
if len(data) == 0:
    sql = f"create index {index_name} on {table_name} using gist(utm);"
    pg_map.execute(sql)
