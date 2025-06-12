true = True
store_suffix = ""


def tesfunc(true, store_suffix):
    for i in range(2):
        store_suffix += f" {'BASE' if true else 'DOUBLE'} FLOW SUCCESS"
        test = f"successfully created{store_suffix}"
        true = False
    return test


result = tesfunc(true, store_suffix)

print(result)
