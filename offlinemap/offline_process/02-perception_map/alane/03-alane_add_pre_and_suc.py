# -*- coding: UTF-8 -*-
"""
基于stich_lane_conn_type.xlsx，为alane表增加前继后继字段
"""

import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path)
import pandas as pd
from lib.config import pg_map




df_conn = pd.read_excel(f"{path}/offline_process/02-perception_map/alane/stich_lane_conn_type.xlsx",sheet_name='Sheet1')
df_alane = pg_map.get('alane')
dic_type = {'along_side':0,'merge_parallel':1,'split_parallel':3}

l = []
for index,row in df_alane.iterrows():
    alane = row['alane_id']
    # 寻找当前alane的pre
    df=df_conn[df_conn['suc_id']==alane]
    pres_list = []
    for index1,row1 in df.iterrows():
        pre_id = row1['pre_id']
        conn_type = dic_type[row1['conn_type']]
        dic1 = {pre_id:conn_type}
        pres_list.append(f"{pre_id}:{conn_type}")
    # 寻找当前alane的suc
    df = df_conn[df_conn['pre_id'] == alane]
    sucs_list = []
    for index1, row1 in df.iterrows():
        suc_id = row1['suc_id']
        conn_type = dic_type[row1['conn_type']]
        dic1 = {suc_id: conn_type}
        sucs_list.append(f"{suc_id}:{conn_type}")
    l.append({'alane_id':alane,'pres':','.join(pres_list),'sucs':','.join(sucs_list)})


df=pd.DataFrame(l)
sql = "drop table if exists df;"
pg_map.execute(sql)
pg_map.df_to_pg(df,'df')
sql = ("alter table alane drop column if exists pres, drop column if exists sucs;"
       "alter table alane add column pres text, add column sucs text;"
       "update alane set pres = df.pres from df where alane.alane_id=df.alane_id;"
       "update alane set sucs = df.sucs from df where alane.alane_id=df.alane_id;"
       "drop table if exists df;")
pg_map.execute(sql)







