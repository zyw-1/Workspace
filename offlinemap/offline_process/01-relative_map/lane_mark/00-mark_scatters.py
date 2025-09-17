"""
将lane mark根据曲率，离散成固定距离的散点，生成新表scatter_in_mark
"""

import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)

import pandas as pd
import numpy as np
from shapely import wkt,wkb
from shapely.geometry import Point, LineString
from lib.config import pg_map,ctf
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


def linestring_split(marking_id,utm,rs):
    accu_length = 0
    total_length = utm.length
    l=[]
    sequence = 0
    while accu_length < total_length or len(l) == 0:
        r_index = scatter_index(accu_length,utm)
        r = abs(rs[r_index])
        interval = cal_interval(r)
        # TODO: 生成第一个点，最后一个点到实际线的终点距离为0.8m
        pnt = utm.interpolate(accu_length)
        sequence += 1
        # interval表示该点到下一个点的实际距离
        l.append({'marking_id': marking_id, 'sequence': sequence, 'geom': ctf.lonlat(pnt).wkt, 'utm':pnt.wkt,
                  'interval': interval,'interval_label': interval})
        accu_length += interval
    accu_length -= interval
    l[-1]['interval'] = total_length-accu_length
    pnt = Point(list(utm.coords)[-1])
    sequence += 1
    l.append({'marking_id': marking_id, 'sequence': sequence, 'geom': ctf.lonlat(pnt).wkt, 'utm':pnt.wkt,
                'interval': 0,'interval_label': interval})

    if len(l) >= 2:
        p1 = wkt.loads(l[-1]['utm'])
        p2 = wkt.loads(l[-2]['utm'])
        dis = p1.distance(p2)
        if dis < 1:
            # TODO: 这里用ctf.lonlat(Point(list(utm.coords)[-1])).wkt，可能会导致生成的坐标和原始的对不上，如果需要利用坐标进行匹配，这里需要改
            l.pop(-2)
            l[-1]['sequence'] = l[-1]['sequence'] - 1
            l[-2]['interval'] = l[-2]['interval'] + dis
            
    else:
        import copy
        dic = copy.copy(l[0])
        l.append(dic)
        l[-1]['interval'] = total_length

    l[-2]['interval'] = l[-2]['interval'] - 0.8
    end_pnt = utm.interpolate(total_length-0.8)
    l[-1]['utm'] = end_pnt.wkt
    l[-1]['geom'] =  ctf.lonlat(end_pnt).wkt
    
    return l 


def scatter_index(accu_length,utm):
    coords = list(utm.coords)
    length = 0
    for i in range(len(coords)-1):
        sub_line = LineString([coords[i],coords[i+1]])
        sub_length = sub_line.length
        length += sub_length
        if length > accu_length:
            index = i+1
            break
    else:
        index = len(coords)

    return index

   
def cal_interval(r):
    if r > 2000:
        interval = 4
    elif r >= 50 and r <= 2000:
        interval = 2
    else:
        interval = 1
    return interval


if __name__ == '__main__':
    df_lane = pg_map.get('rns_road_mark')
    drop_list = []
    # df_lane = df_lane[df_lane.marking_id=='2024']
    l=[]
    for index,row in df_lane.iterrows():
        marking_id = row['marking_id']
        print(marking_id)
        utm = wkb.loads(row['utm'])
        geom = wkb.loads(row['geom'],hex=True)
        x = [x[0] for x in list(utm.coords)]
        y = [x[1] for x in list(utm.coords)]
        headings,kappas = compute_path_profile(x,y)
        rs = []
        for i in kappas:
            if i == 0:
                rs.append(100000)
            else:
                rs.append(1/i)
        l += linestring_split(marking_id,utm,rs)
    df=pd.DataFrame(l)

    sql = "drop table if exists scatter_in_mark;"
    pg_map.execute(sql)
    pg_map.df_to_pg(df, 'scatter_in_mark')
    sql = ("alter table scatter_in_mark alter column geom type geometry;"
           "alter table scatter_in_mark alter column utm type geometry;")
    pg_map.execute(sql)




