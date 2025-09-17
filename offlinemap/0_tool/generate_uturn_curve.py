#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掉头曲线生成工具
根据起点、途径点、终点生成平滑的半圆曲线
"""

import numpy as np
import math
from typing import Tuple, List
import argparse


class Point:
    """点类，表示三维点坐标"""
    def __init__(self, x: float, y: float, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z
    
    def __str__(self):
        return f"Point({self.x}, {self.y}, {self.z})"
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


class UTurnCurveGenerator:
    """掉头曲线生成器"""
    
    def __init__(self):
        pass
    
    def parse_point_string(self, point_str: str) -> Point:
        """
        解析点字符串，例如：
        "Point START(117.27978807636874592,39.69616520505093149,-2.70251252525636687)"
        """
        # 提取括号内的坐标
        start_idx = point_str.find('(')
        end_idx = point_str.find(')')
        if start_idx == -1 or end_idx == -1:
            raise ValueError(f"Invalid point string format: {point_str}")
        
        coords_str = point_str[start_idx+1:end_idx]
        coords = [float(x.strip()) for x in coords_str.split(',')]
        
        if len(coords) != 3:
            raise ValueError(f"Expected 3 coordinates, got {len(coords)}")
        
        return Point(coords[0], coords[1], coords[2])
    
    def calculate_circle_center(self, start: Point, way: Point, end: Point) -> Tuple[Point, float]:
        """
        根据三个点计算圆心和半径
        使用三点确定圆的几何方法
        """
        # 转换为numpy数组便于计算
        p1 = np.array([start.x, start.y])
        p2 = np.array([way.x, way.y])
        p3 = np.array([end.x, end.y])
        
        # 计算两条弦的中点
        mid1 = (p1 + p2) / 2
        mid2 = (p2 + p3) / 2
        
        # 计算弦的方向向量
        dir1 = p2 - p1
        dir2 = p3 - p2
        
        # 计算垂直向量（法向量）
        perp1 = np.array([-dir1[1], dir1[0]])
        perp2 = np.array([-dir2[1], dir2[0]])
        
        # 如果两条线平行，无法确定圆心
        det = perp1[0] * perp2[1] - perp1[1] * perp2[0]
        if abs(det) < 1e-10:
            # 退化情况，使用直线连接
            return Point((start.x + end.x) / 2, (start.y + end.y) / 2), 0
        
        # 解线性方程组求交点（圆心）
        diff = mid2 - mid1
        t = (diff[0] * perp2[1] - diff[1] * perp2[0]) / det
        
        center = mid1 + t * perp1
        radius = np.linalg.norm(center - p1)
        
        return Point(center[0], center[1], (start.z + way.z + end.z) / 3), radius
    
    def generate_arc_points(self, start: Point, way: Point, end: Point, num_points: int = 20) -> List[Point]:
        """
        生成弧线上的点
        """
        center, radius = self.calculate_circle_center(start, way, end)
        
        if radius == 0:
            # 退化情况，返回直线插值点
            return self.generate_line_points(start, end, num_points)
        
        # 计算起点和终点相对于圆心的角度
        start_angle = math.atan2(start.y - center.y, start.x - center.x)
        end_angle = math.atan2(end.y - center.y, end.x - center.x)
        way_angle = math.atan2(way.y - center.y, way.x - center.x)
        
        # 确定弧的方向（顺时针还是逆时针）
        # 通过检查途径点是否在起点到终点的较短弧上
        def normalize_angle(angle):
            while angle < 0:
                angle += 2 * math.pi
            while angle >= 2 * math.pi:
                angle -= 2 * math.pi
            return angle
        
        start_angle = normalize_angle(start_angle)
        end_angle = normalize_angle(end_angle)
        way_angle = normalize_angle(way_angle)
        
        # 判断弧的方向
        if start_angle <= end_angle:
            if way_angle >= start_angle and way_angle <= end_angle:
                # 逆时针方向
                angle_step = (end_angle - start_angle) / (num_points - 1)
                angles = [start_angle + i * angle_step for i in range(num_points)]
            else:
                # 顺时针方向
                end_angle += 2 * math.pi
                angle_step = (end_angle - start_angle) / (num_points - 1)
                angles = [start_angle + i * angle_step for i in range(num_points)]
        else:
            if way_angle >= start_angle or way_angle <= end_angle:
                # 逆时针方向
                end_angle += 2 * math.pi
                angle_step = (end_angle - start_angle) / (num_points - 1)
                angles = [start_angle + i * angle_step for i in range(num_points)]
            else:
                # 顺时针方向
                start_angle += 2 * math.pi
                angle_step = (start_angle - end_angle) / (num_points - 1)
                angles = [start_angle - i * angle_step for i in range(num_points)]
        
        # 生成弧线上的点
        points = []
        z_step = (end.z - start.z) / (num_points - 1) if num_points > 1 else 0
        
        for i, angle in enumerate(angles):
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            z = start.z + i * z_step
            points.append(Point(x, y, z))
        
        return points
    
    def generate_line_points(self, start: Point, end: Point, num_points: int = 20) -> List[Point]:
        """
        生成直线插值点（退化情况）
        """
        points = []
        for i in range(num_points):
            t = i / (num_points - 1) if num_points > 1 else 0
            x = start.x + t * (end.x - start.x)
            y = start.y + t * (end.y - start.y)
            z = start.z + t * (end.z - start.z)
            points.append(Point(x, y, z))
        return points
    
    def points_to_linestring(self, points: List[Point]) -> str:
        """
        将点列表转换为LINESTRING格式
        """
        coords = []
        for point in points:
            coords.append(f"{point.x} {point.y}")
        
        return f"LINESTRING ({', '.join(coords)})"
    
    def generate_uturn_curve(self, start_str: str, way_str: str, end_str: str, num_points: int = 20) -> str:
        """
        主函数：根据输入的三个点字符串生成掉头曲线
        """
        try:
            # 解析点坐标
            start = self.parse_point_string(start_str)
            way = self.parse_point_string(way_str)
            end = self.parse_point_string(end_str)
            
            print(f"起点: {start}")
            print(f"途径点: {way}")
            print(f"终点: {end}")
            
            # 生成弧线点
            arc_points = self.generate_arc_points(start, way, end, num_points)
            
            # 转换为LINESTRING格式
            linestring = self.points_to_linestring(arc_points)
            
            return linestring
            
        except Exception as e:
            print(f"生成曲线时出错: {e}")
            return ""


def main():
    """主函数，提供命令行接口"""
    generator = UTurnCurveGenerator()

    parser = argparse.ArgumentParser(description="根据起点/途径点/终点生成平滑半圆曲线，输出LINESTRING")
    parser.add_argument("--start", type=str, default="Point START(117.27944625293086744, 39.69310343245252426, -2.65009831600590928)", help="起点，格式如：Point START(x,y,z)")
    parser.add_argument("--way", type=str, default="Point WAY(117.27932134,39.69321980,-0.74792957057280773)", help="途径点，格式如：Point WAY(x,y,z)")
    parser.add_argument("--end", type=str, default="Point END(117.27918393767721739, 39.69311518103516079, -2.56459408247175702)", help="终点，格式如：Point END(x,y,z)")
    parser.add_argument("--num_points", type=int, default=30, help="生成弧线上点的数量（越大越平滑）")
    args = parser.parse_args()

    start_str = args.start
    way_str = args.way
    end_str = args.end
    num_points = args.num_points

    print("掉头曲线生成工具")
    print("使用参数：")
    print(f"起点: {start_str}")
    print(f"途径点: {way_str}")
    print(f"终点: {end_str}")
    print(f"点数: {num_points}")
    print()

    # 生成曲线
    result = generator.generate_uturn_curve(start_str, way_str, end_str, num_points=num_points)

    if result:
        print("生成的LINESTRING:")
        print(result)
        print()

        # 保存到文件
        with open('/home/ykzx/0_OffLineMap/0_dev/offlinemap/0_tool/uturn_curve_output.txt', 'w', encoding='utf-8') as f:
            f.write(result)
        print("结果已保存到: /home/ykzx/0_OffLineMap/0_dev/offlinemap/0_tool/uturn_curve_output.txt")
    else:
        print("生成曲线失败！")


if __name__ == "__main__":
    main()