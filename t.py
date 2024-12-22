

def repeat(n:int):
    def wrapper(func):
        for rep in range(n):
            res = func()
            print(res)
    return wrapper

def say_hello():
    return 