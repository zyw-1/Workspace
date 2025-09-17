# -*- coding: UTF-8 -*-
"""
按照perception map的pb协议，处理stop line数据，生成新表pm_stop_lines，包含pb中需要的必须字段
"""
import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map as pg,ctf
import pandas as pd
from shapely import wkt,wkb


import warnings
warnings.filterwarnings('ignore')


def lane_in_which_alane(lane_id):
    alane_id = None
    lanes = df_alane[df_alane['lane_ids'].str.contains(lane_id)]
    for index,row in lanes.iterrows():
        lane_ids = row['lane_ids'].split(':')
        if lane_id in lane_ids:
            alane_id = row['alane_id']
            break
    return alane_id


'''
● SL_UNCLASSIFIED  0
● SL_JUNCTION //路口停车停止线  1
● SL_LEFT_TURN_WAIT //左转待转区停止线  2
● SL_STRAIGHT_WAIT  //直行待行区停止线  3
● SL_DECELERATE //路口减速让行线  4
● SL_VIRTUAL //虚拟停止线  5
'''
dic_type = {1:0,2:4,3:1,999:0}

df_stopline = pg.get('rns_object_sline')
df_rm_sl = pg.get('rm_stop_lines')
df_alane = pg.get('alane')
df_lane = pg.get('mod_lane')


l=[]
for index,row in df_rm_sl.iterrows():
    print(int(row['id']))
    sl_id = int(row['id'])
    lane_ids = row['lane_ids']

    link_id = df_lane[df_lane.lane_id==lane_ids.split(':')[0]]['link_id'].values[0]
    stop_line_type = row['type']
    exit_confidence = None
    geom = wkb.loads(row['geom'], hex=True)
    utm = ctf.utm(geom)
    coords = list(utm.coords)
    x1,y1 = coords[0]
    x2,y2 = coords[-1]
    alane_ids = []
    for lane_id in lane_ids.split(':'):
        alane_id = lane_in_which_alane(lane_id)
        if alane_id is not None:
            alane_ids.append(str(alane_id))
    dic = {'stop_line_id':sl_id,'exit_confidence':exit_confidence,'stop_line_type':stop_line_type,
            'line_points':f"{x1} {y1},{x2} {y2}",'link_id':link_id,'lane_ids':lane_ids,'geometry':geom.wkt
            ,'alane_ids':':'.join(alane_ids),'is_virtual':row['is_virtual']}
    l.append(dic)




# new_id = 1
# l = []
# for index,row in df_stopline.iterrows():
#     link_id = row['link_ids']
#     lane_id = row['lane_ids']
#     stop_line_type = dic_type[row['sub_type']]
#     for ii in lane_id.split(':'):
#         exit_confidence = None
#         geom = wkb.loads(row['geom'], hex=True)
#         utm = ctf.utm(geom)
#         coords = list(utm.coords)
#         x1,y1 = coords[0]
#         x2,y2 = coords[-1]
#         try:
#             alane_id = lane_in_which_alane(ii)
#             dic = {'stop_line_id':new_id,'exit_confidence':exit_confidence,'stop_line_type':stop_line_type,
#                     'line_points':f"{x1} {y1},{x2} {y2}",'link_id':link_id,'lane_id':ii,'geometry':geom.wkt
#                     ,'alane_id':alane_id}
#             l.append(dic)
#         except Exception as e:
#             print(ii, e)
#     new_id += 1


df=pd.DataFrame(l)

sql = "drop table if exists pm_stop_lines;"
pg.execute(sql)
pg.df_to_pg(df,'pm_stop_lines')
sql = ("alter table pm_stop_lines add column geom geometry;"
       "update pm_stop_lines set geom = st_geomfromtext(geometry,4326);"
       "delete from pm_stop_lines where alane_ids = '';")
pg.execute(sql)



