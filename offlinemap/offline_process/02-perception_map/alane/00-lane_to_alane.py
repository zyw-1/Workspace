# -*- coding: UTF-8 -*-
"""
将原始lane合并成alane，alane表示实际道路中的一条车道，从路口/分流点开始，到路口/合流点结束，生成stich_lane.xlsx，包含alane id及每一个alane包含的原始lane序列
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map,ctf,srid,pg_from
import pandas as pd
import networkx as nx
import copy
from shapely import wkb
import math


def start_end_lane():
    '''
    1.每个路口的in/out links对应的lane作为递归的终止/起始lane
    2.没有后继/前继的lane作为递归的终止/起始lane
    3.路口内虚拟lane的前继/后继作为终止/起始lane
    '''
    start_lanes = []
    end_lanes = []
    all_lane_list = df_lane['lane_id'].tolist()
    for index,row in df_lane.iterrows():
        lane_id = row['lane_id']
        pre_lanes = row['pre_lanes']
        suc_lanes = row['suc_lanes']
        if pre_lanes is None and suc_lanes is not None:
            start_lanes.append(lane_id)
        if pre_lanes is not None and suc_lanes is None:
            end_lanes.append(lane_id)

    for index,row in df_junc_points.iterrows():
        in_links = row['in_links']
        out_links = row['out_links']
        for in_link in in_links.split(':'):
            lane_list = df_lane[df_lane.link_id==in_link]['lane_id'].tolist()
            for i in lane_list:
                if i not in end_lanes:
                    end_lanes.append(i)
        for out_link in out_links.split(':'):
            lane_list = df_lane[df_lane.link_id==out_link]['lane_id'].tolist()
            for i in lane_list:
                if i not in start_lanes:
                    start_lanes.append(i)
    
    df_inters_lane = df_lane.dropna(subset=['inters_id'])

    for index,row in df_inters_lane.iterrows():
        lane_id = row['lane_id']
        pre_lanes = row['pre_lanes'].split(':')
        suc_lanes = row['suc_lanes'].split(':')
        for i in pre_lanes:
            if i not in end_lanes and i in all_lane_list:
                end_lanes.append(i)
        for i in suc_lanes:
            if i not in start_lanes and i in all_lane_list:
                start_lanes.append(i)

    return start_lanes,end_lanes


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


def lane_degree_diff(pre,suc):
    def line_degree(x1,y1,x2,y2):
        dx = x2 - x1
        dy = y2 - y1
        # 计算角度（弧度值）
        angle_rad = math.atan2(dy, dx)
        # 将弧度转换为角度
        angle_deg = math.degrees(angle_rad)
        # 转换为正值（0到360度）
        angle_deg = angle_deg % 360

        return angle_deg

    wkb_utm = df_lane[df_lane.lane_id==pre]['utm'].values[0]
    line1 = wkb.loads(wkb_utm,hex=True)
    line1_coords = list(line1.coords)
    line1_degree = line_degree(line1_coords[-2][0],line1_coords[-2][1],line1_coords[-1][0],line1_coords[-1][1])
    wkb_utm = df_lane[df_lane.lane_id==suc]['utm'].values[0]
    line2 = wkb.loads(wkb_utm,hex=True)
    line2_coords = list(line2.coords)
    line2_degree = line_degree(line2_coords[0][0],line2_coords[0][1],line2_coords[1][0],line2_coords[1][1])

    return abs(line2_degree-line1_degree)
    

def check_next_lane(current_lane):
    global end_lanes
    if len(dic_neighbors[current_lane]['sucs']) == 0:
        next_lane = None
        label = 'end'
    elif len(dic_neighbors[current_lane]['sucs']) == 1:
        next_lane = dic_neighbors[current_lane]['sucs'][0]
        if next_lane in end_lanes:
            label = 'end'
        else:
            next_pres_lanes = dic_neighbors[next_lane]['pres']
            if len(next_pres_lanes) == 1:
                label = 'along'
            if len(next_pres_lanes) > 1:
                label = 'merge'
    else:
        label = 'split'
        next_lanes = dic_neighbors[current_lane]['sucs']
        dic = {}
        for i in next_lanes:
            dic[i] = lane_degree_diff(current_lane,i)

        dic_sort = {k: v for k, v in sorted(dic.items(), key=lambda item: item[1])}

        next_lane = list(dic_sort.keys())[0]


    return next_lane


def check_is_end(current_lane):
    global end_lanes
    if len(dic_neighbors[current_lane]['sucs']) == 0:
        return True
    else:
        if current_lane in end_lanes:
            return True
        else:
            return False


def paraller_lanes(lane):
    row = df_lane[df_lane.lane_id==lane].iloc[0]
    snode = row['snode_id']
    enode = row['enode_id']
    merge_neighbors = df_lane[df_lane.enode_id==enode]['lane_id'].tolist()
    merge_neighbors.remove(lane)
    split_neighbors = df_lane[df_lane.snode_id==snode]['lane_id'].tolist()
    split_neighbors.remove(lane)

    return merge_neighbors + split_neighbors  # TODO: 先不考虑一个lane即使合流主支又是分流主支


def check_lane_label(current_lane):
    label = 'along'
    pre_num = len(dic_neighbors[current_lane]['pres'])
    suc_num = len(dic_neighbors[current_lane]['sucs'])
    neighbor_lanes = paraller_lanes(current_lane)
    neighbor_num = len(neighbor_lanes)
    # split-merge-branch
    if neighbor_num >= 2:
        label = 'split-merge-branch'
        return label
    
    # along
    if neighbor_num == 0:
        if pre_num <= 1 and suc_num <= 1:
            label = 'along'
    # merge-main, merge-branch
    if neighbor_num > 0:
        if suc_num == 1:
            suc = dic_neighbors[current_lane]['sucs'][0]
            if len(dic_neighbors[suc]['pres']) > 1:
                dic = {}
                lanes = neighbor_lanes + [current_lane]
                for i in lanes:
                    dic[i] = lane_degree_diff(i,suc)
                dic_sort = {k: v for k, v in sorted(dic.items(), key=lambda item: item[1])}
                main_lane = list(dic_sort.keys())[0]
                if main_lane == current_lane:
                    label = 'merge-main'
                else:
                    label = 'merge-branch'
            else:
                pass
        else:
            pass  
    # merge
    if neighbor_num == 0:
        if pre_num > 1 and suc_num <= 1:
            label = 'merge'
    # split-main, split-branch
    if neighbor_num > 0:
        if pre_num == 1:
            pre = dic_neighbors[current_lane]['pres'][0]
            if len(dic_neighbors[pre]['sucs']) > 1:
                dic = {}
                lanes = neighbor_lanes + [current_lane]
                for i in lanes:
                    dic[i] = lane_degree_diff(pre,i)
                dic_sort = {k: v for k, v in sorted(dic.items(), key=lambda item: item[1])}
                main_lane = list(dic_sort.keys())[0]
                if main_lane == current_lane:
                    label = 'split-main'
                else:
                    label = 'split-branch'
            else:
                pass
        else:
            pass 
    # split
    if neighbor_num == 0:
        if pre_num <= 1 and suc_num > 1:
            label = 'split'
    # split-merge
    if neighbor_num == 0:
        if pre_num > 1 and suc_num > 1:
            label = 'split-merge'

    return label 


def start_to_end_alane(start_lane):
    # global start_lanes,end_lanes
    lane_list_in_alane = []
    current_lane = start_lane
    while True:
        next_lane = check_next_lane(current_lane)
        label = check_lane_label(current_lane)
        is_end = check_is_end(current_lane)
        print(current_lane,next_lane,label,is_end)
        if is_end:
            lane_list_in_alane.append(current_lane)
            used_lane_list.append(current_lane)
            start_lanes.remove(start_lane)
            break
        else:
            if label == 'along':
                lane_list_in_alane.append(current_lane)
                used_lane_list.append(current_lane)
                current_lane = next_lane
            if label == 'merge-main' or label == 'merge':
                lane_list_in_alane.append(current_lane)
                used_lane_list.append(current_lane)
                current_lane = next_lane
            if label == 'merge-branch':
                lane_list_in_alane.append(current_lane)
                used_lane_list.append(current_lane)
                start_lanes.remove(start_lane)
                break
            if label == 'split-main':
                neighbors = paraller_lanes(current_lane)
                for i in neighbors:
                    if i not in start_lanes:
                         start_lanes.append(i)
                # print(start_lanes)
                lane_list_in_alane.append(current_lane)
                used_lane_list.append(current_lane)
                current_lane = next_lane
            if label == 'split-branch':
                lane_list_in_alane.append(current_lane)
                used_lane_list.append(current_lane)
                current_lane = next_lane
            if label == 'split':
                sucs = dic_neighbors[current_lane]['sucs']
                for i in sucs:
                    if i != next_lane:
                        if i not in start_lanes:
                            start_lanes.append(i)
                # print(start_lanes)
                lane_list_in_alane.append(current_lane)
                used_lane_list.append(current_lane)
                current_lane = next_lane
            if label == 'split-merge':
                print(f"lane {current_lane} is both split and merge.")
                sucs = dic_neighbors[current_lane]['sucs']
                for i in sucs:
                    if i != next_lane:
                        if i not in start_lanes:
                            start_lanes.append(i)
                lane_list_in_alane.append(current_lane)
                used_lane_list.append(current_lane)
                current_lane = next_lane
            
            if label == 'split-merge-branch':
                end_lanes.append(current_lane)
                next_lane = check_next_lane(current_lane)
                start_lanes.append(next_lane)
                # return lane_list_in_alane
                

    return lane_list_in_alane       





df_lane = pg_map.get('mod_lane')
# 鄂尔多斯二期暂时放开非机动车道处理，用于可视化路沿
# df_lane = df_lane.drop(df_lane[df_lane.lane_type.isin(['2'])].index)
df_node = pg_from.get('rns_lane_node')
df_link = pg_map.get('rns_link')
df_junc_points = pg_map.get('rns_junction_point')


DG, dic_neighbors = construct_lane_net()
start_lanes,end_lanes = start_end_lane()
used_lane_list = []


# start_lanes = ['32201',]
# end_lanes = ['269',]

dic_alane = {}

new_id = 1
while len(start_lanes) > 0:
    for start_lane in start_lanes:
        print(start_lane)
        if start_lane in used_lane_list:
            start_lanes.remove(start_lane)
        else:
            pre_lanes = dic_neighbors[start_lane]['pres']
            for i in pre_lanes:
                inters_id = df_lane[df_lane.lane_id==i]['inters_id'].values[0]
                if not pd.isna(inters_id): # 路口内lane, 单独作为一个alane
                    dic_alane[new_id] = [i]
                    new_id+=1
            if start_lane in end_lanes: # 既是start lane, 又是end lane
                dic_alane[new_id] = [start_lane]
                start_lanes.remove(start_lane)
                new_id+=1
            else:
                l = start_to_end_alane(start_lane)
                dic_alane[new_id] = l
                new_id+=1


l = []
for alane_id in dic_alane:
    seq = 1
    for lane_id in dic_alane[alane_id]:
        dic = {'lane_id':lane_id, 'lane_id_new': alane_id, 'lane_seq_new': seq}
        l.append(dic)


df=pd.DataFrame(l)
df.to_excel(f"{path}/offline_process/02-perception_map/alane/stich_lane.xlsx")









