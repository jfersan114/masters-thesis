import os
import sys
import subprocess
import ast
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timezone

debug_dir = Path("register")
debug_dir.mkdir(exist_ok=True)

INSTANCES = r"./instances"
SOLVER = r"./main.py"
results = []
timeouts = []
errors = []
DONE = []
u_v_list = []

if not os.path.exists("./register/results.csv"):
    f = open(r"./register/results.csv", "w")
    print("Instance         |   Quality  |         Time       |                  (u,v)\n-------------------------------------------------------------------------------------------------", file=f)
    f.close()

with open(r"./register/results.csv") as f:
    for line in f:
        if not line.startswith("Instance") and not line.startswith("---"):
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
                timeout=1000
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
        u_v_pair = None

        for line in result.stdout.splitlines():

            if line.startswith("Total time spent solving the problem:"):
                time_value = line.split(":")[-1]

            if line.startswith("With best guessing rate:"):
                quality_value = line.split(":")[-1]
            
            if line.startswith("(u,v) = "):
                u_v_pair = ast.literal_eval(line[len("(u,v) = "):].rstrip(":"))
                u_v_list.append(u_v_pair)

        results.append( [ instance, quality_value, time_value, u_v_pair ] )
    
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


# Plot all optimal (u,v) pairs
if u_v_list:
    x, y = zip(*u_v_list)

    # Compute adaptive limits
    min_x, max_x = min(x), max(x)
    min_y, max_y = min(y), max(y)

    # Add a 10% margin (or at least 0.01)
    margin_x = max((max_x - min_x) * 0.1, 0.01)
    margin_y = max((max_y - min_y) * 0.1, 0.01)

    plt.figure(figsize=(6, 6))
    plt.scatter(x, y, color="red", s=5)

    plt.xlim(max(0, min_x - margin_x), max_x + margin_x)
    plt.ylim(max(0, min_y - margin_y), max_y + margin_y)

    plt.xlabel("u")
    plt.ylabel("v")
    plt.title("Optimal (u,v) pairs")
    plt.grid(True)
    plt.gca().set_aspect("equal", adjustable="box")

    plt.savefig("./register/optimal_uv_pairs " + str(datetime.now(timezone.utc))[:19] + ".png", dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved plot with {len(u_v_list)} points to ./register/optimal_uv_pairs.png")
else:
    print("No (u,v) pairs were found.")


print("Finished.")