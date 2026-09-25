import os

INSTANCES = r"./cut_instances"

for filename in os.listdir(INSTANCES):

    if filename.endswith("_cut_cut.std"):

        os.remove("./cut_instances/" + filename)