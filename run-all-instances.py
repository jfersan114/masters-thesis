import os
import sys
import subprocess

INSTANCES = r"./instances"
SOLVER = r"./EXECUTABLE_pysat-v1.1.py"
results = []
timeouts = []
errors = []
DONE = []

with open(r"./register/results.csv") as f:
    for line in f:
        if not line.startswith("Instance"):
            line = line.split()
            if line != []:
                DONE.append(line[0] + ".std")

count = 0

for filename in os.listdir(INSTANCES):

    if filename.endswith(".std") and filename not in DONE and count < 10:

        instance = filename[:-4]

        print(f"Solving {instance}...")

        try:
            result = subprocess.run(
                [sys.executable, SOLVER],
                input=instance,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                errors.append(instance)
                print(f"\t{instance} catched an error.")
                continue

        except subprocess.TimeoutExpired:
            print(f"\t{instance} timed out.")
            timeouts.append(instance)
            count += 1
            continue

        print(f"\t{instance} solved.")

        time_value = None
        quality_value = None
        u_v_tuple = None

        for line in result.stdout.splitlines():

            if line.startswith("Total time spent solving the problem:"):
                time_value = line.split(":")[-1]

            if line.startswith("With best guessing rate:"):
                quality_value = line.split(":")[-1]

            if line.startswith("(u,v) = "):
                u_v_tuple = line.split(" = ")[-1][:-1]

        results.append( [ instance, quality_value, time_value, u_v_tuple ] )
    
        count += 1

with open("./register/results.csv", "a") as f:

    for line in results:
        tabs = ""
        for i in range(5 - (len(line[0])//4)):
            tabs += "\t"
        print(f"{line[0]}" + tabs + f"{line[1]}" + f"{line[2]}" + f"\t {line[3]}", file= f)
    
    for instance in timeouts:
        print(instance + "\t\t\t\t\t\t\tTIMED OUT")

    for instance in errors:
        print(instance + "\t\t\t\t\t\t\tERROR")


print("Finished.")