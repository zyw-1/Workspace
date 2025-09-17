"""
按照relative map的pb协议，处理stop line数据，生成新表rm_stop_lines，包含pb中需要的必须字段
"""

import os,sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)

import pandas as pd
from shapely import wkt,wkb
from shapely.geometry import Point, LineString,Polygon
from lib.config import pg_map,ctf,srid
import math


def generate_virtual_stopline(poly:Polygon,lane):
    # 检查多边形与车道是否有交点
    intersection = poly.intersection(lane)
    if intersection.is_empty or not hasattr(intersection, 'coords') or len(intersection.coords) == 0:
        return None
    pnt = Point(intersection.coords[0])
    
    # 找出与lane相交的第一个边
    poly_coords = list(poly.exterior.coords)
    dic = {}
    for i in range(len(poly_coords)-1):
        p1 = poly_coords[i]
        p2 = poly_coords[i+1]
        line = LineString([p1,p2])
        if line.intersects(geom) == True:
            dic[pnt.distance(line)] = line
    dic = dict(sorted(dic.items(), key=lambda x: x[0]))
    line = list(dic.items())[0][1]
    coords = list(line.coords)

    if coords[1][0] == coords[0][0]:
        p1 = Point(pnt.x-1,pnt.y)
        p2 = Point(pnt.x+1,pnt.y)
        if p1.intersects(poly) != True:
            diff_pnt = p1
        if p2.intersects(poly) != True:
            diff_pnt = p2
    else:
        k = (coords[1][1] - coords[0][1]) / (coords[1][0] - coords[0][0])
        k = -1/k
        dx = 1 / math.sqrt(1 + k**2)
        dy = k*dx
        x1 = pnt.x + dx
        y1 = pnt.y + dy
        x2 = pnt.x - dx
        y2 = pnt.y - dy
        p1 = Point(x1,y1)
        p2 = Point(x2,y2)
        if p1.intersects(poly) != True:
            diff_pnt = p1
        if p2.intersects(poly) != True:
            diff_pnt = p2

    if coords[1][0] == coords[0][0]:
        line = LineString([(pnt.x,pnt.y-2),(pnt.x,pnt.y+2)])
    else:
        k = (coords[1][1] - coords[0][1]) / (coords[1][0] - coords[0][0])
        dx = 2 / math.sqrt(1 + k**2)
        dy = k*dx
        x1 = diff_pnt.x + dx
        y1 = diff_pnt.y + dy
        x2 = diff_pnt.x - dx
        y2 = diff_pnt.y - dy
        line = LineString([(x1, y1), (x2, y2)])

    return line


def stop_line_nearest_junction(geom):
    # TODO: 根据距离最近逻辑匹配路口
    sql = f"select a.inters_code from rns_junction_polygon a ORDER BY st_geomfromtext('{geom}',4326) <-> a.geom LIMIT 1"
    data = pg_map.execute(sql,True)

    return int(data[0][0])



sql = "delete from rns_object_cwalk where lane_ids is null;"
pg_map.execute(sql)

df_stopline = pg_map.get('rns_object_sline_merge')
df_crosswalk = pg_map.get('rns_object_cwalk')
df_lane = pg_map.get('mod_lane')
'''
SL_UNKNOWN = 0;
SL_JUNCTION = 1;       //路口停车停止线
SL_LEFT_TURN_WAIT = 2; //左转待转区停止线
SL_STRAIGHT_WAIT = 3;  //直行待行区停止线
SL_DECELERATE = 4;     //路口减速让行线
SL_OTHER = 5;          //其他停止线

map:
1	停止线
2	减速让行线
3	停车让行线
999 其他
'''
dic_type = {1:1,2:4,3:5,999:5}
l=[]
for index,row in df_stopline.iterrows():
    id = int(row['obj_id'])
    print(id)
    geom = wkb.loads(row['geom'],hex=True)
    junction_id = stop_line_nearest_junction(geom.wkt)
    lane_ids = row['lane_ids']
    type = dic_type[row['sub_type']]
    ll = []
    points = list(wkt.loads(row['utm']).coords)
    for i in points:
        ll.append(f"{i[0]},{i[1]}")
    points = ':'.join(ll)
    is_virtual = 0 
    l.append({'id':id,'points':points,'type':type,'lane_ids':lane_ids,'is_virtual':is_virtual,'junction_id':junction_id,'geom':row['geom'],'utm':row['utm']})



'''没有停止线的人行道, 生成虚拟停止线'''
# TODO: 筛选逻辑要根据不同的地图再进行确认
sql = "select obj_id from rns_object_cwalk where obj_id not in (select a.obj_id from (select obj_id,st_buffer(geom,0.00005) as buffer from rns_object_cwalk) a, rns_object_sline b where st_intersects(a.buffer, b.geom) = true group by a.obj_id)"
data = pg_map.execute(sql,True)
no_sl_cwalks = [x[0] for x in data]
print(no_sl_cwalks)
id = 9999
for cwalk_id in no_sl_cwalks:
    print(cwalk_id)
    row = df_crosswalk[df_crosswalk.obj_id==cwalk_id].iloc[0]
    poly = wkb.loads(row['utm'])
    lane_ids = row['lane_ids']
    for lane_id in lane_ids.split(':'):
        geom = wkb.loads(df_lane[df_lane.lane_id==lane_id]['utm'].values[0],hex=True)
        virtual_sl = generate_virtual_stopline(poly,geom)
        # 检查虚拟停止线是否生成成功
        if virtual_sl is None:
            print(f"Warning: 无法为车道 {lane_id} 生成虚拟停止线，跳过")
            continue
        ll = []
        points = list(virtual_sl.coords)
        for i in points:
            ll.append(f"{i[0]},{i[1]}")
        points = ':'.join(ll)
        sql = f"select a.inters_id from rns_junction_polygon a, (select st_buffer(geom,0.0001) as buffer from rns_object_cwalk where obj_id = '{cwalk_id}') b where st_intersects(a.geom, b.buffer) = true"
        data = pg_map.execute(sql,True)
        if len(data) == 0:
            l.append({'id':id,'points':points,'type':5,'lane_ids':lane_id,'is_virtual':1,'geom':ctf.lonlat(virtual_sl).wkt,'utm':virtual_sl.wkt})
        else:
            l.append({'id':id,'points':points,'type':5,'lane_ids':lane_id,'is_virtual':1,'junction_id':int(data[0][0]),'geom':ctf.lonlat(virtual_sl).wkt,'utm':virtual_sl.wkt})
        id+=1


df=pd.DataFrame(l)
df.replace('',None,inplace=True)
sql = ("drop table if exists rm_stop_lines;")
pg_map.execute(sql)
pg_map.df_to_pg(df,'rm_stop_lines')
sql = ("alter table rm_stop_lines alter column geom type geometry;"
       "alter table rm_stop_lines alter column utm type geometry;"
       f"select UpdateGeometrySRID('rm_stop_lines', 'utm', {srid});"
       f"select UpdateGeometrySRID('rm_stop_lines', 'geom', 4326);")
pg_map.execute(sql)


# TODO: 暂时手动删除不符合要求的停止线
delete_sl_ids = [10007,10008,10009,9999,10000,10001,10016,10017,10018]
sql = f"delete from rm_stop_lines where id in ({','.join([str(x) for x in delete_sl_ids])});"

pg_map.execute(sql)
