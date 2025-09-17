# -*- coding: UTF-8 -*-
"""
生成CL2 MAP依赖的全部pb.txt文件，以及
alane_data.json：感知地图alane的左右车道中心线关系，用于判断平行车道
alane_direction.json：感知地图中不同路口下不同方位包含的alane
lane_direction.json：相对地图中不同路口下不同方位包含的lane
link_data.json：高精度地图中的link的wkb格式的geometry
"""

import os
import sys
import time
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path)
from lib.config import pg_map,ctf
import pandas as pd
import relative_map_pb2 as pb2
import perception_map_pb2 as pm_pb2
from google.protobuf import text_format
import json
from shapely import wkt
from shapely.geometry import Point

x_correct = 0.3
y_correct = -0.15


def lanes_pkl():
    df_junc = pg_map.get('rns_junction_polygon')
    dic_junc = {}
    for index,row in df_junc.iterrows():
        inters_id = int(row['inters_id'])
        inters_code = int(row['inters_code'])
        dic_junc[inters_id] = inters_code
    total_pb = pb2.RelativeMap()
    df = pg_map.get('rm_lanes')
    df_lane = pg_map.get('mod_lane')
    total_list = []
    for lane_id, group in df.groupby('id'):
        print(lane_id)
        lane = pb2.Lane()
        row = group.iloc[0]
        lane.id = int(lane_id)
        link_id = int(df_lane[df_lane.lane_id==lane_id]['link_id'].values[0])
        lane.road_id = link_id
        lane.sequence = int(row['sequence'])
        lane.sequence_right = int(row['sequence_right'])
        lane.length = float(row['length'])
        # lane.speed_limit = float(row['speed_limit'])
        if not pd.isna(row['junction_id']): 
            if '1' in row['turn']:
                lane.speed_limit = 50/3.6
            else: 
                lane.speed_limit = 25/3.6 
        else:
            lane.speed_limit = 50/3.6  # 0417降低限速 60—>40
        if row['predecessor_ids'] is not None:
            lane.predecessor_id.extend([int(x) for x in row['predecessor_ids'].split(':')])
        if row['successor_ids'] is not None:
            lane.successor_id.extend([int(x) for x in row['successor_ids'].split(':')])
        if not pd.isna(row['left_neighbor_forward_lane_id']):
            lane.left_neighbor_forward_lane_id = int(row['left_neighbor_forward_lane_id'])
        if not pd.isna(row['right_neighbor_forward_lane_id']):
            lane.right_neighbor_forward_lane_id = int(row['right_neighbor_forward_lane_id'])
        if not pd.isna(row['left_neighbor_reverse_lane_id']):
            lane.left_neighbor_reverse_lane_id = int(row['left_neighbor_reverse_lane_id'])
        if not pd.isna(row['right_neighbor_reverse_lane_id']):
            lane.left_neighbor_reverse_lane_id = int(row['right_neighbor_reverse_lane_id'])
        if row['left_boundary_id'] is not None:
            lane.left_boundary_id = int(row['left_boundary_id'])
            lane.right_boundary_id = int(row['right_boundary_id'])
        # TODO: 缺少curb
        lane.type = int(row['type'])
        lane.turn.extend([int(x) for x in row['turn'].split(':')])
        lane.is_virtual = int(row['is_virtual'])
        if not pd.isna(row['junction_id']):  # 这里的junction id  是inters id
            lane.junction_id = dic_junc[int(row['junction_id'])]
        if not pd.isna(row['lane_arrow_id']):
            lane.lane_arrow_id.extend([int(x) for x in row['lane_arrow_id'].split(':')])
        if not pd.isna(row['stop_line_id']):
            lane.stop_line_id = int(row['stop_line_id'])
        if not pd.isna(row['cross_walk_id']):
            lane.cross_walk_id = int(row['cross_walk_id'])
        if not pd.isna(row['light_panel_id']):
            lane.light_panel_id = int(row['light_panel_id'])
        if not pd.isna(row['traffic_light_id']):
            lane.traffic_light_id = int(row['traffic_light_id'])
        if not pd.isna(row['traffic_sign_id']):
            lane.traffic_sign_id.extend([int(x) for x in row['traffic_sign_id'].split(':')])

        l = []
        for index,row in group.iterrows():
            pnc = pb2.PNCPoint()
            pnc.heading = float(row['heading'])
            pnc.curvature = float(row['curvature'])
            pnc.width = float(row['width'])
            s_offset = float(row['s_offset'])
            pnc.s_offset = s_offset
            xy = row['point'].split(',')
            pnc.point.x = float(xy[0])
            pnc.point.y = float(xy[1])
            l.append(pnc)
        lane.points.extend(l)
        total_list.append(lane)
    total_pb.lanes.extend(total_list)

    with open(f"{out_path}/lanes.pb.txt", 'wb') as f:
       f.write(total_pb.SerializeToString())


def lane_boundaries_pkl():
    df = pg_map.get('rm_lane_boundarys')
    total_list = []
    total_pb = pb2.RelativeMap()
    for mark_id, group in df.groupby('id'):
        mark = pb2.LaneBoundary()
        row = group.iloc[0]
        mark.id = mark_id
        if not pd.isna(row['types']):
            mark.types.extend([int(x) for x in row['types'].split(':')])
        if not pd.isna(row['colors']):
            mark.colors.extend([int(x) for x in row['colors'].split(':')])
        mark.is_virtual = int(row['is_virtual'])
        if not pd.isna(row['left_lane_id']):
            mark.left_lane_id = int(row['left_lane_id'])
        if not pd.isna(row['right_lane_id']):
            mark.right_lane_id = int(row['right_lane_id'])
        
        l = []
        for index,row in group.iterrows():
            pnc = pb2.PNCPoint()
            pnc.heading = float(row['heading'])
            pnc.curvature = float(row['curvature'])
            s_offset = float(row['s_offset'])
            pnc.s_offset = s_offset
            xy = row['point'].split(',')
            pnc.point.x = float(xy[0])
            pnc.point.y = float(xy[1])
            l.append(pnc)
        mark.points.extend(l)
        total_list.append(mark)
    total_pb.lane_boundaries.extend(total_list)
    with open(f"{out_path}/lane_boundaries.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


def junctions_pkl():
    df = pg_map.get('rm_junctions')
    total_list = []
    total_pb = pb2.RelativeMap()
    for index,row in df.iterrows():
        junc_id = row['id']
        junction = pb2.Junction()
        junction.id = junc_id
        junction.type = row['type']
        if row['stop_line_ids'] is not None:
            junction.stop_line_ids.extend([int(x) for x in row['stop_line_ids'].split(':')])
        if row['cross_walk_ids'] is not None: 
            junction.cross_walk_ids.extend([int(x) for x in row['cross_walk_ids'].split(':')])
        if row['traffic_light_ids'] is not None:
            junction.traffic_light_ids.extend([int(x) for x in row['traffic_light_ids'].split(':')])
        for i in row['junction_polygon'].split(':'):
            xy = i.split(',')
            pnt = junction.junction_polygon.add()
            pnt.x = float(xy[0])
            pnt.y = float(xy[1])
        total_list.append(junction)
    
    total_pb.junctions.extend(total_list)
    with open(f"{out_path}/junctions.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


def stop_lines_pkl():
    df=pg_map.get('rm_stop_lines')
    total_list = []
    total_pb = pb2.RelativeMap()
    for index,row in df.iterrows():
        sl_id = row['id']
        stop_line = pb2.StopLine()
        stop_line.id = sl_id
        stop_line.type = int(row['type'])
        stop_line.lane_ids.extend([int(x) for x in row['lane_ids'].split(':')])
        stop_line.is_virtual = int(row['is_virtual'])
        if not pd.isna(row['junction_id']): 
            stop_line.junction_id = int(row['junction_id'])
        if not pd.isna(row['traffic_light_id']): 
            stop_line.traffic_light_id = int(row['traffic_light_id'])
        for i in row['points'].split(':'):
            xy = i.split(',')
            pnt = stop_line.points.add()
            pnt.x = float(xy[0])
            pnt.y = float(xy[1])
        total_list.append(stop_line)
    
    total_pb.stop_lines.extend(total_list)
    with open(f"{out_path}/stop_lines.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


def cross_walks_pkl():
    df=pg_map.get('rm_cross_walks')
    total_list = []
    total_pb = pb2.RelativeMap()
    for index,row in df.iterrows():
        cwalk_id = int(row['id'])
        cwalk = pb2.CrossWalk()
        cwalk.id = cwalk_id
        cwalk.lane_ids.extend([int(x) for x in row['lane_ids'].split(':')])
        if not pd.isna(row['junction_id']): 
            cwalk.junction_id = int(row['junction_id'])
        cwalk.walk_direction = float(row['walk_direction'])
        # TODO: 非机动车信号灯
        for i in row['points'].split(':'):
            xy = i.split(',')
            pnt = cwalk.points.add()
            pnt.x = float(xy[0])
            pnt.y = float(xy[1])
        
        total_list.append(cwalk)

    total_pb.cross_walks.extend(total_list)
    with open(f"{out_path}/cross_walks.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


def lane_arrows_pkl():
    df=pg_map.get('rm_lane_arrows')
    total_list = []
    total_pb = pb2.RelativeMap()
    for index,row in df.iterrows():
        arrow_id = int(row['id'])
        arrow = pb2.LaneArrow()
        arrow.id = arrow_id
        arrow.type = int(row['type'])
        arrow.heading = float(row['heading'])
        arrow.lane_id = int(row['lane_id'])
        xy = row['point'].split(',')
        arrow.point.x = float(xy[0])
        arrow.point.y = float(xy[1])
        total_list.append(arrow)
    
    total_pb.lane_arrows.extend(total_list)
    with open(f"{out_path}/lane_arrows.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


def traffic_signs_pkl():
    df=pg_map.get('rm_traffic_signs')
    total_list = []
    total_pb = pb2.RelativeMap()
    for index,row in df.iterrows():
        sign_id = int(row['id'])
        sign = pb2.TrafficSign()
        sign.id=sign_id
        sign.sign_type = int(row['sign_type'])
        sign.is_virtual = int(row['is_virtual'])
        # TODO: sign_value
        value = row['sign_value']
        sign.sign_value = float(value)
        sign.road_id = int(row['road_id'])
        sign.lane_id.extend([int(x) for x in row['lane_ids'].split(':')])
        xy = row['point'].split(',')
        sign.point.x = float(xy[0])
        sign.point.y = float(xy[1])

        total_list.append(sign)

    total_pb.traffic_signs.extend(total_list)
    with open(f"{out_path}/traffic_signs.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


# TODO: 根据交互协议修改    
def traffic_lights_pkl():
    df=pg_map.get('rm_light_panels')
    total_list = []
    total_pb = pb2.RelativeMap()
    for light_id, group in df.groupby('traffic_light_id'):
        info = group.iloc[0]
        traffic_light = pb2.TrafficLight()
        traffic_light.id = int(light_id)
        traffic_light.junction_id = int(info['junction_id'])
        
        stop_line_ids = []
        # TODO: cross_walk_ids
        l = []
        for index,row in group.iterrows():
            stop_line_ids += row['stop_line_ids'].split(':')
            panel = pb2.LightPanel()
            panel_id = int(row['id'])
            panel.id = panel_id
            panel.type.extend([int(x) for x in row['type'].split(':')])
            panel.lane_ids.extend([int(x) for x in row['lane_ids'].split(':')])
            panel.heading = float(row['heading'])
            panel.point.x = float(row['point'].split(',')[0])
            panel.point.y = float(row['point'].split(',')[1])
            l.append(panel)

        traffic_light.stop_line_ids.extend([int(x) for x in set(stop_line_ids)])
        traffic_light.light_panels.extend(l)

        total_list.append(traffic_light)

    total_pb.traffic_lights.extend(total_list)
    with open(f"{out_path}/traffic_lights.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


# 感知地图
def pm_lanes_pkl():
    def alane_is_virtual(lane_ids):
        if ':' in lane_ids:
            return 0
        else:
            vt_type = df_lane[df_lane.lane_id==lane_ids]['vt_type'].values[0]
            if vt_type == 0:
                return 0
            else:
                return 1

    df = pg_map.get('pm_all_features')
    df_alane = pg_map.get('alane')
    df_lane = pg_map.get('mod_lane')
    for alane_id, group in df_alane.groupby('alane_id'):
        print(alane_id)

    total_list = []
    total_pb = pm_pb2.PerceptionMap()
    for alane_id, group in df.groupby('alane_id'):
        # print(alane_id)
        lane = pm_pb2.Lane()
        # 处理alane_id可能是浮点数字符串的情况
        try:
            alane_id_int = int(float(alane_id))
        except (ValueError, TypeError):
            print(f"Warning: Invalid alane_id format '{alane_id}', skipping...")
            continue
        matched_rows = df_alane[df_alane.alane_id==alane_id_int]
        if len(matched_rows) == 0:
            print(f"Warning: alane_id {alane_id} not found in alane table, skipping...")
            continue
        alane_row = matched_rows.iloc[0]
        # alane_row = df_alane[df_alane.alane_id==alane_id].iloc[0]
        lane_ids = alane_row['lane_ids']
        lane.lane_id = alane_id_int
        lane.lane_type = 1  # TODO: 先暂定都是机动车道
        lane.is_virtual = alane_is_virtual(lane_ids)
        pres = alane_row['pres']
        l = []
        if pres != '':
            for i in pres.split(','):
                pre = int(i.split(':')[0])
                l.append(pre)
        lane.predecessor_lane_id.extend(l)
        
        sucs = alane_row['sucs']
        l = []
        if sucs != '':
            for i in sucs.split(','):
                suc = int(i.split(':')[0])
                l.append(suc)
        lane.successor_lane_id.extend(l)
        
        left_lines = alane_row['left_line']
        if left_lines:
            for left_line in left_lines.split(','):
                lane.related_left_line_id.append(int(left_line))

        right_lines = alane_row['right_line']
        if right_lines:
            for right_line in right_lines.split(','):
                lane.related_right_line_id.append(int(right_line))
        
        # if int(alane_id) == 365:
        #     lane.ClearField('related_left_line_id')
        #     lane.related_left_line_id.append(2019)
        #     lane.ClearField('related_right_line_id')
        #     lane.related_right_line_id.append(2017)

        arrows = group[group.type=='lane_arrow']
        arrows = arrows.sort_values('dist_on_alane')

        # if int(alane_id) == 256:
        #     lane.related_lane_arrow_id.append(30)
        # else:
        #     for index,row in arrows.iterrows():
        #         arrow_id = int(row['id'])
        #         lane.related_lane_arrow_id.append(arrow_id)
        for index,row in arrows.iterrows():
                arrow_id = int(row['id'])
                lane.related_lane_arrow_id.append(arrow_id)
        

        stop_lines = group[group.type=='stop_line']
        stop_lines = stop_lines.sort_values('dist_on_alane')
        for index,row in stop_lines.iterrows():
            sl_id = int(row['id'])
            lane.related_stop_line_id.append(sl_id)

        cross_walks = group[group.type=='cross_walk']
        cross_walks = cross_walks.sort_values('dist_on_alane')
        for index,row in cross_walks.iterrows():
            cw_id = int(row['id'])
            lane.related_cross_walk_id.append(cw_id)

        traffic_signs = group[group.type=='traffic_sign']
        traffic_signs = traffic_signs.sort_values('dist_on_alane')
        for index,row in traffic_signs.iterrows():
            sign_id = int(row['id'])
            lane.related_traffic_sign_id.append(sign_id)

        junction_lights = group[group.type=='junction_light']
        junction_lights = junction_lights.sort_values('dist_on_alane')
        for index,row in junction_lights.iterrows():
            light_id = int(row['id'])
            lane.related_junction_light_id.append(light_id)
        total_list.append(lane)
    
    total_pb.lane_sequences.extend(total_list)
    with open(f"{out_path}/pm_lanes.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())
       

    
def pm_lane_lines_pkl():
    df = pg_map.get('pm_lane_lines')
    total_list = []
    total_pb = pm_pb2.PerceptionMap()
    
    for line_id,group in df.groupby('line_id'):
        lane_line = pm_pb2.LaneLine()
        group = group.sort_values('s_offset')
        side_list=group['side'].values[0].split(',')
        if len(side_list) == 1:
            related_lane_id = [int(side_list[0].split(':')[0])]
        else:
            related_lane_id = [int(side_list[1].split(':')[0]),int(side_list[0].split(':')[0])]
        lane_line.line_id = int(line_id)
        lane_line.related_lane_id.extend(related_lane_id)
        is_virtual = True if int(group['is_virtual'].max()) == 1 else False
        type_has_change = True if group['type_has_change'].values[0] == 1 else False
        lane_line.is_virtual = is_virtual
        lane_line.type_has_change = type_has_change
        list_features = group.drop(
            group[group['related_feature_point_id'] == 999].index)[
            'related_feature_point_id'].tolist()
        if len(list_features) != 0:
            l = []
            for i in list_features:
                if i not in l:
                    l.append(int(i))
            lane_line.related_feature_point_id.extend(l)
        
        l = []
        for index,row in group.iterrows():
            line_point = pm_pb2.LinePoint()
            line_point.point_position.point_x = row['x']
            line_point.point_position.point_y = row['y']
            line_point.line_type.extend([int(x) for x in row['line_type'].split(':')])
            line_point.point_heading = row['heading']
            line_point.s_offset = row['s_offset']
            l.append(line_point)
        
        lane_line.line_points.extend(l)
        total_list.append(lane_line)
    total_pb.lane_lines.extend(total_list)
    with open(f"{out_path}/pm_lane_lines.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


def pm_feature_point_pkl():
    df = pg_map.get('pm_feature_points')
    total_list = []
    total_pb = pm_pb2.PerceptionMap()

    for index,row in df.iterrows():
        feature_point = pm_pb2.FeaturePoint()
        feature_point.feature_point_id = int(row['feature_point_id'])
        feature_point.feature_type = int(row['feature_type'])
        feature_point.feature_position.point_x = row['x']
        feature_point.feature_position.point_y = row['y']

        total_list.append(feature_point)

    total_pb.feature_points.extend(total_list)
    with open(f"{out_path}/pm_feature_points.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


def pm_stop_line_pkl():
    def stop_line_junction_light_id(id):
        id = str(id)
        df = df_light[df_light.stop_line_id.str.contains(id)]
        for index,row in df.iterrows():
            sl_ids = row['stop_line_id']
            if id in sl_ids.split(':'):
                return row['junction_light_id']
        else:
            return None       


    df = pg_map.get('pm_stop_lines')
    df_light = pg_map.get('pm_junction_lights')
    total_list = []
    total_pb = pm_pb2.PerceptionMap()

    for index,row in df.iterrows():
        stop_line = pm_pb2.StopLine()
        id = int(row['stop_line_id'])
        stop_line.stop_line_id = id
        stop_line.stop_line_type = row['stop_line_type']
        stop_line.is_virtual = row['is_virtual']
        stop_line.related_lane_id.extend([int(x) for x in row['alane_ids'].split(':')])
        junc_id  = stop_line_junction_light_id(id)
        if junc_id is not None:
            stop_line.related_junction_light_id = stop_line_junction_light_id(id)
        points = row['line_points']
        for i in points.split(','):
            j = i.split(' ')
            point = stop_line.line_points.add()
            point.point_x = float(j[0])
            point.point_y = float(j[1])
    
        total_list.append(stop_line)
    
    total_pb.stop_lines.extend(total_list)
    with open(f"{out_path}/pm_stop_lines.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())

    
def pm_cross_walk_pkl():
    df=pg_map.get('pm_cross_walks')
    total_list = []
    total_pb = pm_pb2.PerceptionMap()

    for index, row in df.iterrows():
        cw_id = row['cross_walk_id']
        cross_walk = pm_pb2.CrossWalk()
        cross_walk.cross_walk_id = cw_id
        cross_walk.related_lane_id.extend([int(x) for x in row['alane_ids'].split(':')])
        polygon_points = row['polygon_point']
        for i in polygon_points.split(','):
            j = i.split(' ')
            point = cross_walk.polygon_points.add()
            point.point_x = float(j[0])
            point.point_y = float(j[1])
        total_list.append(cross_walk)
    
    total_pb.cross_walks.extend(total_list)
    with open(f"{out_path}/pm_cross_walks.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())

    
def pm_lane_arrow_pkl():
    df=pg_map.get('pm_lane_arrows')
    total_list = []
    total_pb = pm_pb2.PerceptionMap()

    for index,row in df.iterrows():
        arrow = pm_pb2.LaneArrow()
        id = int(row['lane_arrow_id'])
        arrow.lane_arrow_id = id
        arrow.arrow_position.point_x = row['x']
        arrow.arrow_position.point_y = row['y']
        arrow.arrow_type = int(row['arrow_type'])
        arrow.arrow_heading = row['arrow_heading']
        arrow.related_lane_id.extend([int(row['alane_id'])])

        total_list.append(arrow)
    
    total_pb.lane_arrows.extend(total_list)
    with open(f"{out_path}/pm_lane_arrows.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


def pm_junction_light_pkl():
    df=pg_map.get('pm_junction_lights')
    total_list = []
    total_pb = pm_pb2.PerceptionMap()
    
    for index,row in df.iterrows():
        light_id = row['junction_light_id']
        light = pm_pb2.JunctionLight()
        light.junction_light_id=light_id
        light.junction_has_light = 1
        light.light_is_virtual = 0
        polygon_points = row['junction_position']
        if polygon_points != '':
            for i in polygon_points.split(','):
                j = i.split(' ')
                point = light.junction_position.add()
                point.point_x = float(j[0])
                point.point_y = float(j[1])
        light.related_lane_id.extend([int(x) for x in row['alane_ids'].split(':')])
        # l = []
        # for index,row in group.iterrows():
        #     sl_ids = row['stop_line_id']
        #     for i in sl_ids.split(':'):
        #         i = int(i)
        #         if i not in l:
        #             l.append(i)
        light.related_stop_line_id.extend([int(x) for x in row['stop_line_id'].split(':')])

        # TODO: cross_walks
        total_list.append(light)

    total_pb.junction_lights.extend(total_list)
    with open(f"{out_path}/pm_junction_lights.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


def link_to_json():
    from shapely import wkb
    import json
    df_link = pg_map.get('rns_link')
    dic = {}
    for index,row in df_link.iterrows():
        id = int(row['link_id'])
        geometry = wkb.loads(row['utm'],hex=True).wkb
        dic[id] = geometry.hex()
    
    # 将字典转换为 JSON 格式并保存
    with open(f"{out_path}/link_data.json", "w") as f:
        json.dump(dic, f, indent=4)


def alane_to_json():
    from shapely import wkb
    import json
    df_alane = pg_map.get('alane')
    dic = {}
    for index,row in df_alane.iterrows():
        id = int(row['alane_id'])
        geometry=wkb.loads(row['utm'],hex=True).wkb
        left_alane = row['left_alane']
        right_alane = row['right_alane']
        lane_ids = row['lane_ids']
        left_alanes = []
        if left_alane != '':
            for i in left_alane.split(','):
                left_alanes.append({'id':int(i)})
        right_alanes = []
        if right_alane != '':
            for i in right_alane.split(','):
                right_alanes.append({'id':int(i)})
        
        dic[id] = {'lane_ids':lane_ids,'geom':geometry.hex(),'left_alane':left_alanes,'right_alane':right_alanes}
    with open(f"{out_path}/alane_data.json", "w") as f:
        json.dump(dic, f, indent=4)


def lane_direction_json():
    from shapely import wkb
    import json
    import numpy as np
    df_lane = pg_map.get('mod_lane')
    df_junc=pg_map.get('rm_light_panels')

    dic_result = {}
    for junction_id,group in df_junc.groupby('junction_id'):
        dic = {}
        for index,row in group.iterrows():
            lane_ids = row['lane_ids'].split(':')
            lane_id = lane_ids[0]
            lane_row = df_lane[df_lane.lane_id==lane_id].iloc[0]
            utm = wkb.loads(lane_row['utm'],hex=True)
            coords = list(utm.coords)
            p1 = coords[0]
            p2 = coords[-1]
            dy = p2[1]-p1[1]
            dx = p2[0]-p1[0]
            rad = np.arctan2(dy, dx)
            deg = np.degrees(rad)
            # 对应traffic light pb中的direction
            if 22.5 > deg >= -22.5:
                azimuth = 1 # 东
            if 67.5 > deg >= 22.5:
                azimuth = 5 # 东北
            if 112.5 > deg >= 67.5:
                azimuth = 4 # 北
            if 157.5 > deg >= 112.5:
                azimuth = 8 # 西北
            if 180 >= deg >= 157.5 or -157.5 > deg >= -180:
                azimuth = 2 # 西
            if -112.5 > deg >= -157.5:
                azimuth = 7 # 西南
            if -67.5 > deg >= -112.5:
                azimuth = 3 # 南
            if -22.5 > deg >= -67.5:
                azimuth = 6 # 东南
            if azimuth not in dic:
                dic[azimuth] = []
                for lane in lane_ids:
                    dic[azimuth].append({'lane_id':int(lane),'degree':deg})
            else:
                for lane in lane_ids:
                    dic[azimuth].append({'lane_id':int(lane),'degree':deg})
        dic_result[junction_id] = dic 
    with open(f"{out_path}/lane_direction.json", "w") as f:
        json.dump(dic_result, f, indent=4)


def alane_direction_json():
    from shapely import wkb
    import json
    import numpy as np
    df_alane = pg_map.get('alane')
    df_junc=pg_map.get('pm_junction_lights')

    dic_result = {}
    for junction_id,group in df_junc.groupby('junction_light_id'):
        dic = {}
        for index,row in group.iterrows():
            alane_ids = row['alane_ids'].split(':')
            alane_id = alane_ids[0]
            alane_row = df_alane[df_alane.alane_id==int(alane_id)].iloc[0]
            utm = wkb.loads(alane_row['utm'],hex=True)
            coords = list(utm.coords)
            p1 = coords[0]
            p2 = coords[-1]
            dy = p2[1]-p1[1]
            dx = p2[0]-p1[0]
            rad = np.arctan2(dy, dx)
            deg = np.degrees(rad)
            # 对应traffic light pb中的direction
            # if 22.5 > deg >= -22.5:
            #     azimuth = 1 # 东
            # if 67.5 > deg >= 22.5:
            #     azimuth = 5 # 东北
            # if 112.5 > deg >= 67.5:
            #     azimuth = 4 # 北
            # if 157.5 > deg >= 112.5:
            #     azimuth = 8 # 西北
            # if 180 >= deg >= 157.5 or -157.5 > deg >= -180:
            #     azimuth = 2 # 西
            # if -112.5 > deg >= -157.5:
            #     azimuth = 7 # 西南
            # if -67.5 > deg >= -112.5:
            #     azimuth = 3 # 南
            # if -22.5 > deg >= -67.5:
            #     azimuth = 6 # 东南
            if 45 > deg >= -45:
                azimuth = 1 # 东
            if 135 > deg >= 45:
                azimuth = 4 # 北
            if 180 >= deg >= 135 or -135 > deg >= -180:
                azimuth = 2 # 西
            if -45 > deg >= -135:
                azimuth = 3 # 南

            if azimuth not in dic:
                dic[azimuth] = []
                for lane in alane_ids:
                    dic[azimuth].append({'alane_id':int(lane),'degree':deg})
            else:
                for lane in alane_ids:
                    dic[azimuth].append({'alane_id':int(lane),'degree':deg})
        dic_result[junction_id] = dic 
    with open(f"{out_path}/alane_direction.json", "w") as f:
        json.dump(dic_result, f, indent=4)


def lanes_pkl_correct():
    df_junc = pg_map.get('rns_junction_polygon')
    dic_junc = {}
    for index,row in df_junc.iterrows():
        inters_id = int(row['inters_id'])
        inters_code = int(row['inters_code'])
        dic_junc[inters_id] = inters_code
    total_pb = pb2.RelativeMap()
    df = pg_map.get('rm_lanes')
    df_lane = pg_map.get('mod_lane')
    total_list = []
    for lane_id, group in df.groupby('id'):
        if lane_id in [583,560]:
            ads = 10
        lane = pb2.Lane()
        row = group.iloc[0]
        lane.id = int(lane_id)
        link_id = int(df_lane[df_lane.lane_id==lane_id]['link_id'].values[0])
        lane.road_id = link_id
        lane.sequence = int(row['sequence'])
        lane.length = float(row['length'])
        lane.speed_limit = float(row['speed_limit'])
        if row['predecessor_ids'] is not None:
            lane.predecessor_id.extend([int(x) for x in row['predecessor_ids'].split(':')])
        if row['successor_ids'] is not None:
            lane.successor_id.extend([int(x) for x in row['successor_ids'].split(':')])
        if not pd.isna(row['left_neighbor_forward_lane_id']):
            lane.left_neighbor_forward_lane_id = int(row['left_neighbor_forward_lane_id'])
        if not pd.isna(row['right_neighbor_forward_lane_id']):
            lane.right_neighbor_forward_lane_id = int(row['right_neighbor_forward_lane_id'])
        if not pd.isna(row['left_neighbor_reverse_lane_id']):
            lane.left_neighbor_reverse_lane_id = int(row['left_neighbor_reverse_lane_id'])
        if not pd.isna(row['right_neighbor_reverse_lane_id']):
            lane.left_neighbor_reverse_lane_id = int(row['right_neighbor_reverse_lane_id'])
        if row['left_boundary_id'] is not None:
            lane.left_boundary_id = int(row['left_boundary_id'])
            lane.right_boundary_id = int(row['right_boundary_id'])
        # TODO: 缺少curb
        lane.type = int(row['type'])
        lane.turn.extend([int(x) for x in row['turn'].split(':')])
        lane.is_virtual = int(row['is_virtual'])
        if not pd.isna(row['junction_id']):
            lane.junction_id = dic_junc[int(row['junction_id'])]
        if not pd.isna(row['lane_arrow_id']):
            lane.lane_arrow_id.extend([int(x) for x in row['lane_arrow_id'].split(':')])
        if not pd.isna(row['stop_line_id']):
            lane.stop_line_id = int(row['stop_line_id'])
        if not pd.isna(row['cross_walk_id']):
            lane.cross_walk_id = int(row['cross_walk_id'])
        if not pd.isna(row['light_panel_id']):
            lane.light_panel_id = int(row['light_panel_id'])
        if not pd.isna(row['traffic_light_id']):
            lane.traffic_light_id = int(row['traffic_light_id'])
        if not pd.isna(row['traffic_sign_id']):
            lane.traffic_sign_id.extend([int(x) for x in row['traffic_sign_id'].split(':')])

        l = []
        for index,row in group.iterrows():
            pnc = pb2.PNCPoint()
            pnc.heading = float(row['heading'])
            pnc.curvature = float(row['curvature'])
            pnc.width = float(row['width'])
            s_offset = float(row['s_offset'])
            pnc.s_offset = s_offset
            xy = row['point'].split(',')
            # 手动向右纠偏0.15m，向下0.1m
            pnc.point.x = float(xy[0])+x_correct
            pnc.point.y = float(xy[1])+y_correct
        lane.points.extend(l)
        total_list.append(lane)
    total_pb.lanes.extend(total_list)

    with open(f"{out_path}/lanes_correct.pb.txt", 'wb') as f:
       f.write(total_pb.SerializeToString())


def lane_boundaries_pkl_correct():
    df = pg_map.get('rm_lane_boundarys')
    total_list = []
    total_pb = pb2.RelativeMap()
    for mark_id, group in df.groupby('id'):
        mark = pb2.LaneBoundary()
        row = group.iloc[0]
        mark.id = mark_id
        if not pd.isna(row['types']):
            mark.types.extend([int(x) for x in row['types'].split(':')])
        if not pd.isna(row['colors']):
            mark.colors.extend([int(x) for x in row['colors'].split(':')])
        mark.is_virtual = int(row['is_virtual'])
        if not pd.isna(row['left_lane_id']):
            mark.left_lane_id = int(row['left_lane_id'])
        if not pd.isna(row['right_lane_id']):
            mark.right_lane_id = int(row['right_lane_id'])
        
        l = []
        for index,row in group.iterrows():
            pnc = pb2.PNCPoint()
            pnc.heading = float(row['heading'])
            pnc.curvature = float(row['curvature'])
            s_offset = float(row['s_offset'])
            pnc.s_offset = s_offset
            xy = row['point'].split(',')
            pnc.point.x = float(xy[0])+x_correct
            pnc.point.y = float(xy[1])+y_correct
            l.append(pnc)
        mark.points.extend(l)
        total_list.append(mark)
    total_pb.lane_boundaries.extend(total_list)
    with open(f"{out_path}/lane_boundaries_correct.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


def pm_lane_lines_pkl_correct():
    df = pg_map.get('smooth_lane_lines')
    total_list = []
    total_pb = pm_pb2.PerceptionMap()
    
    for line_id,group in df.groupby('line_id'):
        lane_line = pm_pb2.LaneLine()
        group = group.sort_values('s_offset')
        side_list=group['side'].values[0].split(',')
        if len(side_list) == 1:
            related_lane_id = [int(side_list[0].split(':')[0])]
        else:
            related_lane_id = [int(side_list[1].split(':')[0]),int(side_list[0].split(':')[0])]
        lane_line.line_id = int(line_id)
        lane_line.related_lane_id.extend(related_lane_id)
        is_virtual = True if int(group['is_virtual'].max()) == 1 else False
        type_has_change = True if group['type_has_change'].values[0] == 1 else False
        lane_line.is_virtual = is_virtual
        lane_line.type_has_change = type_has_change
        list_features = group.drop(
            group[group['related_feature_point_id'] == 999].index)[
            'related_feature_point_id'].tolist()
        if len(list_features) != 0:
            l = []
            for i in list_features:
                if i not in l:
                    l.append(int(i))
            lane_line.related_feature_point_id.extend(l)
        
        l = []
        for index,row in group.iterrows():
            line_point = pm_pb2.LinePoint()
            line_point.point_position.point_x = row['x']+x_correct
            line_point.point_position.point_y = row['y']+y_correct
            line_point.line_type.extend([int(x) for x in row['line_type'].split(':')])
            line_point.point_heading = row['heading']
            line_point.s_offset = row['s_offset']
            l.append(line_point)
        
        lane_line.line_points.extend(l)
        total_list.append(lane_line)
    total_pb.lane_lines.extend(total_list)
    with open(f"{out_path}/pm_lane_lines_correct.pb.txt", 'wb') as f:
        f.write(total_pb.SerializeToString())


if __name__ == '__main__':
    out_path = f"{path}/data/pb.txt"
    lanes_pkl()
    # lanes_pkl_correct()
    # lane_boundaries_pkl_correct()
    lane_boundaries_pkl()
    junctions_pkl()
    stop_lines_pkl()
    cross_walks_pkl()
    lane_arrows_pkl()
    traffic_signs_pkl()
    traffic_lights_pkl()

    pm_lanes_pkl()
    pm_lane_lines_pkl()
    # pm_lane_lines_pkl_correct()
    pm_feature_point_pkl()
    pm_stop_line_pkl()
    pm_cross_walk_pkl()
    pm_lane_arrow_pkl()
    pm_junction_light_pkl()

    link_to_json()
    alane_to_json()
    lane_direction_json()
    alane_direction_json()


