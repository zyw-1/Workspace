# -*- coding: UTF-8 -*-
"""
为原始lane添加虚拟换道lane，根据边线类型判断是否能换道，生成新表lane_add_virtual_change
"""

import os
import sys
import time
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path)
from lib.config import pg_map
import pandas as pd
from shapely.geometry import LineString, Point
from shapely import wkt,wkb
from functools import partial
import shapely.ops as ops


def genetare_vlane(side_lane_row,link_id,lane_id,geometry,utm,snode,enode,length,seq,chg_flg):
    def gen_vlane_geometry(geometry,side_lane_geom):
        geom = wkt.loads(geometry)
        rlane_geom = wkt.loads(side_lane_geom)
        vlane_snode_geometry = geom.interpolate(0.5, normalized=True)
        vlane_enode_geometry = rlane_geom.interpolate(0.5, normalized=True)
        vlane_geomtry = LineString([vlane_snode_geometry, vlane_enode_geometry])
        return vlane_geomtry

    def generate_vlane(link_id,lane_id,geometry,utm,side_lane_row):
        vlane_id = lane_id + '_' + side_lane_row['lane_id'].values[0]
        vlane_snode = lane_id + '_m'
        vlane_enode = side_lane_row['lane_id'].values[0] + '_m'
        vlane_geometry = gen_vlane_geometry(geometry,side_lane_row['geometry'].values[0])
        vlane_utm = gen_vlane_geometry(utm,side_lane_row['utm'].values[0])
        dic = {'link_id':link_id,'lane_id':vlane_id,'lane_seq':-1,'origin_lane':'0','chg_flg':-1,'length':vlane_utm.length,
                  'snode_id':vlane_snode,'enode_id':vlane_enode,'geometry':vlane_geometry.wkt,'utm':vlane_utm.wkt}

        return [dic]

    def lane_split(link_id,lane_id,geometry,utm,snode,enode,length,seq):
        geom = wkt.loads(geometry)
        utm = wkt.loads(utm)
        half_length = length/2
        mid_pnt_id = lane_id + '_m'
        forlane_geometry = ops.substring(geom, start_dist=0, end_dist=0.5, normalized=True)
        backlane_geometry = ops.substring(geom, start_dist=0.5, end_dist=1, normalized=True)
        forlane_utm = ops.substring(utm, start_dist=0, end_dist=0.5, normalized=True)
        backlane_utm = ops.substring(utm, start_dist=0.5, end_dist=1, normalized=True)
        dic1 = {'link_id': link_id, 'lane_id': lane_id + '_1', 'lane_seq': seq, 'chg_flg': chg_flg,
               'snode_id': snode, 'enode_id': mid_pnt_id, 'geometry': forlane_geometry.wkt, 'utm': forlane_utm.wkt,
               'length': half_length,'origin_lane':lane_id}
        dic2 = {'link_id': link_id, 'lane_id': lane_id+ '_2' , 'lane_seq': seq, 'chg_flg': chg_flg,
                'snode_id': mid_pnt_id, 'enode_id': enode, 'geometry': backlane_geometry.wkt, 'utm': backlane_utm.wkt,
                'length': half_length,'origin_lane':lane_id}

        return [dic1,dic2]

    def side_lane_split(side_lane_row):
        link_id = side_lane_row['link_id'].values[0]
        lane_id= side_lane_row['lane_id'].values[0]
        geom= wkt.loads(side_lane_row['geometry'].values[0])
        utm= wkt.loads(side_lane_row['utm'].values[0])
        snode= side_lane_row['snode_id'].values[0]
        enode= side_lane_row['enode_id'].values[0]
        length= float(side_lane_row['length'].values[0])
        seq= side_lane_row['lane_seq'].values[0]
        half_length = length / 2
        mid_pnt_id = lane_id + '_m'
        chg_flg = side_lane_row['chg_flg'].values[0]
        forlane_geometry = ops.substring(geom, start_dist=0, end_dist=0.5, normalized=True)
        backlane_geometry = ops.substring(geom, start_dist=0.5, end_dist=1, normalized=True)
        forlane_utm = ops.substring(utm, start_dist=0, end_dist=0.5, normalized=True)
        backlane_utm = ops.substring(utm, start_dist=0.5, end_dist=1, normalized=True)
        dic1 = {'link_id': link_id, 'lane_id': lane_id+ '_1', 'lane_seq': seq, 'chg_flg': chg_flg,
                'snode_id': snode, 'enode_id': mid_pnt_id, 'geometry': forlane_geometry.wkt, 'utm': forlane_utm.wkt,
                'length': half_length,'origin_lane':lane_id}
        dic2 = {'link_id': link_id, 'lane_id': lane_id+ '_2', 'lane_seq': seq, 'chg_flg': chg_flg,
                'snode_id': mid_pnt_id, 'enode_id': enode, 'geometry': backlane_geometry.wkt, 'utm': backlane_utm.wkt,
                'length': half_length,'origin_lane':lane_id}
        return [dic1, dic2]


    l1 = generate_vlane(link_id,lane_id,geometry,utm,side_lane_row)
    l2 = lane_split(link_id,lane_id,geometry,utm,snode,enode,length,seq)
    l3 = side_lane_split(side_lane_row)
    return l1+l2+l3


df_lane = pg_map.get('mod_lane')
df_lane.drop(df_lane[df_lane['enode_id'].isnull()].index,inplace=True)  # 删掉enode_id为空的两个lane
# df_lane.drop(df_lane[(df_lane['conn_type']==4)&(df_lane['vt_type']==1)].index,inplace=True)  # 删除虚拟的掉头路
df_lane.drop(df_lane[df_lane.lane_type=='2'].index,inplace=True)
df_lane.drop(df_lane[df_lane.lane_id=='1989'].index,inplace=True)
l = []
for index,row in df_lane.iterrows():
    l.append(wkb.loads(row['utm'],hex=True).wkt)
df_lane['utm'] = l


l = []
done_list = []
dic_right_change = {0:0,1:0,2:1,3:1}
for link_id,group in df_lane.groupby('link_id'):
    group = group.sort_values('lane_seq')
    for index,row in group.iterrows():
        lane_id = row['lane_id']
        seq = row['lane_seq']
        chg_flg = row['chg_flg']
        geometry = row['geometry']
        utm = row['utm']
        snode = row['snode_id']
        enode = row['enode_id']
        length = float(row['length'])
        vt_type = row['vt_type']
        if dic_right_change[chg_flg] == 0 or vt_type == 1 or length <= 12:
            if lane_id not in done_list:
                l.append({'link_id':link_id,'lane_id':lane_id,'lane_seq':seq,'origin_lane':lane_id,'chg_flg':chg_flg,
                          'snode_id':snode,'enode_id':enode,'geometry':geometry,'utm':utm,'length':length})
        else:
            # 检查右侧有无lane
            df = df_lane[df_lane['link_id']==link_id]
            if df['lane_seq'].max() == seq:
                if lane_id not in done_list:
                    l.append({'link_id': link_id, 'lane_id': lane_id, 'lane_seq': seq,'origin_lane':lane_id, 'chg_flg': chg_flg,
                              'snode_id': snode, 'enode_id': enode, 'geometry': geometry, 'utm': utm, 'length': length})
            else:
                rlane_row = df_lane[(df_lane['link_id'] == link_id) & (df_lane['lane_seq'] == seq + 1)]
                rlane_id = rlane_row['lane_id'].values[0]
                l += genetare_vlane(rlane_row,link_id, lane_id, geometry, utm, snode, enode, length, seq, chg_flg)
                done_list.append(lane_id)
                done_list.append(rlane_id)

# # 处理可左变道
done_list = []
dic_left_change = {0:0,1:1,2:0,3:1}
for link_id,group in df_lane.groupby('link_id'):
    group = group.sort_values('lane_seq')
    for index,row in group.iterrows():
        lane_id = row['lane_id']
        seq = row['lane_seq']
        chg_flg = row['chg_flg']
        geometry = row['geometry']
        utm = row['utm']
        snode = row['snode_id']
        enode = row['enode_id']
        length = float(row['length'])
        vt_type = row['vt_type']
        if dic_left_change[chg_flg] == 0 or vt_type == 1 or length <= 12:
            if lane_id not in done_list:
                l.append({'link_id':link_id,'lane_id':lane_id,'lane_seq':seq,'chg_flg':chg_flg,'origin_lane':lane_id,
                          'snode_id':snode,'enode_id':enode,'geometry':geometry,'utm':utm,'length':length})
        else:
            # 检查左侧有无lane
            df = df_lane[df_lane['link_id']==link_id]
            if seq == 1:
                if lane_id not in done_list:
                    l.append({'link_id': link_id, 'lane_id': lane_id, 'lane_seq': seq, 'chg_flg': chg_flg,'origin_lane':lane_id,
                              'snode_id': snode, 'enode_id': enode, 'geometry': geometry, 'utm': utm, 'length': length})
            else:
                llane_row = df_lane[(df_lane['link_id'] == link_id) & (df_lane['lane_seq'] == seq - 1)]
                llane_id = llane_row['lane_id'].values[0]
                l += genetare_vlane(llane_row,link_id, lane_id, geometry, utm, snode, enode, length, seq, chg_flg)
                done_list.append(lane_id)
                done_list.append(llane_id)
df = pd.DataFrame(l)

drop_list = []
for lane_id,group in df.groupby('origin_lane'):
    count = group.shape[0]
    if count >= 3:
        if str(lane_id) != '0':
            for index,row in group.iterrows():
                if '_' not in row['lane_id']:
                    drop_list.append(row['lane_id'])
df=df.drop_duplicates(subset=['lane_id'])
df=df.drop(df[df['lane_id'].isin(drop_list)].index)

sql = "drop table if exists lane_add_virtual_change;"
pg_map.execute(sql)
pg_map.df_to_pg(df,'lane_add_virtual_change')
sql = ("alter table lane_add_virtual_change drop column if exists geom;"
       "alter table lane_add_virtual_change add column geom geometry;"
       "update lane_add_virtual_change set geom = st_geomfromtext(geometry,4326);")
pg_map.execute(sql)















