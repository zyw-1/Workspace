"""
按照relative map的pb协议，处理stop line数据，生成新表rm_traffic_signs，包含pb中需要的必须字段
"""

import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

sys.path.append(path)

import pandas as pd
import numpy as np
from shapely import wkt,wkb
from shapely.geometry import Point, LineString
from lib.config import pg_map,ctf,srid


df_sign = pg_map.get('rns_object_sign')
df_lane = pg_map.get('mod_lane')
'''
UNKNOWN_SIGN = 0;
SINGLE_SPEED_LIMIT = 1; //单点最高限速，如普通限速标志、摄像头单点测速拍照  sub_type: 2
RANGE_SPEED_LIMIT = 2; //区间限速，区间平均速度拍照  sub_type: 
SPEED_LIMIT_END = 3; //限速解除  sub_type: 50
前两种理论上都应该有限速值, 如果数据里没有, 就不发; 限速接触, 如果限速值为null, 就发proto里规定的无效值

SIGN_ROAD_WORKS = 4; //道路施工  sub_type: 155
SIGN_YIELD = 5; //减速让行  sub_type: 127
SIGN_STOP = 6;  //停车让行  sub_type: 121
'''  
# TODO: 根据地图确认后修改
# TODO: 区分车道标志与道路标志，pb只发道路级别的，lane_id为road下所有的lane id，目前宝坻数据都先按照道路级的处理；如果是车道级的，要在交通标志处手动拆分lane，手动检查限速，以交通标志的优先
dic_type = {0:0,2:1,50:3,155:4,127:5,121:6}
df_sign = df_sign[df_sign.sub_type.astype(int).isin([0,2,50,155,127,121])]
l = []
for index,row in df_sign.iterrows():
    id = int(row['obj_id'])
    utm = wkb.loads(row['utm'])
    pnt = utm.minimum_rotated_rectangle.representative_point()
    type = dic_type[int(row['sub_type'])]
    is_virtual = 0
    # TODO: 后续填充lane id
    if not pd.isna(row['link_ids']):
        if ':' in row['link_ids']:
            raise ValueError("link id must be optional, but contains more than one link.")
        else:
            link_id = row['link_ids']
        
        lanes = df_lane[df_lane.link_id==link_id]['lane_id'].tolist()
        
        spd_max = row['spd_max']
        if type in [0,1,2]:
            if not pd.isna(spd_max):
                l.append({'id':id,'point':f"{pnt.x},{pnt.y}",'sign_type':type,'is_virtual':is_virtual,'sign_value':spd_max,'road_id':link_id,'lane_ids':':'.join(lanes),
                        'geom':ctf.lonlat(pnt).wkt,'utm':pnt.wkt})
        if type == 3:
            if not pd.isna(spd_max):
                l.append({'id':id,'point':f"{pnt.x},{pnt.y}",'sign_type':type,'is_virtual':is_virtual,'sign_value':spd_max,'road_id':link_id,'lane_ids':':'.join(lanes),
                        'geom':ctf.lonlat(pnt).wkt,'utm':pnt.wkt})
            else:
                l.append({'id':id,'point':f"{pnt.x},{pnt.y}",'sign_type':type,'is_virtual':is_virtual,'sign_value':65535,'road_id':link_id,'lane_ids':':'.join(lanes),
                        'geom':ctf.lonlat(pnt).wkt,'utm':pnt.wkt})
        if type in [4,5,6]:
            l.append({'id':id,'point':f"{pnt.x},{pnt.y}",'sign_type':type,'is_virtual':is_virtual,'sign_value':65535,'road_id':link_id,'lane_ids':':'.join(lanes),
                        'geom':ctf.lonlat(pnt).wkt,'utm':pnt.wkt})

df=pd.DataFrame(l)
df.replace('',None,inplace=True)
sql = ("drop table if exists rm_traffic_signs;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'rm_traffic_signs')
sql = ("alter table rm_traffic_signs alter column geom type geometry;"
       "alter table rm_traffic_signs alter column utm type geometry;"
       f"select UpdateGeometrySRID('rm_traffic_signs', 'utm', {srid});"
       f"select UpdateGeometrySRID('rm_traffic_signs', 'geom', 4326);")
pg_map.execute(sql)
    





