import os
from collections import deque

INSTANCES = r"./cut_instances"

for filename in os.listdir(INSTANCES):

    if filename.endswith(".std"):
        stock = filename[:-4]

        with open(os.path.join(INSTANCES, filename), "r") as file1, \
             open(os.path.join(INSTANCES, stock + "_cut.std"), "w") as file2:

            last_1000 = deque(maxlen=1000)

            for line in file1:
                if len(last_1000) == 1000:
                    print(last_1000.popleft(), end="", file=file2)

                last_1000.append(line)