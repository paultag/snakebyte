from snakebyte import Snakebyte


x = Snakebyte("hello.snake").compile()

def foo():
    print("Hello!")

foo()
foo.__code__ = x
foo()
