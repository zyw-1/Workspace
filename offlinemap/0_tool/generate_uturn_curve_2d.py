#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2D 掉头曲线生成工具
根据起点、途径点、终点（仅 x, y）生成平滑的半圆曲线，输出为 WKT LINESTRING
"""

import math
import argparse
from typing import Tuple, List


class Point2D:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point({self.x}, {self.y})"

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


class UTurnCurveGenerator2D:
    def parse_point_string(self, point_str: str) -> Point2D:
        """
        解析点字符串，例如：
        "Point START(117.27978807636874592,39.69616520505093)"
        """
        start_idx = point_str.find('(')
        end_idx = point_str.rfind(')')
        if start_idx == -1 or end_idx == -1:
            raise ValueError(f"Invalid point string format: {point_str}")
        coords_str = point_str[start_idx + 1:end_idx]
        parts = [s.strip() for s in coords_str.split(',')]
        if len(parts) != 2:
            raise ValueError(f"Expected 2 coordinates, got {len(parts)}")
        x = float(parts[0])
        y = float(parts[1])
        return Point2D(x, y)

    def _circle_center_by_3points(self, a: Point2D, b: Point2D, c: Point2D) -> Tuple[Point2D, float]:
        """
        由三点求圆心与半径；若三点近乎共线，返回半径=0
        """
        x1, y1 = a.x, a.y
        x2, y2 = b.x, b.y
        x3, y3 = c.x, c.y

        # 公式法：解线性方程组
        A = 2 * (x2 - x1)
        B = 2 * (y2 - y1)
        C = x2 * x2 + y2 * y2 - x1 * x1 - y1 * y1
        D = 2 * (x3 - x2)
        E = 2 * (y3 - y2)
        F = x3 * x3 + y3 * y3 - x2 * x2 - y2 * y2

        det = A * E - B * D
        if abs(det) < 1e-12:
            return Point2D((x1 + x3) / 2.0, (y1 + y3) / 2.0), 0.0

        cx = (C * E - B * F) / det
        cy = (A * F - C * D) / det
        r = math.hypot(cx - x1, cy - y1)
        return Point2D(cx, cy), r

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        while angle < 0:
            angle += 2 * math.pi
        while angle >= 2 * math.pi:
            angle -= 2 * math.pi
        return angle

    def generate_arc_points(self, start: Point2D, way: Point2D, end: Point2D, num_points: int = 30) -> List[Point2D]:
        center, radius = self._circle_center_by_3points(start, way, end)
        if radius == 0:
            return self.generate_line_points(start, end, num_points)

        sa = math.atan2(start.y - center.y, start.x - center.x)
        wa = math.atan2(way.y - center.y, way.x - center.x)
        ea = math.atan2(end.y - center.y, end.x - center.x)

        sa = self._normalize_angle(sa)
        wa = self._normalize_angle(wa)
        ea = self._normalize_angle(ea)

        angles: List[float]
        # 选择包含 way 的弧段方向
        if sa <= ea:
            if wa >= sa and wa <= ea:
                step = (ea - sa) / (num_points - 1)
                angles = [sa + i * step for i in range(num_points)]
            else:
                ea += 2 * math.pi
                step = (ea - sa) / (num_points - 1)
                angles = [sa + i * step for i in range(num_points)]
        else:
            if wa >= sa or wa <= ea:
                ea += 2 * math.pi
                step = (ea - sa) / (num_points - 1)
                angles = [sa + i * step for i in range(num_points)]
            else:
                sa += 2 * math.pi
                step = (sa - ea) / (num_points - 1)
                angles = [sa - i * step for i in range(num_points)]

        points: List[Point2D] = []
        for ang in angles:
            x = center.x + radius * math.cos(ang)
            y = center.y + radius * math.sin(ang)
            points.append(Point2D(x, y))
        return points

    def generate_line_points(self, start: Point2D, end: Point2D, num_points: int = 30) -> List[Point2D]:
        pts: List[Point2D] = []
        for i in range(num_points):
            t = i / (num_points - 1) if num_points > 1 else 0.0
            x = start.x + t * (end.x - start.x)
            y = start.y + t * (end.y - start.y)
            pts.append(Point2D(x, y))
        return pts

    def points_to_linestring(self, points: List[Point2D]) -> str:
        coords = ", ".join([f"{p.x} {p.y}" for p in points])
        return f"LINESTRING ({coords})"

    def generate_uturn_curve(self, start_str: str, way_str: str, end_str: str, num_points: int = 30) -> str:
        s = self.parse_point_string(start_str)
        w = self.parse_point_string(way_str)
        e = self.parse_point_string(end_str)
        pts = self.generate_arc_points(s, w, e, num_points=num_points)
        return self.points_to_linestring(pts)


def main():
    parser = argparse.ArgumentParser(description="根据起点/途径点/终点(2D)生成平滑半圆曲线，输出LINESTRING")
    parser.add_argument("--start", type=str, default="Point START(117.27969983419898,39.696169691823016)", help="起点，格式如：Point START(x,y)")
    parser.add_argument("--way", type=str, default="Point WAY(117.27965038,39.69622787)", help="途径点，格式如：Point WAY(x,y)")
    parser.add_argument("--end", type=str, default="Point END(117.27960469236841,39.6961698111221)", help="终点，格式如：Point END(x,y)")
    parser.add_argument("--num_points", type=int, default=30, help="生成弧线上点的数量（越大越平滑）")
    args = parser.parse_args()

    gen = UTurnCurveGenerator2D()

    print("2D 掉头曲线生成工具")
    print("使用参数：")
    print(f"起点: {args.start}")
    print(f"途径点: {args.way}")
    print(f"终点: {args.end}")
    print(f"点数: {args.num_points}")
    print()

    linestr = gen.generate_uturn_curve(args.start, args.way, args.end, num_points=args.num_points)

    print("生成的LINESTRING:")
    print(linestr)

    out_path = "/home/ykzx/0_OffLineMap/offlinemap/0_tool/uturn_curve_2d_output.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(linestr)
    print(f"结果已保存到: {out_path}")


if __name__ == "__main__":
    main()