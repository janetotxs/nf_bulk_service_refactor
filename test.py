# remark = "IN_CHARGE: Success | EXTEND_FIRST_EXPIRY: Success | DATA: Failed | SMS: Success | VOICE: Success"

# # Convert string to dict
# test = remark.replace(" | ", ",").replace(": ", ",")
# lists = test.split(",")
# hashmap = {lists[i]: lists[i + 1] for i in range(0, len(lists), 2)}

# # Modify value
# hashmap["DATA"] = "Hotdog"

# # Convert dict back to original string format
# new_remark = " | ".join(f"{key}: {value}" for key, value in hashmap.items())
# print(new_remark)

test = None
dicts = {}

dicts.update(test)
# def loop():
#     retry = 1
#     max_retries = 2

#     while retry <= max_retries:
#         try:
#             if test["erer"] == 0:
#                 print("TEST")
#         except Exception as e:
#             if retry == max_retries:
#                 raise print(f"MAX RETIES REACH {e}")
#             print(f"Exception occurred: {retry}")
#             retry += 1


# def outer():
#     try:
#         print("trigger loop")
#         loop()
#     except Exception:
#         print("GOT THE ERROR")


# outer()
