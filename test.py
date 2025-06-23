def inner():
    try:
        test["test"] = 32
    except:
        raise Exception("inner error!")


def outer():
    try:
        inner()
    except Exception as e:
        print(e)


outer()
