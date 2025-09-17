import pandas as pd
import numpy as np
import os,sys
sys.path.append(os.path.join(os.path.dirname(__file__), "build"))
import pybind_solver
from scripts.config import pg_map
import numpy as np

'''
result: 
std::vector<std::vector<double>> results(6);
results[0] = std::move(smooth_x);
results[1] = std::move(smooth_y);
results[2] = std::move(smooth_s);
results[3] = std::move(smooth_heading);
results[4] = std::move(smooth_kappa);, kappa = 1/r (curvature)
results[5] = std::move(smooth_dkappa);
'''

solver = pybind_solver.Solver()
df_alane = pg_map.get('alane')
df_lane_line = pg_map.get('pm_lane_lines')

alane_id = 596
side = 'right_line'
line_ids = df_alane[df_alane.alane_id==alane_id][side].values[0].split(',')

x=[]
y=[]
for line_id in line_ids:
    df=df_lane_line[df_lane_line.line_id.astype(str)==line_id].sort_values('s_offset')
    x.extend(df['x'].tolist())
    y.extend(df['y'].tolist())

solver.init(x,y)
result = solver.get_solution()


import matplotlib.pyplot as plt

smooth_x,smooth_y = [],[]
for idx in range(len(result[0])):
    smooth_x.append(result[0][idx])
    smooth_y.append(result[1][idx])


plt.plot(x,y,c='r')
plt.scatter(x,y,c='r')

plt.plot(smooth_x,smooth_y,c='g')
plt.scatter(smooth_x,smooth_y,c='g')

plt.axis('equal')
plt.show()