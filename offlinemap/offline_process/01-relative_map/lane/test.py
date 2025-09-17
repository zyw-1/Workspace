from shapely import wkt
import matplotlib.pyplot as plt

s = 'LINESTRING (500140.0745007702 4382650.271318935, 500148.1146227671 4382654.846447372, 500149.8041814192 4382656.321787247, 500150.7299222623 4382658.17202012, 500151.095376887 4382660.300390386, 500151.0210699473 4382662.574508152, 500150.6275259879 4382664.86198375, 500150.0352694284 4382667.030427693, 500149.3648244741 4382668.947450619, 500148.73671518 4382670.480663252, 500148.2714654304 4382671.497676327, 500148.0402254849 4382672.011489568, 500137.5323794247 4382694.156604404)'

geom = wkt.loads(s)
coords = list(geom.coords)
half_width = 1.6

left = []
right = []

for i in range(1,len(coords)):
    p1 = coords[i]
    p2 = coords[i - 1]
    # 计算线段方向向量
    v = (p2[0] - p1[0], p2[1] - p1[1])
    # 计算垂直向量
    v_perp = (-v[1], v[0])
    # 计算垂直向量的长度
    length = (v_perp[0] ** 2 + v_perp[1] ** 2) ** 0.5
    if length != 0:
        # 归一化垂直向量
        v_perp_normalized = (v_perp[0] / length, v_perp[1] / length)
    else:
        # 如果垂直向量长度为 0，使用默认值
        v_perp_normalized = (0, 1)
    # 计算左右两侧的点
    left_point = (p1[0] + half_width * v_perp_normalized[0], p1[1] + half_width * v_perp_normalized[1])
    right_point = (p1[0] - half_width * v_perp_normalized[0], p1[1] - half_width * v_perp_normalized[1])
    left.append(left_point)
    right.append(right_point)

# 处理最后一个点
p1 = coords[0]
p2 = coords[1]
# 计算线段方向向量
v = (p2[0] - p1[0], p2[1] - p1[1])
# 计算垂直向量
v_perp = (-v[1], v[0])
# 计算垂直向量的长度
length = (v_perp[0] ** 2 + v_perp[1] ** 2) ** 0.5
if length != 0:
    # 归一化垂直向量
    v_perp_normalized = (v_perp[0] / length, v_perp[1] / length)
else:
    # 如果垂直向量长度为 0，使用默认值
    v_perp_normalized = (0, 1)
# 计算左右两侧的点
left_point = (p1[0] - half_width * v_perp_normalized[0], p1[1] - half_width * v_perp_normalized[1])
right_point = (p1[0] + half_width * v_perp_normalized[0], p1[1] + half_width * v_perp_normalized[1])
left.insert(0,left_point)
right.insert(0,right_point)

fig = plt.figure()
plt.plot([x[0] for x in coords], [x[1] for x in coords], c='r')
plt.plot([x[0] for x in left], [x[1] for x in left], c='g')
plt.plot([x[0] for x in right], [x[1] for x in right], c='b')
plt.axis('equal')
plt.show()




