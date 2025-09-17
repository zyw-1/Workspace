# -*- coding: UTF-8 -*-
"""
为lane mark增加node id，生成新表mod_mark
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map
from shapely.geometry import LineString, Point
from shapely import wkt, wkb
import networkx as nx


def net_construct(df,type):
    if type == 'DiGraph':
        G = nx.DiGraph()
    if type == 'MultiGraph':
        G = nx.MultiGraph()
    for index,row in df.iterrows():
        snode = row['snode_id']
        enode = row['enode_id']
        edge = row['marking_id']
        G.add_edge(snode, enode, edge=edge)

    return G


def succeoosrs_by_marking(marking_id):
    l=[]
    enode = df_marking[df_marking['marking_id']==marking_id]['enode_id'].values[0]
    marking_succeoosrs=[]
    for i in marking_net_dg.successors(enode):
        MG_data = marking_net_mg.get_edge_data(enode, i)
        if len(MG_data) > 1:
            for j in MG_data:
                marking_succeoosrs.append(MG_data[j]['edge'])
        else:
            marking_succeoosrs.append(marking_net_dg.get_edge_data(enode,i)['edge'])
    df_lanes = df_lane[(df_lane['lmkg_id']==marking_id)|(df_lane['rmkg_id']==marking_id)]
    for index,row in df_lanes.iterrows():
        suc_list = [] if row['suc_lanes'] is None or row['suc_lanes'] == '' else row['suc_lanes'].split(':')
        for i in suc_list:
            df = df_lane[df_lane['lane_id']==i]
            lmkg = df['lmkg_id'].values[0]
            rmkg = df['rmkg_id'].values[0]
            if lmkg in marking_succeoosrs:
                l.append(lmkg)
            if rmkg in marking_succeoosrs:
                l.append(rmkg)

    return list(set(l))


def precedessors_by_marking(marking_id):
    l=[]
    snode = df_marking[df_marking['marking_id']==marking_id]['snode_id'].values[0]
    marking_predecessors=[]
    for i in marking_net_dg.predecessors(snode):
        MG_data = marking_net_mg.get_edge_data(i,snode)
        if len(MG_data) > 1:
            for j in MG_data:
                marking_predecessors.append(MG_data[j]['edge'])
        else:
            marking_predecessors.append(marking_net_dg.get_edge_data(i,snode)['edge'])
    df_lanes = df_lane[(df_lane['lmkg_id']==marking_id)|(df_lane['rmkg_id']==marking_id)]
    for index,row in df_lanes.iterrows():
        pre_list = [] if row['pre_lanes'] is None or row['pre_lanes'] == '' else row['pre_lanes'].split(':')
        for i in pre_list:
            df = df_lane[df_lane['lane_id']==i]
            lmkg = df['lmkg_id'].values[0]
            rmkg = df['rmkg_id'].values[0]
            if lmkg in marking_predecessors:
                l.append(lmkg)
            if rmkg in marking_predecessors:
                l.append(rmkg)

    return list(set(l))



df_marking = pg_map.get('rns_road_mark')
for index,row in df_marking.iterrows():
    snode_id = Point(list(wkt.loads(row['geometry']).coords)[0]).wkt
    enode_id = Point(list(wkt.loads(row['geometry']).coords)[-1]).wkt
    df_marking.loc[index, 'snode_id'] = snode_id
    df_marking.loc[index, 'enode_id'] = enode_id


df_lane = pg_map.get('mod_lane')
marking_net_dg = net_construct(df_marking,'DiGraph')
marking_net_mg = net_construct(df_marking,'MultiGraph')

# 生成marking的接续关系
list_pre_markings = []
list_suc_markings = []
for index,row in df_marking.iterrows():
    marking_id = row['marking_id']
    suc_markings = succeoosrs_by_marking(marking_id)
    pre_markings = precedessors_by_marking(marking_id)
    list_suc_markings.append(':'.join(suc_markings))
    list_pre_markings.append(':'.join(pre_markings))
df_marking['pre_marks'] = list_pre_markings
df_marking['suc_marks'] = list_suc_markings


sql = f"drop table if exists mod_mark;"
pg_map.execute(sql)
pg_map.df_to_pg(df_marking,'mod_mark')
sql = (f"alter table mod_mark alter column geom type geometry;"
       f"update mod_mark set pre_marks = null where pre_marks = '';"
       f"update mod_mark set suc_marks = null where suc_marks = '';"
       f"alter table mod_mark add column suc_num int, add column pre_num int;"
        f"update mod_mark set suc_num = 0 where suc_marks is null;"
        f"update mod_mark set suc_num = 1 + length(suc_marks) - length(replace(suc_marks, ':', '')) where suc_marks is not null;"
        f"update mod_mark set pre_num = 0 where pre_marks is null;"
        f"update mod_mark set pre_num = 1 + length(pre_marks) - length(replace(pre_marks, ':', '')) where pre_marks is not null;")
pg_map.execute(sql)


