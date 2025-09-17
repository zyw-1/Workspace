"""
按照relative map的pb协议，处理traffic light数据，生成新表rm_traffic_lights，包含pb中需要的必须字段
"""

import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

sys.path.append(path)

import pandas as pd
import numpy as np
from shapely import wkt,wkb
from shapely.geometry import Point, LineString
from lib.config import pg_map,ctf,srid
import math


def panel_position(junc_poly,lane_ids):
    # TODO: 只先生成机动车灯，暂不处理行人灯
    x1=[]
    y1=[]
    x2=[]
    y2=[]
    for lane_id in lane_ids.split(':'):
        utm = wkb.loads(df_lane[df_lane.lane_id==lane_id]['utm'].values[0],hex=True)
        coords = list(utm.coords)
        x1.append(coords[-2][0])
        y1.append(coords[-2][1])
        x2.append(coords[-1][0])
        y2.append(coords[-1][1])
    x1 = np.mean(x1)
    y1 = np.mean(y1)
    x2 = np.mean(x2)
    y2 = np.mean(y2)
    x_label = 1 if x2 > x1 else -1
    y_label = 1 if y2 > y1 else -1
    k = abs((y2-y1)/(x2-x1))
    dx = 100 / math.sqrt(1 + k**2)
    dy = k*dx
    a1 = x2 + dx * x_label
    b1 = y2 + dy * y_label
    line = LineString([(x2, y2), (a1, b1)])
    intersec_line = junc_poly.intersection(line)
    # import matplotlib.pyplot as plt
    # fig = plt.figure()
    # x,y=[],[]
    # for i in junc_poly.exterior.coords:
    #     x.append(i[0])
    #     y.append(i[1])
    # plt.plot(x,y)
    # x,y=[],[]
    # for i in line.coords:
    #     x.append(i[0])
    #     y.append(i[1])
    # plt.plot(x,y)
    
    pnt = intersec_line.interpolate(intersec_line.length-10)
    # plt.scatter(pnt.x,pnt.y)
    # plt.axis('equal')
    # plt.show()
    return pnt


def panel_type(phase,lane_ids):
    '''
    UNKNOWN_LIGHT = 0;
    STRAIGHT = 1; // 直行
    LEFT = 2; // 左转
    RIGHT = 3; // 右转
    U_TURN = 4; // 调头
    BICYCLE = 5; // 非机动车道信号灯
    CIRCULAR = 6; // 圆饼信号灯
    WAIT_TO_PROCEED = 7; // 待行信号灯
    WAIT_TO_TURN = 8; // 待转信号灯

    map:
    1 直行
    2 左转
    3 右转
    4 掉头
    0 未知
    '''

    dic_panel = {1:1, 2:2, 4:6, 8:1, 9:2, 15:1, 16:2, 18:6, 22:1, 23:2, 29:1, 30:2, 32:6, 36:1, 37:2, 43:1, 44:2, 46:6, 50:1, 51:2}
    
    # if phase in [2,16,30,44]:  # 
    #     type = 2
    # elif phase in [4,18,32,46]:
    #     type = 6
    # else:
    #     l = []
    #     for lane_id in lane_ids.split(':'):
    #         conn_type = df_lane[df_lane.lane_id==lane_id]['conn_type'].values[0]
    #         l.append(conn_type)
    #     l = list(set(l))
    #     if len(l) == 1:
    #         type = l[0]
    #     else:
    #         print(lane_id)
    #         raise ValueError("Inconsistent lane conn types.")
    if dic_panel.get(phase) is None:
        return '0'
    
    return str(dic_panel[phase])


def light_stop_line_ids(lane_ids):
    l = []
    for lane_id in lane_ids.split(':'):
        df = df_stopline[df_stopline.lane_ids.str.contains(lane_id)]
        for index,row in df.iterrows():
            stopline_id = row['id']
            stopline_lane_ids = row['lane_ids'].split(':')
            if lane_id in stopline_lane_ids:
                l.append(str(stopline_id))
    l = list(set(l))

    return ':'.join(l)


df_phase = pg_map.get('rns_signal_phase')
df_lane = pg_map.get('mod_lane')
df_junction = pg_map.get('rns_junction_polygon')
df_stopline = pg_map.get('rm_stop_lines')

'''信号灯关联表里的北，表示车 北-->南, TODO: 根据不同项目修改'''
dic_azimuth = {1:'东', 2:'东', 3:'东', 4:'东', 8:'东南', 9:'东南', 15:'南', 16:'南', 17:'南', 18:'南', 22:'西南', 23:'西南', 
             29:'西', 30:'西',31:'西', 32:'西', 36:'西北', 37:'西北', 43:'北', 44:'北', 45:'北', 46:'北', 50:'东北', 51:'东北'}

l = []
for index,row in df_phase.iterrows():
    id = int(row['signal_id'])
    print(id)
    lane_ids = row['ctrl_lanes']
    phase = row['phase_id']
    inters_code = row['inters_id']
    inters_id = int(df_junction[df_junction.inters_code==inters_code]['inters_code'].values[0])
    junc_poly = wkb.loads(df_junction[df_junction.inters_code==inters_code]['utm'].values[0],hex=True)
    pnt = panel_position(junc_poly,lane_ids)
    type = panel_type(phase,lane_ids)
    azimuth = dic_azimuth[phase]
    # TODO: 先不考虑非机动车信号灯关联的人行道
    stop_line_ids = light_stop_line_ids(lane_ids)
    lane_id = lane_ids.split(':')[0]
    heading = df_lane[df_lane.lane_id==lane_id]['heading'].values[0]
    l.append({'id':id,'point':f"{pnt.x},{pnt.y}",'type':type,'lane_ids':lane_ids,'junction_id':inters_id,'heading':heading,'azimuth':azimuth,
              'stop_line_ids':stop_line_ids,'geom':ctf.lonlat(pnt).wkt,'utm':pnt.wkt})

df=pd.DataFrame(l)
l = []
i = 0
for junction_id,group in df.groupby('junction_id'):
    for azimuth,group1 in group.groupby('azimuth'):
        i+=1
        for index,row in group1.iterrows():
            lane_id = row['id']
            l.append({'id':lane_id,'traffic_light_id':i})
        
df1 = pd.DataFrame(l)
df=pd.merge(left=df,right=df1,on='id',how='left')
df.replace('',None,inplace=True)
sql = ("drop table if exists rm_light_panels;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'rm_light_panels')
sql = ("alter table rm_light_panels alter column geom type geometry;"
       "alter table rm_light_panels alter column utm type geometry;"
       f"select UpdateGeometrySRID('rm_light_panels', 'utm', {srid});"
       f"select UpdateGeometrySRID('rm_light_panels', 'geom', 4326);")
pg_map.execute(sql)


'''填充停止线关联的信号灯id, optional类型'''
dic = {}
for index,row in df.iterrows():
    traffic_light_id = row['traffic_light_id']
    stop_line_ids = row['stop_line_ids']
    for stop_line_id in stop_line_ids.split(':'):
        if stop_line_id not in dic.keys():
            dic[stop_line_id] = [traffic_light_id]
        else:
           dic[stop_line_id].append(traffic_light_id)

l = []
for i in dic:
    if len(set(dic[i])) > 1 :
        print(f"check stop line {i} and its traffic light.")
    l.append({'stop_line_id':int(i),'traffic_light_id':':'.join([str(x) for x in set(dic[i])])})
df = pd.DataFrame(l)
sql = ("drop table if exists df;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'df')
sql = ("alter table rm_stop_lines drop column if exists traffic_light_id;"
       "alter table rm_stop_lines add column traffic_light_id text;"
       "update rm_stop_lines a set traffic_light_id = df.traffic_light_id from df where df.stop_line_id = a.id;"
       "drop table if exists df;")
pg_map.execute(sql)


# TODO: 人行道关联信号灯id



