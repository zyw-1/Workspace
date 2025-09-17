# -*- coding: UTF-8 -*-
"""
基于pm_lane_lines_no_distinct对lane mark连接处的散点去重，生成新表pm_lane_lines，保证没有重复坐标的点，并添加必要的信息
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
import pandas as pd
import warnings
from shapely import wkt,wkb
from functools import partial
import pyproj
import shapely.ops as ops
from shapely.geometry import Point
from lib.config import ctf
warnings.filterwarnings('ignore')

'''
前一个mark的终点和后一个mark的起点可以重复, 同一个边线, 所属不同lane时, 只能存在一个点
'''

from lib.config import pg_map as pg
df_lane_lines=pg.get('pm_lane_lines_no_distinct')
df_lane = pg.get('mod_lane')
df_lane = df_lane.drop(df_lane[df_lane.lane_type==2].index)
df_mark = pg.get('mod_mark')
df_alane = pg.get('alane')
# df_alane = df_alane[df_alane['alane_id']==9]
# df_lane_lines = df_lane_lines[df_lane_lines['line_id'].isin([16,33,34])]


def lane_in_which_alane(lane_id):
    alane_id = None
    lanes = df_alane[df_alane['lane_ids'].str.contains(lane_id)]
    for index,row in lanes.iterrows():
        lane_ids = row['lane_ids'].split(':')
        if lane_id in lane_ids:
            alane_id = row['alane_id']
            break
    return alane_id


def generate_lane_lines():
    def has_two_lane(marking):
        try:
            llane = df_rl[df_rl['rmkg_id'] == marking]['lane_id'].values[0]
            rlane = df_rl[df_rl['lmkg_id'] == marking]['lane_id'].values[0]
            return True
        except:
            return False
    
    df = pd.DataFrame()
    for marking, group in df_lane_lines.groupby('marking_id'):
        print(marking)
        # 检查marking下有几个line_id
        line_num = len(set(group['line_id'].tolist()))

        if line_num == 1:  # 如果只有一个line_id, 不需要做处理
            group['side'] = f"{group['alane_id'].values[0]}:{group['side'].values[0]}"
            df = pd.concat([df, group])
        else:  # 目前只处理有两个line_id的情况, 且一左一右
            # if not has_two_lane(marking):
            #     continue
            df_rl = df_lane[(df_lane['lmkg_id'] == marking) | (df_lane['rmkg_id'] == marking)]
            llane = df_rl[df_rl['rmkg_id'] == marking]['lane_id'].values[0]
            rlane = df_rl[df_rl['lmkg_id'] == marking]['lane_id'].values[0]
            lalane = lane_in_which_alane(llane)
            ralane = lane_in_which_alane(rlane)
            ralane = df_alane[df_alane['alane_id']==ralane]
            lalane = df_alane[df_alane['alane_id']==lalane]
            rmark_list = []
            lmark_list = []
            for lane_id in lalane['lane_ids'].values[0].split(':'):
                row = df_lane[df_lane['lane_id'] == lane_id].iloc[0]
                rmark_list.append(row['rmkg_id'])
            for lane_id in ralane['lane_ids'].values[0].split(':'):
                row = df_lane[df_lane['lane_id'] == lane_id].iloc[0]
                lmark_list.append(row['lmkg_id'])
            if set(rmark_list) == set(lmark_list):  # 如果两个alane公用的marking一样, 保留任意一个marking的散点即可
                group1 = group[group['side'] == 'right']
                group1['side'] = f"{lalane['alane_id'].values[0]}:right,{ralane['alane_id'].values[0]}:left"
                df = pd.concat([df, group1])
            else:  # 如果不共用一个marking, 判断保留一条
                group1 = group[group['side'] == 'right']
                group1['side'] = f"{lalane['alane_id'].values[0]}:right,{ralane['alane_id'].values[0]}:left"
                df = pd.concat([df, group1])

    sql = "drop table if exists pm_lane_lines;"
    pg.execute(sql)
    pg.df_to_pg(df, 'pm_lane_lines')
    sql = ("alter table pm_lane_lines alter column geom type geometry;")
    pg.execute(sql)


def sort_line(alane,line_list,df):
    # def position(pnt,alane_first_pnt,alane_last_pnt):
    #     print(pnt)
    #     k1 = (alane_first_pnt.y-pnt.y)/(alane_first_pnt.x-pnt.x)
    #     k2 = (alane_last_pnt.y-pnt.y)/(alane_last_pnt.x-pnt.x)
    #     d1 = pnt.distance(alane_first_pnt)
    #     d2 = pnt.distance(alane_last_pnt)
    #     if k1*k2 < 0:
    #         pose = 1   # 1表示在alane中间
    #     else:
    #         # if d1 > d2:
    #         #     pose = -1  # 这里的1表示超出alane终点, 
    #         # else:
    #         #     pose = 1  # -1表示超出alane起点
    #         pose = -1
    #     return pose


    if len(line_list) == 1:
        return line_list
    else:
        alane_row = df_alane[df_alane['alane_id']==alane].iloc[0]
        alane_geom = wkb.loads(alane_row['utm'],hex=True)
        alane_first_pnt = Point(alane_geom.coords[0])
        alane_last_pnt = Point(alane_geom.coords[-1])
        dic_dis = {}
        for line in line_list:
            df_line = df[df['line_id']==line].sort_values(by='sequence')
            line_row = df_line.iloc[0]
            first_pnt = ctf.utm(wkt.loads(line_row['geometry']))
            # pose = position(first_pnt, alane_first_pnt, alane_last_pnt)
            # dis = pose*alane_first_pnt.distance(first_pnt)
            dis = alane_geom.project(first_pnt)
            dic_dis[line]=dis
        dic_dis = dict(sorted(dic_dis.items(),key = lambda x:x[1]))
        sort_line_list = list(dic_dis.keys())
        return sort_line_list


def alane_side():
    dic = {}
    df = pg.get('pm_lane_lines')
    for index,row in df_alane.iterrows():
        alane = row['alane_id']
        df1=df[df['side'].str.contains(str(alane)+':')]
        for index1,row1 in df1.iterrows():
            side = row1['side']
            line_id = row1['line_id']
            for i in side.split(','):
                j=i.split(':')
                if int(j[0]) == alane:
                    if alane not in dic:
                        dic[alane] = [f"{j[1]}:{line_id}"]
                    else:
                        dic[alane].append(f"{j[1]}:{line_id}")
    dic_side = {}
    for i in dic:
        dic_side[i] = list(set(dic[i]))

    for alane in dic_side:
        left = []
        right = []
        for j in dic_side[alane]:
            side = j.split(':')[0]
            line_id = int(j.split(':')[1])
            if side == 'left':
                left.append(line_id)
            else:
                right.append(line_id)

        sort_left = sort_line(alane,left, df)
        sort_right = sort_line(alane, right, df)
        dic[alane] = [','.join([str(x) for x in sort_left]),','.join([str(x) for x in sort_right])]

    l = []
    for i in dic:
        l.append([i,'left',dic[i][0]])
        l.append([i, 'right', dic[i][1]])

    df1 = pd.DataFrame(l,columns=['alane_id', 'side', 'line_id'])
    df1 = df1.drop_duplicates(subset=['alane_id', 'side', 'line_id'])
    sql = "drop table if exists df;"
    pg.execute(sql)
    pg.df_to_pg(df1, 'df')

    ################################
    '''需要手动检查左右边线序列是否正确'''
    ################################

    sql = ("alter table alane drop column if exists left_line, drop column if exists right_line;"
           "alter table alane add column left_line text, add column right_line text;"
           "update alane a set left_line = b.line_id from df b where a.alane_id = b.alane_id and b.side = 'left';"
           "update alane a set right_line = b.line_id from df b where a.alane_id = b.alane_id and b.side = 'right';"
           "drop table if exists df;")
    pg.execute(sql)


pm_lane_lines_exists = False
if pm_lane_lines_exists:
    alane_side()
else:
    generate_lane_lines()
    # df_alane = df_alane[df_alane['alane_id'] == 9]
    alane_side()


# 修改边线的is_virtual属性
sql = ("alter table pm_lane_lines drop column if exists is_virtual_mod;"
"alter table pm_lane_lines add column is_virtual_mod text;"
"update pm_lane_lines a set is_virtual_mod = b.max from (select line_id, max(is_virtual) from pm_lane_lines group by line_id) b where a.line_id=b.line_id;")
pg.execute(sql)


