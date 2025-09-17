"""
在mod_lane中增加一些必要的信息，如lane的heading、方位、type
"""

import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

sys.path.append(path)

import pandas as pd
import numpy as np
from shapely import wkb
from lib.config import pg_map


def trans_lane_type(type:int):
    '''
    proto :
    UNKNOWN_LANE = 0;
    MOTORWAY_LANE = 1; //机动车道, 对应地图bit: 0,4,5,6,7
    BICYCLE_LANE = 2; //非机动车道, 对应地图: 1,2
    VARIABLE_LANE = 3; //可变导向车道, 对应地图bit: 17
    REVERSIBLE_LANE = 4; //潮汐车道, 对应地图bit: 18
    EMERGENCY_LANE = 5; //应急车道, 对应地图bit: 11
    BUS_LANE = 6; //公交车道, 对应地图bit: 16
    WAITING_LANE = 7; //待转/待行区车道, 对应地图bit: 10
    '''
    type_list = []
    dic = {0:1, 4:1, 5:1, 6:1, 7:1, 
           1:2, 2:2,
           17:3,
           18:4,
           11:5,
           16:6,
           10:7}
    binary = bin(type)[1:]
    for i in range(len(binary)):
        if binary[::-1][i] == '1':
            type_list.append(dic.get(i,0))
    
    if 0 in type_list and len(type_list) > 1:
        type_list.remove(0)
    if 1 in type_list and len(type_list) > 1:
        type_list.remove(1)
        
    return ':'.join([str(x) for x in type_list])


'''
UNKNOWN_BOUNDARY = 0; // 未知类型
SINGLE_SOLID = 1; // 单实线
SINGLE_DASH = 2; // 单虚线

map: 
0: 虚拟标线
1: 单虚线
2: 双虚线
3: 单实线
4: 双实线
5: 左虚线右实线
6: 左实线右虚线
7: 短虚线
999: 其他
'''
dic_mark_type = {0:'0',1:'2',2:'2:2',3:'1',4:'1:1',5:'2:1',6:'1:2',7:'2',999:'0'}


def boundary_type(lane_id):
    lane_row = df_lane[df_lane.lane_id==lane_id].iloc[0]
    left_id = lane_row['lmkg_id']
    right_id = lane_row['rmkg_id']
    try:
        left_row = df_mark[df_mark.marking_id==left_id].iloc[0]
        right_row = df_mark[df_mark.marking_id==right_id].iloc[0]
        left_type = dic_mark_type[int(left_row['type'])]
        right_type = dic_mark_type[int(right_row['type'])]
        left_virtual = int(left_row['type'])
        left_virtual = 1 if left_virtual == 0 else 0
        right_virtual = int(right_row['type'])
        right_virtual = 1 if right_virtual == 0 else 0
    except:
        left_type,right_type,left_virtual,right_virtual = '0','0',1,1

    return [left_type,right_type,left_virtual,right_virtual]



'''
添加lane heading, 只用于箭头的可视化
添加lane的方位, 八分位, 正东为1, 顺时针旋转, 正南为3, 表示车行驶的朝向
更改lane type
'''

df_lane = pg_map.get('mod_lane')
df_mark = pg_map.get('rns_road_mark')
l = []
for index,row in df_lane.iterrows():
    utm = wkb.loads(row['utm'],hex=True)
    lane_id = row['lane_id']
    print(lane_id)
    coords = list(utm.coords)
    p1 = coords[0]
    p2 = coords[-1]
    dy = p2[1]-p1[1]
    dx = p2[0]-p1[0]
    rad = np.arctan2(dy, dx)
    deg = np.degrees(rad)
    if 22.5 > deg >= -22.5:
        azimuth = 1 # 东
    if 67.5 > deg >= 22.5:
        azimuth = 8 # 东北
    if 112.5 > deg >= 67.5:
        azimuth = 7 # 北
    if 157.5 > deg >= 112.5:
        azimuth = 6
    if 180 >= deg >= 157.5 or -157.5 > deg >= -180:
        azimuth = 5
    if -112.5 > deg >= -157.5:
        azimuth = 4
    if -67.5 > deg >= -112.5:
        azimuth = 3
    if -22.5 > deg >= -67.5:
        azimuth = 2
    type = trans_lane_type(int(row['lane_type']))
    mark_types = boundary_type(lane_id)
    l.append({'lane_id':lane_id,'heading':rad,'azimuth':azimuth,'type':type,'left_type':mark_types[0],'right_type':mark_types[1],'left_virtual':mark_types[2],'right_virtual':mark_types[3]})


df=pd.DataFrame(l)
sql = "drop table if exists df;"
pg_map.execute(sql)
pg_map.df_to_pg(df,'df')
sql = ("alter table mod_lane drop column if exists heading, drop column if exists azimuth, drop column if exists left_type, drop column if exists right_type,drop column if exists left_virtual, drop column if exists right_virtual;"
       "alter table mod_lane add column heading float, add column azimuth int, add left_type text, add right_type text, add left_virtual int, add right_virtual int;"
       "update mod_lane a set heading = b.heading from df b where a.lane_id = b.lane_id;"
       "update mod_lane a set azimuth = b.azimuth from df b where a.lane_id = b.lane_id;"
       "update mod_lane a set left_type = b.left_type from df b where a.lane_id = b.lane_id;"
       "update mod_lane a set right_type = b.right_type from df b where a.lane_id = b.lane_id;"
        "update mod_lane a set left_virtual = b.left_virtual from df b where a.lane_id = b.lane_id;"
       "update mod_lane a set right_virtual = b.right_virtual from df b where a.lane_id = b.lane_id;"
       "alter table mod_lane alter column lane_type type text;"
       "update mod_lane a set lane_type = b.type from df b where a.lane_id = b.lane_id;"
       "drop table if exists df;") 
pg_map.execute(sql)





