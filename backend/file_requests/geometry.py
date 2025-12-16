import math
from typing import List, Tuple

class Point:
    """Точка в двумерном пространстве"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other: 'Point') -> 'Point':
        """Сложение двух точек"""
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        """Вычитание двух точек"""
        return Point(self.x - other.x, self.y - other.y)
    
    def __eq__(self, other: 'Point') -> bool:
        """Проверка на равенство"""
        return self.x == other.x and self.y == other.y
    
    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"
    
    def dot(self, other: 'Point') -> float:
        """Скалярное произведение"""
        return self.x * other.x + self.y * other.y
    
    def perp(self) -> 'Point':
        """Перпендикулярный вектор"""
        return Point(-self.y, self.x)


class Polygon:
    """Выпуклый многоугольник"""
    def __init__(self, points: List[Point]):
        """
        Args:
            points: Список точек в порядке обхода (по или против часовой стрелки)
        """
        self.points = points
    
    def __repr__(self) -> str:
        return f"Polygon({self.points})"
    
    @classmethod
    def from_rectangle(cls, bottom_left: Point, width: float, height: float) -> 'Polygon':
        """
        Создает прямоугольный полигон из левой нижней точки, ширины и высоты
        
        Args:
            bottom_left: Левая нижняя точка
            width: Ширина прямоугольника
            height: Высота прямоугольника
        
        Returns:
            Прямоугольный полигон (точки в порядке против часовой стрелки)
        """
        points = [
            bottom_left,
            Point(bottom_left.x + width, bottom_left.y),
            Point(bottom_left.x + width, bottom_left.y + height),
            Point(bottom_left.x, bottom_left.y + height)
        ]
        return cls(points)
    
    def get_edges(self) -> List[Point]:
        """Возвращает векторы ребер полигона"""
        edges = []
        n = len(self.points)
        for i in range(n):
            edge = self.points[(i + 1) % n] - self.points[i]
            edges.append(edge)
        return edges
    
    def get_axes(self) -> List[Point]:
        """Возвращает нормали к ребрам (оси для проекции в SAT)"""
        edges = self.get_edges()
        axes = []
        for edge in edges:
            axis = edge.perp()
            length = math.sqrt(axis.x**2 + axis.y**2)
            if length > 0:
                axis.x /= length
                axis.y /= length
            axes.append(axis)
        return axes
    
    def project_onto_axis(self, axis: Point) -> Tuple[float, float]:
        """
        Проецирует полигон на ось и возвращает минимальную и максимальную проекции
        
        Args:
            axis: Ось для проекции (должна быть нормализована)
        
        Returns:
            Кортеж (min_proj, max_proj)
        """
        min_proj = float('inf')
        max_proj = float('-inf')
        
        for point in self.points:
            proj = point.dot(axis)
            min_proj = min(min_proj, proj)
            max_proj = max(max_proj, proj)
        
        return min_proj, max_proj
    
    def intersects(self, other: 'Polygon') -> bool:
        """
        Проверяет пересечение двух выпуклых полигонов с помощью Separating Axis Theorem
        
        Args:
            other: Другой полигон для проверки пересечения
        
        Returns:
            True если полигоны пересекаются, иначе False
        """
        for axis in self.get_axes():
            min1, max1 = self.project_onto_axis(axis)
            min2, max2 = other.project_onto_axis(axis)
            
            if max1 < min2 or max2 < min1:
                return False
        
        for axis in other.get_axes():
            min1, max1 = self.project_onto_axis(axis)
            min2, max2 = other.project_onto_axis(axis)
            
            if max1 < min2 or max2 < min1:
                return False
        
        return True


if __name__ == "__main__":
    rect1 = Polygon.from_rectangle(Point(0, 0), 5, 5)
    rect2 = Polygon.from_rectangle(Point(5.0, 5), 5, 5)
    
    print(f"Polygon 1: {rect1}")
    print(f"Polygon 2: {rect2}")
    print(f"Intersect: {rect1.intersects(rect2)}")
    
    rect3 = Polygon.from_rectangle(Point(0, 0), 2, 2)
    rect4 = Polygon.from_rectangle(Point(10, 10), 2, 2)
    
    print(f"\nPolygon 3: {rect3}")
    print(f"Polygon 4: {rect4}")
    print(f"Intersect: {rect3.intersects(rect4)}") 
    
    triangle = Polygon([
        Point(0, 0),
        Point(5, 0),
        Point(2.5, 5)
    ])
    
    print(f"\nTriangle: {triangle}")
    print(f"Triangle intersects rect1: {triangle.intersects(rect1)}")

class Car:
    def __init__(self, wheels: Polygon, bounding_box: Polygon, id: int):
        self.wheels = wheels
        self.bounding_box = bounding_box
        self.id = id

    def get_danger_level(self, danger_zone: Polygon) -> int:
        if danger_zone.intersects(self.wheels):
            return 2
        if danger_zone.intersects(self.bounding_box):
            return 1
        return 0
