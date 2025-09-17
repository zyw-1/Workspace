# -*- coding: UTF-8 -*-
"""
基于lane_feature_point，生成lane mark的分合流点，生成新表feature_points
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
import pandas as pd
import networkx as nx
from shapely import wkt
# import matplotlib.pyplot as plt
import warnings
from lib.config import pg_map
warnings.filterwarnings('ignore')


def net_construct(df):
    G = nx.DiGraph()
    for index,row in df.iterrows():
        snode = row['snode_id']
        enode = row['enode_id']
        edge = row['marking_id']
        seq = row['sequence']
        is_virtual = True if row['type'] == 0 else False
        G.add_edge(snode, enode, edge=edge, seq=seq, is_virtual=is_virtual)

    return G


def lane_sort_seq(pre_lanes,suc_lanes,label):
    def lane_azimuth(lane_id):
        sql = f"select case when (a.degrees >= 0 and a.degrees < 45) or (a.degrees >= 315 and a.degrees < 360) then 1 when a.degrees >= 45 and a.degrees < 135 then 2 when a.degrees >= 135 and a.degrees < 225 then 3 when a.degrees >= 225 and a.degrees < 315 then 4 end as azimuth from (select degrees(ST_Azimuth(st_startpoint(geom),st_endpoint(geom))) from mod_lane where lane_id = '{lane_id}') a"
        data = pg_map.execute(sql,return_data=True)
        azimuth = data[0][0]

        return azimuth

    if label == 'split':
        lane_id = pre_lanes[0]
        azimuth = lane_azimuth(lane_id)
        df = df_lane[df_lane['lane_id'].isin(suc_lanes)]
        df['x'] = df['geometry'].apply(lambda i: wkt.loads(i).interpolate(0.5,normalized=True).x)
        df['y'] = df['geometry'].apply(lambda i: wkt.loads(i).interpolate(0.5,normalized=True).y)
        if azimuth == 1:
            df_sort = df.sort_values('x')
        if azimuth == 2:
            df_sort = df.sort_values('y', ascending=False)
        if azimuth == 3:
            df_sort = df.sort_values('x', ascending=False)
        if azimuth == 4:
            df_sort = df.sort_values('y')
        dic = {}
        i = 0
        for index,row in df_sort.iterrows():
            dic[i] = row['lane_id']
            i+=1
        return dic
    if label == 'merge':
        lane_id = suc_lanes[0]
        azimuth = lane_azimuth(lane_id)
        df = df_lane[df_lane['lane_id'].isin(pre_lanes)]
        df['x'] = df['geometry'].apply(lambda i: wkt.loads(i).interpolate(0.5,normalized=True).x)
        df['y'] = df['geometry'].apply(lambda i: wkt.loads(i).interpolate(0.5,normalized=True).y)
        if azimuth == 1:
            df_sort = df.sort_values('x')
        if azimuth == 2:
            df_sort = df.sort_values('y', ascending=False)
        if azimuth == 3:
            df_sort = df.sort_values('x', ascending=False)
        if azimuth == 4:
            df_sort = df.sort_values('y')
        dic = {}
        i = 0
        for index, row in df_sort.iterrows():
            dic[i] = row['lane_id']
            i += 1

        return dic


def check_virtual_mark(node_id,total_net:nx.DiGraph):
    # 检查边线的node是否连接了虚拟边线
    try:
        suc_label = True
        pre_label = True
        for suc in total_net.successors(node_id):
            type = total_net.get_edge_data(node_id,suc)['is_virtual']
            if type: # 连接了虚拟边线
                suc_label = False
                break
        for pre in total_net.predecessors(node_id):
            type = total_net.get_edge_data(pre,node_id)['is_virtual']
            if type:
                pre_label = False
                break

        if suc_label and pre_label:
            return False
        else:
            return True
    except nx.exception.NetworkXError: # 两条线相交生成的点，在netwirk中找不到
        return True





def marking_features(label,sub_marking_net,dic_marking,dic_side):
    def choose_node(label):
        if label == 'split':
            l = []
            for node in sub_marking_net.nodes():
                suc_nums = len(list(sub_marking_net.successors(node)))
                if suc_nums >= 2:
                    l.append(node)
            
        if label == 'merge':
            l = []
            for node in sub_marking_net.nodes():
                pre_nums = len(list(sub_marking_net.predecessors(node)))
                if pre_nums >= 2:
                    l.append(node)
            
        return l

    l = []
    if label == 'split':
        target_node_list = choose_node(label)
        for target_node in target_node_list:
            suc_nums = len(list(sub_marking_net.successors(target_node)))
            if suc_nums > 2:    # 连接超过3个marking，只有分流起点，没有终点
                dic = {'geometry':target_node,'start_or_end':'start','is_split':1,'is_merge':0,'marks':None}
                l.append(dic)
            if suc_nums == 2:
                dic = {'geometry': target_node, 'start_or_end': 'start', 'is_split': 1, 'is_merge': 0,'marks':None}
                l.append(dic)
                llane_rmkg = dic_marking[dic_side[0]][1]
                rlane_lmkg = dic_marking[dic_side[1]][0]
                if llane_rmkg == rlane_lmkg:  # 如果左边lane的rmkg和右边lane的lmkg为同一个，检查这个公用的marking有几个suc
                    public_marking_suc_num = df_marking[df_marking['marking_id']==llane_rmkg]['suc_num'].values[0]
                    if public_marking_suc_num > 1:
                        geometry = df_marking[df_marking['marking_id']==llane_rmkg]['enode_id'].values[0]
                        dic = {'geometry': geometry, 'start_or_end': 'end', 'is_split': 1, 'is_merge': 0,'marks':None}
                        l.append(dic)
                else:  # 如果不共用一个，把左边lane的rmkg和右边lane的lmkg的交点作为流终点
                    line1 = wkt.loads(df_marking[df_marking['marking_id']==llane_rmkg]['geometry'].values[0])
                    line2 = wkt.loads(df_marking[df_marking['marking_id'] == rlane_lmkg]['geometry'].values[0])
                    inters_pnt = line1.intersection(line2)
                    marks = f"{llane_rmkg},{rlane_lmkg}"
                    if len(list(inters_pnt.coords)) > 0:
                        dic = {'geometry': inters_pnt.wkt, 'start_or_end': 'end', 'is_split': 1, 'is_merge': 0,'marks':marks}
                        l.append(dic)
    if label == 'merge':
        target_node_list = choose_node(label)
        for target_node in target_node_list:
            pre_nums = len(list(sub_marking_net.predecessors(target_node)))
            if pre_nums > 2:    # 连接超过3个marking，只有合流终点，没有起点
                dic = {'geometry':target_node,'start_or_end':'end','is_split':0,'is_merge':1,'marks':None}
                l.append(dic)
            if pre_nums == 2:
                dic = {'geometry': target_node, 'start_or_end': 'end', 'is_split': 0, 'is_merge': 1,'marks':None}
                l.append(dic)
                llane_rmkg = dic_marking[dic_side[0]][1]
                rlane_lmkg = dic_marking[dic_side[1]][0]
                if llane_rmkg == rlane_lmkg:  # 如果左边lane的rmkg和右边lane的lmkg为同一个，检查这个公用的marking有几个pre
                    public_marking_pre_num = df_marking[df_marking['marking_id']==llane_rmkg]['pre_num'].values[0]
                    if public_marking_pre_num > 1:
                        geometry = df_marking[df_marking['marking_id']==llane_rmkg]['snode_id'].values[0]
                        dic = {'geometry': geometry, 'start_or_end': 'start', 'is_split': 0, 'is_merge': 1,'marks':None}
                        l.append(dic)
                else:  # 如果不共用一个，把左边lane的rmkg和右边lane的lmkg的交点作为合流起点
                    line1 = wkt.loads(df_marking[df_marking['marking_id']==llane_rmkg]['geometry'].values[0])
                    line2 = wkt.loads(df_marking[df_marking['marking_id'] == rlane_lmkg]['geometry'].values[0])
                    marks = f"{llane_rmkg},{rlane_lmkg}"
                    inters_pnt = line1.intersection(line2)
                    if len(list(inters_pnt.coords)) > 0:
                        dic = {'geometry': inters_pnt.wkt, 'start_or_end': 'start', 'is_split': 0, 'is_merge': 1,'marks':marks}
                        l.append(dic)
    key_list = []
    ll = []
    for i in l:
        if i['geometry'] not in key_list:
            if not check_virtual_mark(i['geometry'],total_net):  # 如果有连接了虚拟mark的点，先不生成特征点
                key_list.append(i['geometry'])
                ll.append(i)

    return ll


df_lane_feature = pg_map.get('lane_feature_point')
df_marking = pg_map.get('mod_mark')
df_lane = pg_map.get('mod_lane')
total_net = net_construct(df_marking)
# check_virtual_mark('POINT (117.288260166155 39.73412059636888)',total_net)

# df_lane_feature = df_lane_feature[df_lane_feature['node_id']=='422']
l = []
for index,row in df_lane_feature.iterrows():
    print(row['node_id'])
    label = row['label']
    pre_lanes = row['pre_lanes'].split(',')
    suc_lanes = row['suc_lanes'].split(',')
    if '' in pre_lanes:
        pre_lanes.remove('')
    if '' in suc_lanes:
        suc_lanes.remove('')
    if len(pre_lanes) > 0 and len(suc_lanes) >  0:
        dic_side = lane_sort_seq(pre_lanes,suc_lanes,label)  # key: lane_seq, 从左到右升序, value: lane id
        lane_list = pre_lanes + suc_lanes
        list_marking = []
        dic_marking = {}  # key: lane id, value: [lmkg id,rmkg id]
        for lane in lane_list:
            lmkg = df_lane[df_lane['lane_id']==lane]['lmkg_id'].values[0]
            rmkg = df_lane[df_lane['lane_id']==lane]['rmkg_id'].values[0]
            list_marking.append(lmkg)
            list_marking.append(rmkg)
            dic_marking[lane] = [lmkg,rmkg]
        df_sub_marking = df_marking[df_marking['marking_id'].isin(list_marking)]
        sub_marking_net = net_construct(df_sub_marking)
        ll = marking_features(label,sub_marking_net,dic_marking,dic_side)
        l += ll

df=pd.DataFrame(l)
print(df)
id_list = []
i = 0
for index,row in df.iterrows():
    i+=1
    id_list.append(i)
df['id'] = id_list

feature_point_table = 'feature_points'
sql = f"drop table if exists {feature_point_table};"
pg_map.execute(sql)
pg_map.df_to_pg(df, feature_point_table)
sql = (f"alter table {feature_point_table} add column geom geometry;"
       f"update {feature_point_table} set geom = st_geomfromtext(geometry,4326);")
pg_map.execute(sql)




'''
representative_point() : linestring用这个函数不一定会输出线的中点
'''








