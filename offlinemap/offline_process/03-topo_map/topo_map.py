# -*- coding: UTF-8 -*-
"""
基于topo_graph.proto定义的规格，使用lane_add_virtual_change生成topo_graph.pb.txt
"""

import os
import sys
import time
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(path)
sys.path.append(path)
from lib.config import pg_map
from shapely import wkt, wkb
import topo_graph_pb2 as pb2
import math
import networkx as nx

'''
UNKNOWN_TYPE = 0;
FORWARD = 1;
LANE_CHANGE_RIGHT = 2;
LANE_CHANGE_LEFT = 3;
JUNC_TRUN_RIGHT = 4;
JUNC_TURN_LEFT = 5;
JUNC_FORWARD = 6;
JUNC_U_TURN = 7;
LANE_LFET_MERGE = 8; // 向左侧合流
LANE_RIGHT_MERGE = 9; // 向右侧合流
LANE_LFET_SPLIT = 10; // 向左侧合流
LANE_RIGHT_SPLIT = 11; // 向右侧合流
'''

def neighbor_lanes(lane_id):
    left_lane = None
    right_lane = None
    lane_row = df_lane[df_lane.lane_id==lane_id].iloc[0]
    link_id = lane_row['link_id']
    lane_rows =  df_lane[df_lane.link_id==link_id]
    max_seq = lane_rows['lane_seq'].max()
    # 右侧lane
    if lane_row['lane_seq'] < max_seq:
        right_seq = lane_row['lane_seq']+1
        right_lane_filtered = lane_rows[lane_rows.lane_seq==right_seq]
        if not right_lane_filtered.empty:
            right_lane_row = right_lane_filtered.iloc[0]
            if f"{lane_id}_{right_lane_row['lane_id']}" in change_lane_list:
                right_lane = right_lane_row['lane_id']
    
    # 左侧lane
    if lane_row['lane_seq'] > 1:
        left_seq = lane_row['lane_seq']-1
        left_lane_filtered = lane_rows[lane_rows.lane_seq==left_seq]
        if not left_lane_filtered.empty:
            left_lane_row = left_lane_filtered.iloc[0]
            if f"{lane_id}_{left_lane_row['lane_id']}" in change_lane_list:
                left_lane = left_lane_row['lane_id']

    return left_lane,right_lane


def check_change(from_lane,to_lane):
    if f"{from_lane}_{to_lane}" in change_lane_list:
        return True
    else:
        return False


def lane_degree_diff(pre,suc):
    def line_degree(x1,y1,x2,y2):
        dx = x2 - x1
        dy = y2 - y1
        # 计算角度（弧度值）
        angle_rad = math.atan2(dy, dx)
        # 将弧度转换为角度
        angle_deg = math.degrees(angle_rad)
        # 转换为正值（0到360度）
        angle_deg = (90 - angle_deg) % 360

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


def check_conn_type(from_lane,to_lane):
    from_inters_id = df_lane[df_lane.lane_id==from_lane]['inters_id'].values[0]
    to_inters_id = df_lane[df_lane.lane_id==to_lane]['inters_id'].values[0]
    from_conn_type = df_lane[df_lane.lane_id==from_lane]['conn_type'].values[0]
    to_conn_type = df_lane[df_lane.lane_id==to_lane]['conn_type'].values[0]
    
    conn_type = 0
    if to_inters_id is None:
        # 增加合流的判断
        row = df_feature_point[(df_feature_point.suc_lanes==to_lane) | (df_feature_point.pre_lanes==from_lane)]
        if row.empty:
            conn_type = 1
        else:
            feature_type = row['label'].values[0]
            if feature_type == 'merge':
                pre_lanes = row['pre_lanes'].values[0].split(',')
                if len(pre_lanes) == 2:
                    pre_lanes.remove(from_lane)
                    other_lane = pre_lanes[0]
                    other_lane_diff = lane_degree_diff(other_lane,to_lane)
                    from_lane_diff = lane_degree_diff(from_lane,to_lane)
                    if from_lane_diff > other_lane_diff: # other lane 是FORWARD
                        other_lane_seq = df_lane[df_lane.lane_id==other_lane]['lane_seq'].values[0]
                        from_lane_seq = df_lane[df_lane.lane_id==from_lane]['lane_seq'].values[0]
                        if other_lane_seq < from_lane_seq:  # other lane在左边
                            conn_type = 8
                        if other_lane_seq > from_lane_seq:  # from lane在左边
                            conn_type = 9
                    else:
                        conn_type = 1

                    # 宝坻路线定制津围线合流车道
                    if to_lane == '2044' and from_lane == '2040':
                        conn_type = 1
                    if to_lane == '2044' and from_lane == '2041':
                        conn_type = 8
                else:
                    print('lane merge more than 2 lane, to lane id is ' + to_lane)
                    conn_type = 1
            else:
                suc_lanes = row['suc_lanes'].values[0].split(',')
                if len(suc_lanes) == 2:
                    suc_lanes.remove(to_lane)
                    other_lane = suc_lanes[0]
                    other_lane_diff = lane_degree_diff(from_lane,other_lane)
                    to_lane_diff = lane_degree_diff(from_lane,to_lane)
                    if to_lane_diff > other_lane_diff: # other lane 是FORWARD
                        other_lane_seq = df_lane[df_lane.lane_id==other_lane]['lane_seq'].values[0]
                        to_lane_seq = df_lane[df_lane.lane_id==to_lane]['lane_seq'].values[0]
                        if other_lane_seq < to_lane_seq:  # other lane在左边
                            conn_type = 11
                        if other_lane_seq > to_lane_seq:  # to lane在左边
                            conn_type = 10
                    else:
                        conn_type = 1
                else:
                    print('lane split more than 2 lane, from lane id is ' + from_lane)
                    conn_type = 1
    else:
        if to_conn_type == 2:
            conn_type = 5
        if to_conn_type == 3:
            conn_type = 4
        if to_conn_type == 4:
            conn_type = 7
        if to_conn_type == 1:
            conn_type = 6
    
    return conn_type
    
df_feature_point = pg_map.get('lane_feature_point')
df_lane = pg_map.get('mod_lane')
df_change_lane = pg_map.get('lane_add_virtual_change')
pb = pb2.TopoGraph()
change_lane_list = df_change_lane['lane_id'].tolist()


for index,row in df_lane.iterrows():
    pair = pb.map_node_edge.add()
    lane_id = row['lane_id']
    edge_id = int(row['enode_id'])
    print(lane_id)
    geom = wkb.loads(df_lane[df_lane.lane_id==lane_id]['utm'].values[0],hex=True)
    length = float(row['length'])
    pres = row['pre_lanes'].split(':')if row['pre_lanes'] is not None else []
    sucs = row['suc_lanes'].split(':') if row['suc_lanes'] is not None else []
    if int(lane_id) == 100058:
        left_lane,right_lane = None, None
    else:
        left_lane,right_lane = neighbor_lanes(lane_id)
    topo_node_pb = pair.node
    topo_node_pb.lane_id = int(lane_id)
    topo_node_pb.length = length
    mid_pnt = geom.interpolate(0.5,normalized=True)
    topo_node_pb.anchor_point_x = mid_pnt.x
    topo_node_pb.anchor_point_y = mid_pnt.y
    topo_node_pb.predecessor_id.extend([int(x) for x in pres])
    topo_node_pb.successor_id.extend([int(x) for x in sucs])
    if left_lane is not None:
        topo_node_pb.left_neighbor_forward_lane_id.extend([int(left_lane)])
        topo_edge_pb = pair.suc_edges.add()
        topo_edge_pb.edge_id = edge_id
        topo_edge_pb.from_lane_id = int(lane_id)
        topo_edge_pb.to_lane_id = int(left_lane)
        topo_edge_pb.conn_type = 3
        edge_id += 1
        if check_change(left_lane,lane_id):
            topo_edge_pb = pair.pre_edges.add()
            topo_edge_pb.edge_id = edge_id
            topo_edge_pb.from_lane_id = int(left_lane)
            topo_edge_pb.to_lane_id = int(lane_id)
            topo_edge_pb.conn_type = 2
            edge_id += 1

    if right_lane is not None:
        topo_node_pb.right_neighbor_forward_lane_id.extend([int(right_lane)])
        topo_edge_pb = pair.suc_edges.add()
        topo_edge_pb.edge_id = edge_id
        topo_edge_pb.from_lane_id = int(lane_id)
        topo_edge_pb.to_lane_id = int(right_lane)
        topo_edge_pb.conn_type = 2
        edge_id += 1
        if check_change(right_lane,lane_id):
            topo_edge_pb = pair.pre_edges.add()
            topo_edge_pb.edge_id = edge_id
            topo_edge_pb.from_lane_id = int(right_lane)
            topo_edge_pb.to_lane_id = int(lane_id)
            topo_edge_pb.conn_type = 3
            edge_id += 1

    edge_id = 1
    # pre
    for from_lane_id in pres:
        conn_type = check_conn_type(from_lane_id,lane_id)
        topo_edge_pb = pair.pre_edges.add()
        topo_edge_pb.edge_id = edge_id
        topo_edge_pb.from_lane_id = int(from_lane_id)
        topo_edge_pb.to_lane_id = int(lane_id)
        topo_edge_pb.conn_type = conn_type
        edge_id += 1

    # suc
    for to_lane_id in sucs:
        conn_type = check_conn_type(lane_id,to_lane_id)
        topo_edge_pb = pair.suc_edges.add()
        topo_edge_pb.edge_id = edge_id
        topo_edge_pb.from_lane_id = int(lane_id)
        topo_edge_pb.to_lane_id = int(to_lane_id)
        topo_edge_pb.conn_type = conn_type
        edge_id += 1

    
from google.protobuf import text_format
def save_pb_to_txt(pb_object, filename):
    with open(filename, 'w') as f:
        f.write(text_format.MessageToString(pb_object))


save_pb_to_txt(pb,f"{path}/data/topo_graph.pb.txt")









