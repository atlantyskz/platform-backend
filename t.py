

from typing import Callable


def repeat(n: int):

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                res = func(*args, **kwargs)
                print(res)
        return wrapper
    return decorator

@repeat(3)
def say_hello(string:str):
    return "Hi " + string

a = say_hello("sads")