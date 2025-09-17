# -*- coding: UTF-8 -*-
"""
alane表增加左右alane字段，也就是alane的平行车道
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map as pg
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

df_lane = pg.get('mod_lane')
alane = pg.get('alane')
lane_list = []
for index,row in alane.iterrows():
    lanes = row['lane_ids'].split(':')
    lane_list+=lanes
df_lane=df_lane[df_lane['lane_id'].isin(lane_list)]


def is_in_cross(alane_id):
    alane_row = alane[alane['alane_id']==alane_id].iloc[0]
    lanes = alane_row['lane_ids'].split(':')
    if len(lanes) == 1:
        lane_row = df_lane[df_lane['lane_id']==lanes[0]].iloc[0]
        inters_id = lane_row['inters_id']
        if inters_id is not None:
            return True
        else:
            return False
    else:
        return False


def lane_left_side(lane_id,chg_flg):
    if chg_flg in [1,3]:
        lane_row = df_lane[df_lane['lane_id']==lane_id].iloc[0]
        seq = lane_row['lane_seq']
        link = lane_row['link_id']
        df_lane_in_link = df_lane[df_lane['link_id']==link]
        min_seq = df_lane_in_link['lane_seq'].min()
        if seq != min_seq:
            left_seq = seq - 1
            try:
                left_lane = df_lane_in_link[df_lane_in_link['lane_seq']==left_seq]['lane_id'].values[0]
                return left_lane
            except:
                return ''
        else:
            return ''
    else:
        return ''


def lane_right_side(lane_id,chg_flg):
    if chg_flg in [2,3]:
        lane_row = df_lane[df_lane['lane_id']==lane_id].iloc[0]
        seq = lane_row['lane_seq']
        link = lane_row['link_id']
        df_lane_in_link = df_lane[df_lane['link_id']==link]
        max_seq = df_lane_in_link['lane_seq'].max()
        if seq != max_seq:
            right_seq = seq + 1
            try:
                right_lane = df_lane_in_link[df_lane_in_link['lane_seq'] == right_seq]['lane_id'].values[0]
                return right_lane
            except:
                return ''
        else:
            return ''
    else:
        return ''


def alane_left_side(alane_id):
    alane_row = alane[alane['alane_id']==alane_id].iloc[0]
    lanes = alane_row['lane_ids']
    left_list = []
    for lane in lanes.split(':'):
        chg_flg = df_lane[df_lane['lane_id']==lane]['chg_flg'].values[0]
        left_lane = lane_left_side(lane,chg_flg)
        if left_lane != '':
            left_list.append(left_lane)
    if len(left_list) == 0:
        return ''
    else:
        alane_list = []
        for i in left_list:
            j = str(lane_in_which_alane(i))
            alane_list.append(j)
        if len(set(alane_list)) == 1:
            return ','.join(list(set(alane_list)))
        else:
            print(f"check alane left : {','.join([str(x) for x in alane_list])}")
            return ','.join(list(set(alane_list)))


def alane_right_side(alane_id):
    alane_row = alane[alane['alane_id'] == alane_id].iloc[0]
    lanes = alane_row['lane_ids']
    right_list = []
    for lane in lanes.split(':'):
        chg_flg = df_lane[df_lane['lane_id'] == lane]['chg_flg'].values[0]
        right_lane = lane_right_side(lane, chg_flg)
        if right_lane != '':
            right_list.append(right_lane)
    if len(right_list) == 0:
        return ''
    else:
        alane_list = []
        for i in right_list:
            j = str(lane_in_which_alane(i))
            alane_list.append(j)
        if len(set(alane_list)) == 1:
            return ','.join(list(set(alane_list)))
        else:
            print(f"check alane right : {','.join([str(x) for x in alane_list])}")
            return ','.join(list(set(alane_list)))


def lane_in_which_alane(lane_id):
    alane_id = None
    lanes = alane[alane['lane_ids'].str.contains(lane_id)]
    for index,row in lanes.iterrows():
        lane_ids = row['lane_ids'].split(':')
        if lane_id in lane_ids:
            alane_id = row['alane_id']
            break
    return alane_id


l=[]
for index,row in alane.iterrows():
    alane_id = row['alane_id']
    in_cross = is_in_cross(alane_id)
    if in_cross:
        left_alane,right_alane = '',''
    else:
        left_alane, right_alane = alane_left_side(alane_id),  alane_right_side(alane_id)
    l.append({'alane_id':alane_id,'left':left_alane,'right':right_alane})

df=pd.DataFrame(l)
sql = "drop table if exists df;"
pg.execute(sql)
pg.df_to_pg(df,'df')
sql = ("alter table alane drop column if exists left_alane, drop column if exists right_alane;"
    "alter table alane add column left_alane text, add column right_alane text;"
       "update alane a set left_alane = df.left from df where a.alane_id = df.alane_id;"
       "update alane a set right_alane = df.right from df where a.alane_id = df.alane_id;")
pg.execute(sql)



