# -*- coding: UTF-8 -*-
"""
基于lane的拓扑连接关系识别lane的分合流点，原则为一个lane有超过两个前继/后继，则为分流/合流，生成新表lane_feature_point
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
import pandas as pd
import networkx as nx
from lib.config import pg_map

def net_construct(df):
    G = nx.DiGraph()
    for index,row in df.iterrows():
        snode = row['snode_id']
        enode = row['enode_id']
        edge = row['lane_id']
        G.add_edge(snode, enode, edge=edge)

    return G


def node_conn_vt_lane(node):
    list_pre_nodes = lane_net.predecessors(node)
    list_suc_nodes = lane_net.successors(node)
    l = []
    for pre_node in list_pre_nodes:
        pre_lane = lane_net.get_edge_data(pre_node,node)['edge']
        l.append(pre_lane)
    for suc_node in list_suc_nodes:
        suc_lane = lane_net.get_edge_data(node,suc_node)['edge']
        l.append(suc_lane)
    # list_vt_type = df_lane[df_lane['lane_id'].isin(l)]['vt_type'].tolist()
    list_inters_id = df_lane[df_lane['lane_id'].isin(l)]['inters_id'].tolist()
    label = True
    for i in list_inters_id:
        if i is not None or not pd.isna(i):  # 路口内虚拟车道不生成
            label = False

    return label


df_lane = pg_map.get('mod_lane')
lane_net = net_construct(df_lane)
l=[]
for node in lane_net.nodes:
    vt_type = node_conn_vt_lane(node)
    if vt_type is True:
        list_pre_nodes = list(lane_net.predecessors(node))
        list_suc_nodes = list(lane_net.successors(node))
        label = None
        if len(list_pre_nodes) > 1:
            label = 'merge'
        if len(list_suc_nodes) > 1:
            label = 'split'
        if label is not None:
            dic = {'node_id':node,'label':label,
                   'pre_lanes':','.join([lane_net.get_edge_data(i,node)['edge'] for i in list_pre_nodes]),
                   'suc_lanes':','.join([lane_net.get_edge_data(node,i)['edge'] for i in list_suc_nodes])}
            l.append(dic)

df=pd.DataFrame(l)
sql = 'drop table if exists lane_feature_point;'
pg_map.execute(sql)
pg_map.df_to_pg(df,'lane_feature_point')
sql = ("alter table lane_feature_point add column geom geometry;"
       "update lane_feature_point a set geom = b.geom from rns_lane_node b where a.node_id = b.node_id;")
pg_map.execute(sql)















