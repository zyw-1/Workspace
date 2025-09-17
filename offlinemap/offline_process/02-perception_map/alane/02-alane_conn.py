# -*- coding: UTF-8 -*-
"""
基于alane的连接关系及包含的lane序列，生成stich_lane_conn_type.xlsx，每一条数据是alane的连接点，包含连接点的前继后继alane、连接关系
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map,ctf,srid
import pandas as pd
import networkx as nx
import copy
from shapely import wkb
import math


def construct_lane_net():
    DG = nx.DiGraph()
    dic_neightbors = {}
    for index,row in df_lane.iterrows():
        lane_id = row['lane_id']
        snode = row['snode_id']
        enode = row['enode_id']
        pres = row['pre_lanes'].split(':') if row['pre_lanes'] is not None else []
        sucs = row['suc_lanes'].split(':') if row['suc_lanes'] is not None else []
        DG.add_edge(snode,enode,edge=lane_id)

        dic_neightbors[lane_id] = {'pres':pres,'sucs':sucs}
    
    return DG,dic_neightbors


df_lane = pg_map.get('mod_lane')
# 鄂尔多斯二期暂时放开非机动车道处理，用于可视化路沿
# df_lane = df_lane.drop(df_lane[df_lane.lane_type.isin(['2'])].index)
df_alane = pg_map.get('alane')

DG, dic_neighbors = construct_lane_net()

dic = {}
for index,row in df_alane.iterrows():
    alane_id = row['alane_id']
    print(alane_id)
    lane_ids = row['lane_ids'].split(':')
    
    for lane_id in lane_ids:
        idx = lane_ids.index(lane_id)
        sucs = dic_neighbors[lane_id]['sucs']
        pres = dic_neighbors[lane_id]['pres']
        for index1,row1 in df_alane.iterrows():
            alane_id1 = row1['alane_id']
            lane_ids1 = row1['lane_ids'].split(':')
            for lane_id1 in lane_ids1:
                idx1 = lane_ids1.index(lane_id1)
                if lane_id1 in sucs:
                    if idx==len(lane_ids)-1 and idx1==0:
                        node = df_lane[df_lane.lane_id==lane_id]['enode_id'].values[0]
                        key = f"{alane_id}-{alane_id1}"
                        if key not in dic.keys():
                            dic[key] = [node,'along_side']
                    if idx!=len(lane_ids)-1 and idx1==0:
                        node = df_lane[df_lane.lane_id==lane_id]['enode_id'].values[0]
                        key = f"{alane_id}-{alane_id1}"
                        if key not in dic.keys():
                            dic[key] = [node,'split_parallel']
                    if idx==len(lane_ids)-1 and idx1!=0:
                        node = df_lane[df_lane.lane_id==lane_id]['enode_id'].values[0]
                        key = f"{alane_id}-{alane_id1}"
                        if key not in dic.keys():
                            dic[key] = [node,'merge_parallel']
                if lane_id1 in pres:
                    if idx==0 and idx1==len(lane_ids1)-1:
                        node = df_lane[df_lane.lane_id==lane_id]['snode_id'].values[0]
                        key = f"{alane_id1}-{alane_id}"
                        if key not in dic.keys():
                            dic[key] = [node,'along_side']
                    if idx==0 and idx1!=len(lane_ids1)-1:
                        node = df_lane[df_lane.lane_id==lane_id]['snode_id'].values[0]
                        key = f"{alane_id1}-{alane_id}"
                        if key not in dic.keys():
                            dic[key] = [node,'split_parallel']
                    if idx!=0 and idx1==len(lane_ids1)-1:
                        node = df_lane[df_lane.lane_id==lane_id]['snode_id'].values[0]
                        key = f"{alane_id1}-{alane_id}"
                        if key not in dic.keys():
                            dic[key] = [node,'merge_parallel']
print(dic)
l = []
for i in dic:
    from_ = int(i.split('-')[0])
    to_ = int(i.split('-')[1])
    node = dic[i][0]
    label = dic[i][1]
    l.append({'pre_id':from_,'suc_id':to_,'conn_type':label,'conn_node':node})
print(l)
out_path = f"{path}/offline_process/02-perception_map/alane/stich_lane_conn_type.xlsx"
df=pd.DataFrame(l)
df.to_excel(out_path)


                    
                    




