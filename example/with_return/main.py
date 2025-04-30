import dis

from inline.inline_runtime import inline


class Point:
    x: int
    y: int

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def add_slow(p: Point, q: Point) -> int:
    p.x += q.x
    p.y += q.y
    return sum([p.x, p.y, q.x, q.y])


@inline
def add_fast(p: Point, q: Point) -> int:
    p.x += q.x
    p.y += q.y
    return sum([p.x, p.y, q.x, q.y])


def slow_caller() -> int:
    point_a = Point(1, 2)
    point_b = Point(3, 4)
    return add_slow(point_a, point_b)


def fast_caller() -> int:
    point_a = Point(1, 2)
    point_b = Point(3, 4)
    return add_fast(point_a, point_b)


def main():
    dis.dis(slow_caller)
    print("-" * 100)
    dis.dis(fast_caller)
