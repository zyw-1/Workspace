# -*- coding: UTF-8 -*-
"""
基于stich_lane.xlsx，生成新表alane，包含geom字段
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from lib.config import pg_map,ctf,srid
import pandas as pd
from shapely import wkt,wkb
from shapely.geometry import LineString


df_lane = pg_map.get('mod_lane')
df_alane = pd.read_excel(f"{path}/offline_process/02-perception_map/alane/stich_lane.xlsx")
l = []
alane_id = 1
for alink, group in df_alane.groupby('lane_id_new'):
    group = group.sort_values('lane_seq_new')
    points = []
    lanes = []
    links = []
    for index,row in group.iterrows():
        lane_id = row['lane_id']
        link_id = df_lane[df_lane['lane_id']==str(lane_id)]['link_id'].values[0]
        geometry = df_lane[df_lane['lane_id']==str(lane_id)]['geom'].values[0]
        geom = wkb.loads(geometry,hex=True)
        points += list(geom.coords)
        lanes.append(str(lane_id))
        links.append(link_id)
    line = LineString(points)
    utm = ctf.utm(line)
    dic = {'alane_id':alane_id,'lane_ids':':'.join(lanes),'link_ids':','.join(links),'geometry':line.wkt,'utm':utm.wkt}
    l.append(dic)
    alane_id += 1

df=pd.DataFrame(l)
sql = "drop table if exists alane;"
pg_map.execute(sql)
pg_map.df_to_pg(df,'alane')
sql = ("alter table alane add column geom geometry;"
       "update alane set geom = st_geomfromtext(geometry,4326);"
       "drop index if exists spetial_alane;"
       "create index spetial_alane on alane using gist(geom);"
       "alter table alane alter column utm type geometry;"
       f"select UpdateGeometrySRID('alane', 'utm', {srid});"
       "drop index if exists spetial_alane_utm;"
       "create index spetial_alane_utm on alane using gist(utm);"
       f"delete from alane where alane_id = '712';")
pg_map.execute(sql)




