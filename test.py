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

from test2 import Test2
from utils import helpers

damn = {}
t = Test2()
try:
    test = t.run()
except Exception:
    print("GOT ERROR")
pot = helpers.convert_string_hashmap(damn, "string")
print(pot)
print("LAGPA")
damn.update(test)
if pot:
    print("SADASD")
if t.rows:
    print("PASS")

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
