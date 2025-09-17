# -*- coding: UTF-8 -*-
"""
根据lane的左右边线类型，为mod_lane添加换道信息
"""

import os
import sys
import time
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map


def chg_flg_by_marking(lane_id,lane_row):
    '''
    return: 0:双侧禁止; 1:左可变道; 2:右可变道; 3:双侧都可
    makr type: 
    0:虚拟标线
    1:单虚线
    2:双虚线
    3:单实线
    4:双实线
    5:左虚线右实线
    6:左实线右虚线
    7:短虚线
    '''
    lane_seq = lane_row['lane_seq']
    link_id = lane_row['link_id']
    link_lanes = df_lane[df_lane.link_id==link_id]
    # 检查是否能左变道
    lmkg_id= lane_row['lmkg_id']
    lmkg_type = int(df_mark[df_mark.marking_id==lmkg_id]['type'].values[0])
    if lmkg_type in [1,2,6]:
        # 可左换道，检查左侧是否有lane
        if lane_seq == 1:
            left_chg_flg = 0
        else:
            left_chg_flg = 1
    else:
        left_chg_flg = 0
    
    # 检查是否能左变道
    max_seq = link_lanes['lane_seq'].max()
    rmkg_id= lane_row['rmkg_id']
    rmkg_type = int(df_mark[df_mark.marking_id==rmkg_id]['type'].values[0])
    if rmkg_type in [1,2,5]:
        # 可左换道，检查左侧是否有lane
        if lane_seq == max_seq:
            right_chg_flg = 0
        else:
            right_chg_flg = 1
    else:
        right_chg_flg = 0

    if left_chg_flg == 0 and right_chg_flg == 0:
        chg_flg = 0
    if left_chg_flg == 1 and right_chg_flg == 0:
        chg_flg = 1
    if left_chg_flg == 0 and right_chg_flg == 1:
        chg_flg = 2
    if left_chg_flg == 1 and right_chg_flg == 1:
        chg_flg = 3

    return chg_flg
    


df_lane = pg_map.get('mod_lane')
df_mark = pg_map.get('rns_road_mark')


l = []
for index,row in df_lane.iterrows():
    lane_id = row['lane_id']
    if row['lmkg_id'] is not None:
        chg_flg = chg_flg_by_marking(lane_id,row)
        l.append({'lane_id':lane_id,'chg_flg':chg_flg})

import pandas as pd
df=pd.DataFrame(l)
sql = "drop table if exists df;"
pg_map.execute(sql)
pg_map.df_to_pg(df,'df')
sql = ("update mod_lane a set chg_flg = df.chg_flg from df where df.lane_id=a.lane_id;"
       "drop table if exists df;")
pg_map.execute(sql)

