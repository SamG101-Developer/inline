from inline.inline_runtime import inline, inline_cls
import dis


@inline_cls
class MyClass:
    a: int
    b: int

    def __init__(self, a: int, b: int) -> None:
        self.a = a
        self.b = b

    def add_slow(self) -> int:
        return self.a + self.b

    @inline
    def add_fast(self) -> int:
        return self.a + self.b

    def call_slow(self) -> int:
        x = self.add_slow()
        return x

    def call_fast(self) -> int:
        x = self.add_fast()
        return x


def main() -> None:
    dis.dis(MyClass.call_slow)
    print("-" * 100)
    dis.dis(MyClass.call_fast)
