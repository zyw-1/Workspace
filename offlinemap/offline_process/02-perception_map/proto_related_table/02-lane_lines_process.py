# -*- coding: UTF-8 -*-
"""
按照perception map的pb协议，处理lane line数据，生成新表pm_lane_lines_no_distinct，此表没有对mark连接处的点做去重，后面会做去重
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map as pg,ctf
import pandas as pd
from shapely import wkt,wkb
from shapely.geometry import Point
import copy


def merge_marking(lane_list,list_marking,df_lane):
    list_lmkg = []
    list_rmkg = []
    for lane_id in lane_list:
        lmkg_id = df_lane[df_lane['lane_id']==str(lane_id)]['lmkg_id'].values[0]
        rmkg_id = df_lane[df_lane['lane_id'] == str(lane_id)]['rmkg_id'].values[0]
        if lmkg_id in list_marking:   # 检查lane图层中的左边线是否在marking图层中存在
            list_lmkg.append(str(lmkg_id))
        if rmkg_id in list_marking:
            list_rmkg.append(str(rmkg_id))

    return list_lmkg,list_rmkg


def group_mkg_by_type(list_mkg):
    type_list = []
    for i in list_mkg:
        type = df_marking[df_marking['marking_id'] == str(i)]['type'].values[0]
        if type == 0:
            type_list.append(0)
        else:
            type_list.append(1)
    
    l = []
    current_group = [0]
    for i in range(1,len(type_list)):
        if type_list[i] == type_list[i-1]:
            current_group.append(i)
        else:
            l.append(current_group)
            current_group = [i]
    
    l.append(current_group)

    group_mkg = []
    for lst in l:
        ll =[] 
        for i in lst:
            ll.append(list_mkg[i])
        group_mkg.append(ll)

    return group_mkg        


# def merge_marking_scatter(list_mkg,df_marking_scatter,merge_lane,side):
#     global new_marking_id
#     l = []
#     group_mkg = group_mkg_by_type(list_mkg)
#     for group in group_mkg:
#         mark_s_offset = 0
#         seq = 0
#         for mkg in group:
#             link_id = df_marking[df_marking['marking_id']==mkg]['link_id'].values[0]
#             df_scatter = df_marking_scatter[df_marking_scatter['id'].astype(str)==mkg]
#             df_scatter = df_scatter.sort_values('s_offset')

#             for index,row in df_scatter.iterrows():
#                 geometry = wkb.loads(row['geom'],hex=True).wkt
#                 seq += 1
#                 s = row['s_offset']
#                 geom = wkb.loads(row['geom'],hex=True)
#                 utm = ctf.utm(geom)
#                 x = utm.x
#                 y = utm.y
#                 line_type = row['types']
#                 line_color = row['colors']
#                 is_virtual = row['is_virtual']
#                 curvature = row['curvature']
#                 heading = row['heading']
#                 exit_confidence = None

#                 if geometry in list_feature_points_geometry:
#                     related_feature_node_id = int(df_feature[df_feature['geometry']==geometry]['feature_point_id'].values[0])
#                 else:
#                     related_feature_node_id = 999
                
#                 dic = {'line_id':new_marking_id,'exit_confidence':exit_confidence,'related_feature_point_id':related_feature_node_id,
#                     'line_type':line_type,'line_color':line_color,'is_virtual':is_virtual,'x':x,'y':y,'curvature':curvature,'s_offset':s+mark_s_offset,
#                     'heading':heading,'sequence':seq,'geometry':geom.wkt,'link_id':link_id,'side':side,'alane_id':merge_lane,'marking_id':mkg}
                
#                 l.append(dic)
#             mark_s_offset = mark_s_offset + s + 0.8
        
#         new_marking_id+=1
#     last_mkg = list_mkg[-1]
#     dic_last = copy.copy(l[-1])
#     row = df_marking[df_marking['marking_id']==last_mkg].iloc[0]
#     geom = wkb.loads(row['geom'],hex=True)
#     coord = list(geom.coords)[-1]
#     geometry = Point(coord).wkt
#     utm = ctf.utm(Point(coord))
#     dic_last['x'] = utm.x
#     dic_last['y'] = utm.y
#     dic_last['sequence'] = l[-1]['sequence'] + 1
#     dic_last['geometry'] = geometry
#     total_length = 0
#     for i in group:
#         length = df_marking[df_marking['marking_id']==i]['length'].values[0]
#         total_length += length
#     dic_last['s_offset'] = total_length
#     if geometry in list_feature_points_geometry:
#         related_feature_node_id = int(df_feature[df_feature['geometry']==geometry]['feature_point_id'].values[0])
#     else:
#         related_feature_node_id = 999
#     dic_last['related_feature_point_id'] = related_feature_node_id
#     l.insert(-1,dic_last)


#     return l


def merge_marking_scatter(list_mkg,df_marking_scatter,merge_lane,side):
    global new_marking_id
    l = []
    group_mkg = group_mkg_by_type(list_mkg)
    for group in group_mkg:
        mark_s_offset = 0
        seq = 0
        for mkg in group:
            link_id = df_marking[df_marking['marking_id']==mkg]['link_id'].values[0]
            df_scatter = df_marking_scatter[df_marking_scatter['id'].astype(str)==mkg]
            df_scatter = df_scatter.sort_values('s_offset')

            for index,row in df_scatter.iterrows():
                geometry = wkb.loads(row['geom'],hex=True).wkt
                seq += 1
                s = row['s_offset']
                geom = wkb.loads(row['geom'],hex=True)
                utm = ctf.utm(geom)
                x = utm.x
                y = utm.y
                line_type = row['types']
                line_color = row['colors']
                is_virtual = row['is_virtual']
                curvature = row['curvature']
                heading = row['heading']
                exit_confidence = None

                if geometry in list_feature_points_geometry:
                    related_feature_node_id = int(df_feature[df_feature['geometry']==geometry]['feature_point_id'].values[0])
                else:
                    related_feature_node_id = 999
                
                dic = {'line_id':new_marking_id,'exit_confidence':exit_confidence,'related_feature_point_id':related_feature_node_id,
                    'line_type':line_type,'line_color':line_color,'is_virtual':is_virtual,'x':x,'y':y,'curvature':curvature,'s_offset':s+mark_s_offset,
                    'heading':heading,'sequence':seq,'geometry':geom.wkt,'link_id':link_id,'side':side,'alane_id':merge_lane,'marking_id':mkg}
                # print(new_marking_id,s+mark_s_offset)
                l.append(dic)
            mark_s_offset = mark_s_offset + s + 0.8
        
        new_marking_id+=1
        last_mkg = group[-1]
        dic_last = copy.copy(l[-1])
        row = df_marking[df_marking['marking_id']==last_mkg].iloc[0]
        geom = wkb.loads(row['geom'],hex=True)
        coord = list(geom.coords)[-1]
        geometry = Point(coord).wkt
        utm = ctf.utm(Point(coord))
        dic_last['x'] = utm.x
        dic_last['y'] = utm.y
        dic_last['sequence'] = l[-1]['sequence'] + 1
        dic_last['geometry'] = geometry
        total_length = 0
        
        # for i in group:
        #     length = df_marking[df_marking['marking_id']==i]['length'].values[0]
        #     total_length += length
        dic_last['s_offset'] = mark_s_offset
        
        if geometry in list_feature_points_geometry:
            related_feature_node_id = int(df_feature[df_feature['geometry']==geometry]['feature_point_id'].values[0])
        else:
            related_feature_node_id = 999
        dic_last['related_feature_point_id'] = related_feature_node_id
        l.insert(-1,dic_last)


    return l


df_feature = pg.get('pm_feature_points')
df_marking_scatter = pg.get('rm_lane_boundarys')
df_marking = pg.get('mod_mark')
df_lane = pg.get('mod_lane')
df_alane = pg.get('alane')
# df_alane=df_alane[df_alane.alane_id.isin([232,233])]

l=[]
done_list = []
new_marking_id = 1
list_marking = df_marking['marking_id'].tolist()

list_feature_points_geometry = []
for index,row in df_feature.iterrows():
    list_feature_points_geometry.append(row['geometry'])


for index,row in df_alane.iterrows():
    lane_list = row['lane_ids'].split(':')
    merge_lane = row['alane_id']
    list_lmkg, list_rmkg = merge_marking(lane_list,list_marking,df_lane)
    if len(list_lmkg) != 0 :
        l_label = ','.join(list_lmkg)
        r_label = ','.join(list_rmkg)
        list_lmkg_scatter = merge_marking_scatter(list_lmkg, df_marking_scatter, merge_lane, 'left')
        new_marking_id += 1
        l += list_lmkg_scatter
        list_rmkg_scatter = merge_marking_scatter(list_rmkg, df_marking_scatter, merge_lane,'right')
        new_marking_id += 1
        l += list_rmkg_scatter
    # if l_label not in done_list:
    #     list_lmkg_scatter = merge_marking_scatter(list_lmkg,df_marking_scatter,new_marking_id,merge_lane,'left')
    #     new_marking_id+=1
    #     done_list.append(l_label)
    #     l += list_lmkg_scatter
    # if r_label not in done_list:
    #     list_rmkg_scatter = merge_marking_scatter(list_rmkg, df_marking_scatter, new_marking_id,merge_lane,'right')
    #     new_marking_id += 1
    #     done_list.append(r_label)
    #     l+=list_rmkg_scatter

df=pd.DataFrame(l)

l=[]
new_id = 1
for index,row in df.iterrows():
    l.append(new_id)
    new_id+=1
df['lane_line_id'] = l
df=df.drop_duplicates(subset=['geometry','line_id', 'side'])

l = []
dic={}
uuid=0
for geometry,group in df.groupby('geometry'):
    uuid+=1
    for index,row in group.iterrows():
        lane_line_id = row['lane_line_id']
        dic[lane_line_id] = uuid
for index,row in df.iterrows():
    lane_line_id = row['lane_line_id']
    l.append(dic[lane_line_id])

df['uuid'] = l

sql = "drop table if exists pm_lane_lines_no_distinct;"
pg.execute(sql)
pg.df_to_pg(df,'pm_lane_lines_no_distinct')
sql = ("alter table pm_lane_lines_no_distinct add column geom geometry;"
       "update pm_lane_lines_no_distinct set geom = st_geomfromtext(geometry,4326);"
       "alter table pm_feature_points drop column if exists link_id;"
       "alter table pm_feature_points add column link_id text;"
       "update pm_feature_points a set link_id = b.link_id from pm_lane_lines_no_distinct b where a.feature_point_id = b.related_feature_point_id;"
       "delete from pm_feature_points where link_id is null;"
       "alter table pm_feature_points drop column if exists alane_id;"
       "alter table pm_feature_points add column alane_id int;"
       "update pm_feature_points a set alane_id = b.alane_id from pm_lane_lines_no_distinct b where a.feature_point_id = b.related_feature_point_id;"
       "alter table alane drop column if exists right_line, drop column if exists left_line;"
       "alter table alane add column right_line int, add column left_line int;"
        "update alane a set right_line = b.line_id from pm_lane_lines_no_distinct b where a.alane_id = b.alane_id and b.side = 'right';"
        "update alane a set left_line = b.line_id from pm_lane_lines_no_distinct b where a.alane_id = b.alane_id and b.side = 'left';")
pg.execute(sql)






