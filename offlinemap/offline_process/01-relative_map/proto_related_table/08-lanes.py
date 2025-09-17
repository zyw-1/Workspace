"""
按照relative map的pb协议，处理lane数据，生成新表rm_lanes，包含pb中需要的必须字段
"""

import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

sys.path.append(path)

import pandas as pd
import numpy as np
from shapely import wkt,wkb
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
import math
from lib.config import pg_map,ctf,srid


def lane_neighbors(lane_id,lane_seq,is_virtual):
    lane_row = df_lane[df_lane.lane_id==lane_id].iloc[0]
    link_id = lane_row['link_id']
    chg_flg = lane_row['chg_flg']
    link_lanes = df_lane[df_lane.link_id==link_id]
    max_seq = link_lanes['lane_seq'].astype(int).max()
    if max_seq >= lane_seq + 1:  # 判断是否有右侧lane
        right_lane = link_lanes[link_lanes.lane_seq==(lane_seq+1)]['lane_id'].values[0]
        right_label = 'forward'
    else:
        right_lane = None  # TODO: 不属于同一个link下的lane
        right_label = 'forward'
    if lane_seq == 1: # 最左侧车道，判断是否左侧对向lane
        if is_virtual == 1: # 虚拟车道不生成对向lane
            left_lane = None
            left_label = 'forward'
        else:
            utm = wkb.loads(row['utm'],hex=True)
            coords = list(utm.coords)
            x1 = coords[0][0]
            y1 = coords[0][1]
            x2 = coords[-1][0]
            y2 = coords[-1][1]
            midx = (x1+x2)/2
            midy = (y1+y2)/2
            k = abs((y2-y1) / (x2-x1))
            if k == 0:
                if y2 > y1:
                    line = LineString([(midx,midy),(midx-20)])
                else:
                    line = LineString([(midx,midy),(midx+20)])
            else:
                if x2>x1 and y2>y1:
                    x_label = -1
                    y_label = 1
                if x2>x1 and y2<y1:
                    x_label = 1
                    y_label = 1
                if x2<x1 and y2>y1:
                    x_label = -1
                    y_label = -1
                if x2<x1 and y2<y1:
                    x_label = 1
                    y_label = -1
                k = 1/k
                dx = 20 / math.sqrt(1 + k**2)
                dy = k*dx
                a1 = midx + dx * x_label
                b1 = midy + dy * y_label
                line = LineString([(x2, y2), (a1, b1)])
            sql = f"select a.lane_id,st_intersection(a.utm, b.utm) as pnt from mod_lane a,(select st_geomfromtext('{line.wkt}',{srid}) as utm) b where st_intersects(a.utm, b.utm) = true"
            data = pg_map.execute(sql,True)
            mid_pnt = Point(midx,midy)
            left_lane = None
            min_dis = 100
            left_label = 'reverse'
            for i in data:
                pnt = wkb.loads(i[1],hex=True)
                dis = pnt.distance(mid_pnt)
                if dis < min_dis and i[0] != lane_id:
                    min_dis = dis
                    left_lane = i[0]

    else:
        # 添加健壮性检查，防止IndexError
        left_lane_candidates = link_lanes[link_lanes.lane_seq==(lane_seq-1)]['lane_id'].values
        if len(left_lane_candidates) > 0:
            left_lane = left_lane_candidates[0]
            left_label = 'forward'
        else:
            left_lane = None
            left_label = 'forward'

    if left_lane is not None and right_lane is not None:
        right_neighbor_forward_lane_id = right_lane  # TODO: 按我的理解，不会出现对向右侧车道
        right_neighbor_reverse_lane_id = None
        if left_label == 'forward':
            left_neighbor_forward_lane_id = left_lane
            left_neighbor_reverse_lane_id = None
        else:
            left_neighbor_forward_lane_id = None
            left_neighbor_reverse_lane_id = left_lane

    if left_lane is None and right_lane is not None:
        right_neighbor_forward_lane_id = right_lane
        right_neighbor_reverse_lane_id = None
        left_neighbor_forward_lane_id = None
        left_neighbor_reverse_lane_id = None

    if left_lane is not None and right_lane is None:
        right_neighbor_forward_lane_id = None
        right_neighbor_reverse_lane_id = None
        if left_label == 'forward':
            left_neighbor_forward_lane_id = left_lane
            left_neighbor_reverse_lane_id = None
        else:
            left_neighbor_forward_lane_id = None
            left_neighbor_reverse_lane_id = left_lane

    if left_lane is None and right_lane is None:
        right_neighbor_forward_lane_id = None
        right_neighbor_reverse_lane_id = None
        left_neighbor_forward_lane_id = None
        left_neighbor_reverse_lane_id = None

    if chg_flg == 0:
        left_neighbor_forward_lane_id = None
        right_neighbor_forward_lane_id = None
    if chg_flg == 1:
        right_neighbor_forward_lane_id = None
    if chg_flg == 2:
        left_neighbor_forward_lane_id = None
    return left_neighbor_forward_lane_id, right_neighbor_forward_lane_id, left_neighbor_reverse_lane_id, right_neighbor_reverse_lane_id


def check_lane_change(host,target):
    pass


def lane_turn(lane_id,conn_type,arrow_ids):
    # def lane_match_which_arrow(lane_id):
    #     df = df_arrow[df_arrow['lane_ids'].str.contains(lane_id)]
    #     l = []
    #     for index,row in df.iterrows():
    #         lane_ids = row['lane_ids'].split(':')
    #         if lane_id in lane_ids:
    #             arrow_id = row['id']
    #             l.append(arrow_id)
    #     return l
    '''
    UNKNOWN_TURN = 0; 
    STRAIGHT = 1; // 直行
    LEFT_TURN = 2; // 左转
    RIGHT_TURN = 3; // 右转
    U_TURN = 4; // 调头 
    LFET_MERGE = 5; // 左合流
    RIGHT_MERGE = 6; // 右合流
    SPLIT_LEFT = 7;  //向左分叉
    SPLIT_RIGHT = 8; //向右分叉
    '''
    dic = {1:4,2:2,3:1,4:3}
    if arrow_ids == '': # 没有关联到arrow
        for i in range(10):
            row = df_lane[df_lane.lane_id==lane_id].iloc[0]
            pre_lanes = row['pre_lanes'] if not pd.isna(row['pre_lanes']) else ':'
            if ':' in pre_lanes:
                lane_turn = str(conn_type)
                break
            else:
                if ':' in df_lane[df_lane.lane_id==pre_lanes]['suc_lanes'].values[0]:
                    lane_turn = str(conn_type)
                    break
                else:
                    arrow_id_list = df_arrow[df_arrow.lane_id==pre_lanes]['id'].tolist()
                    if len(arrow_id_list) == 0:
                        lane_id = pre_lanes
                        continue
                    else:
                        if df_lane[df_lane.lane_id==pre_lanes]['conn_type'].values[0] == 3:
                            lane_turn = str(conn_type)
                            break
                        else:
                            l = []
                            for arrow_id in arrow_id_list:
                                arrow_type = int(df_arrow[df_arrow.id==arrow_id]['type'].values[0])
                                if arrow_type == 5:
                                    l+=[2,4]
                                elif arrow_type == 6:
                                    l+=[1,4]
                                elif arrow_type == 8:
                                    l+=[1,2]
                                elif arrow_type == 9:
                                    l+=[3,2]
                                elif arrow_type == 11:
                                    l+=[1,2,3]
                                elif arrow_type == 12:
                                    l+=[1,3]
                                elif arrow_type == 14:
                                    l.append(5)
                                elif arrow_type == 15:
                                    l.append(6)
                                else:
                                    l.append(dic[arrow_type])
                            if len(l) == 1 and int(l[0]) == 0:
                                l.remove(0)
                            l = list(set(l))
                            l = [str(x) for x in l]
                            lane_turn = ':'.join(l)
                            break
        else:
            lane_turn = str(conn_type)
    else:
        l = []
        for arrow_id in arrow_ids.split(':'):
            arrow_type = int(df_arrow[df_arrow.id==arrow_id]['type'].values[0])
            if arrow_type == 5:
                l+=[2,4]
            elif arrow_type == 6:
                l+=[1,4]
            elif arrow_type == 8:
                l+=[1,2]
            elif arrow_type == 9:
                l+=[3,2]
            elif arrow_type == 11:
                l+=[1,2,3]
            elif arrow_type == 12:
                l+=[1,3]
            elif arrow_type == 14:
                l.append(5)
            elif arrow_type == 15:
                l.append(6)
            else:
                l.append(dic[arrow_type])
        if len(l) == 1 and int(l[0]) == 0:
            l.remove(0)
        l = list(set(l))
        l = [str(x) for x in l]
        lane_turn = ':'.join(l)

    return lane_turn


df_lane = pg_map.get('mod_lane')
df_scatters = pg_map.get('lane_scatters')
df_arrow = pg_map.get('rm_lane_arrows')
df_stopline = pg_map.get('rm_stop_lines')
df_cwalk = pg_map.get('rm_cross_walks')
df_panel = pg_map.get('rm_light_panels')
df_sign = pg_map.get('rm_traffic_signs')

l=[]
for index,row in df_lane.iterrows():
    lane_id = row['lane_id']
    print(lane_id)
    seq = int(row['lane_seq'])  # TODO: 先用默认的lane_seq
    link_id = row['link_id']
    max_seq = int(df_lane[df_lane.link_id==link_id]['lane_seq'].max())
    right_seq = max_seq+1 - seq
    length = float(row['length'])
    spd_lmt = round(float(row['spd_max'])/3.6,2) # TODO: 有为0的，暂不处理
    pre_lanes = row['pre_lanes']
    suc_lanes = row['suc_lanes']
    left_boundary = row['lmkg_id']
    right_boundary = row['rmkg_id']
    left_type = row['left_type']
    right_type = row['right_type']
    left_virtual = row['left_virtual']
    right_virtual = row['right_virtual']
    is_virtual = 0 if row['vt_type']==0 else 1
    # TODO: 左右curb暂不添加
    left_neighbor_forward_lane_id, right_neighbor_forward_lane_id, left_neighbor_reverse_lane_id, right_neighbor_reverse_lane_id = lane_neighbors(lane_id,seq,is_virtual)
        
    junction_id = row['inters_id']
    type = row['lane_type']
    conn_type = int(row['conn_type']) if not np.isnan(row['conn_type']) else 0 

    arrow_ids = ':'.join(df_arrow[df_arrow.lane_id==lane_id]['id'].astype(str).tolist())

    turn = lane_turn(lane_id,conn_type,arrow_ids)
    

    stop_line_id = None
    stopline_rows = df_stopline[df_stopline.lane_ids.str.contains(lane_id)]
    for index1,row1 in stopline_rows.iterrows():
        lane_ids = row1['lane_ids'].split(':')
        if lane_id in lane_ids:
            stop_line_id = row1['id']
            break

    cross_walk_id = None
    cross_walk_rows = df_cwalk[df_cwalk.lane_ids.str.contains(lane_id)]
    for index1,row1 in cross_walk_rows.iterrows():
        lane_ids = row1['lane_ids'].split(':')
        if lane_id in lane_ids:
            cross_walk_id = row1['id']
            break

    # traffic_sign_ids = ':'.join(df_sign[df_sign.lane_id==lane_id]['id'].astype(str).tolist())
    # TODO: 这里只填充车道级的交通标志
    traffic_sign_ids = ''
    
    light_panel_id = None
    traffic_light_id = None
    light_panel_rows = df_panel[df_panel.lane_ids.str.contains(lane_id)]
    for index1,row1 in light_panel_rows.iterrows():
        lane_ids = row1['lane_ids'].split(':')
        if lane_id in lane_ids:
            light_panel_id = row1['id']
            traffic_light_id = row1['traffic_light_id']
            break
    
    scatters = df_scatters[df_scatters.lane_id==lane_id]
    scatters = scatters.sort_values('s_offset')
    for index1,row1 in scatters.iterrows():
        heading = row1['heading']
        curvature = row1['curvature']
        s = row1['s_offset']
        width = row1['width']
        pnt = wkb.loads(row1['utm'])
        l.append({'id':lane_id,'sequence':seq,'sequence_right':right_seq,'length':length,'speed_limit':spd_lmt,'predecessor_ids':pre_lanes,'successor_ids':suc_lanes,
              'left_neighbor_forward_lane_id':left_neighbor_forward_lane_id,'right_neighbor_forward_lane_id':right_neighbor_forward_lane_id,
              'left_neighbor_reverse_lane_id':left_neighbor_reverse_lane_id,'right_neighbor_reverse_lane_id':right_neighbor_reverse_lane_id,
              'left_boundary_id':left_boundary,'right_boundary_id':right_boundary,'type':type,'turn':turn,'is_virtual':is_virtual,'junction_id':junction_id,
              'lane_arrow_id':arrow_ids,'stop_line_id':stop_line_id,'cross_walk_id':cross_walk_id,'light_panel_id':light_panel_id,
              'left_type':left_type,'right_type':right_type,'left_virtual':left_virtual,'right_virtual':right_virtual,
              'traffic_light_id':traffic_light_id,'traffic_sign_id':traffic_sign_ids,'point':f"{pnt.x},{pnt.y}",'heading':heading,'curvature':curvature,
              's_offset':s,'width':width,'left_width':width/2,'right_width':width/2,'geom':ctf.lonlat(pnt).wkt,'utm':pnt.wkt})

df=pd.DataFrame(l)
df.replace('',None,inplace=True)
sql = ("drop table if exists rm_lanes;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'rm_lanes')
sql = ("alter table rm_lanes alter column geom type geometry;"
       "alter table rm_lanes alter column utm type geometry;"
       f"select UpdateGeometrySRID('rm_lanes', 'utm', {srid});"
       f"select UpdateGeometrySRID('rm_lanes', 'geom', 4326);")
pg_map.execute(sql)

# 手动修改s路turn
sql = "update rm_lanes set turn = '1:8' where id = '2736';"
pg_map.execute(sql)









