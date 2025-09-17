# -*- coding: UTF-8 -*-
import pandas as pd
from scripts.config import pg_map
import numpy as np
import json
import math

def remake_line_points(x,y,start_label,end_label):
    if start_label == False:
        x1, y1 = x[0],y[0]
        x2, y2 = x[1],y[1]
        ab_distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        direction_x = (x2 - x1) / ab_distance
        direction_y = (y2 - y1) / ab_distance
        target_x = x1 + direction_x * 0.8
        target_y = y1 + direction_y * 0.8
        x[0] = target_x
        y[0] = target_y
    if end_label == False:
        x.pop()
        y.pop()

    return x,y


df_lane_lines = pg_map.get('pm_lane_lines')
with open('dic_smooth.json', 'r') as json_file:
    dic_smooth = json.load(json_file)


dic_remake_xy = {}
for line in dic_smooth:
    print(line)
    df = df_lane_lines[df_lane_lines.line_id == int(line)].sort_values('s_offset')
    start_label = dic_smooth[line]['start']
    end_label = dic_smooth[line]['end']
    heading_list = df['heading'].tolist()
    start_heading,end_heading = heading_list[0],heading_list[-1]
    x = [row['x'] for index,row in df.iterrows()]
    y = [row['y'] for index,row in df.iterrows()]
    remake_x, remake_y = remake_line_points(x,y,start_label,end_label)
    dic_remake_xy[line] = [remake_x,remake_y,start_heading,end_heading]

with open('dic_remake_xy.json', 'w') as json_file:
    json.dump(dic_remake_xy, json_file, indent=4)



# with open('dic_remake_xy.json','r') as f:
#     dic_remake_xy = json.load(f)

# line_id = '1'

# import matplotlib.pyplot as plt
# fig = plt.figure()
# remake_x,remake_y,h1,h2 = dic_remake_xy[line_id]
# df = df_lane_lines[df_lane_lines.line_id == int(line_id)].sort_values('s_offset')
# x = [row['x'] for index,row in df.iterrows()]
# y = [row['y'] for index,row in df.iterrows()]


# plt.scatter(remake_x,remake_y, s=10,c='r')
# plt.plot(remake_x,remake_y,c='r')

# plt.scatter(x,y,s=10,c='g')
# plt.plot(x,y,c='g')



# plt.show()








