# -*- coding: UTF-8 -*-
import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
from scripts.config import pg_map as pg,ctf,srid
import pandas as pd
from shapely import wkt


sql = "delete from pm_feature_points where dist_on_alane is null;"
pg.execute(sql)


dic_type = {'pm_cross_walks':'cross_walk','pm_junction_lights':'junction_light','pm_lane_arrows':'lane_arrow',
             'pm_stop_lines':'stop_line','smooth_lane_lines':'lane_line','pm_feature_points':'feature_point',}
dic_id = {'pm_cross_walks':'cross_walk_id','pm_junction_lights':'junction_light_id','pm_lane_arrows':'lane_arrow_id',
          'pm_stop_lines':'stop_line_id','smooth_lane_lines':'line_id','pm_feature_points':'feature_point_id'}


l=[]
for table in dic_type:
    print(table)
    df= pg.get(table)
    for index,row in df.iterrows():
        id = row[dic_id[table]]
        type = dic_type[table]
        geometry = row['geometry']
        utm = ctf.utm(wkt.loads(geometry)).wkt
        dist = round(row['dist_on_alane'],2)
        alane_id = row['alane_id']
        link_id = row['link_id']
        if table == 'smooth_lane_lines':
            idx = f"{str(id)}|{str(dist)}"
        else:
            idx = None
        dic = {'id':id,'type':type,'geometry':geometry,'utm':utm,'dist_on_alane':float(dist),'alane_id':alane_id,'link_id':link_id,'idx':idx}
        l.append(dic)
df=pd.DataFrame(l)
sql = "drop table if exists pm_all_features;"
pg.execute(sql)
pg.df_to_pg(df,'pm_all_features')


sql = ("alter table pm_all_features add column geom geometry;"
       "update pm_all_features set geom = st_geomfromtext(geometry,4326);"
       "alter table pm_all_features alter column utm type geometry;"
       f"select UpdateGeometrySRID('pm_all_features', 'utm', {srid});"
       "drop table if exists pm_features_around_junction;"
        "create table pm_features_around_junction as select a.id::text as inters_id, b.* from rm_junctions a, pm_all_features b where st_intersects(st_buffer(a.utm,60), b.utm) = true;"
       "drop index if exists spetial_pm_all_features;"
       "create index spetial_pm_all_features on pm_all_features using gist(utm);")
pg.execute(sql)

sql = ("alter table pm_all_features alter column alane_id type int;")
pg.execute(sql)




