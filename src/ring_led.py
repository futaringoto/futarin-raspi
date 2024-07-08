import os
import sys
import pickle
counter = 0
# while True:
#     input_msg = input()
#     with open('./ledtest.log', 'a') as f:
#         f.write(f"{input_msg}, {counter}")
#     counter += 1
#     print(counter)
class Led():
    def __init__(self) -> None:
        pass
    def flash(self):
        pass
    def check_sudo(self):
        print(os.geteuid())
if __name__ == "__main__":
    led = Led()
    with open('ledtest.pickle', 'wb') as f:
        pickle.dump(led, f)
