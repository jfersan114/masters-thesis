import os
import sys
import subprocess
import re
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timezone

debug_dir = Path("register")
debug_dir.mkdir(exist_ok=True)

INSTANCES = r"./instances"
SOLVER = r"./main-cut.py"
results = []
timeouts = []
errors = []
DONE = []
#TO_DO = ["ACCIONA.std", "ACERINOX.std", "ACS.std", "ATRESMEDIA.std", "AZKOYEN.std", "BANKINTER.std", "BBVA.std", "BODEGAS_RIOJANAS.std", "CAF.std", "CIE.std"]
#TO_DO = ["EBRO_FOODS.std", "ELECNOR.std", "ENAGAS.std", "ENCE.std", "ENDESA.std", "FAES.std", "FCC.std", "FERROVIAL.std", "IBERDROLA.std", "IBERPAPEL.std"]
#TO_DO = ["INDITEX.std", "INDRA.std", "LINGOTES.std", "MAPFRE.std", "MELIA.std", "MIQUEL_COSTA.std", "MONTEBALITO.std", "NATURGY.std", "NICOLAS_CORREA.std", "OCCIDENT.std"]
#TO_DO = ["PHARMA_MAR.std", "PROSEGUR.std", "REDEIA.std", "REIG_JOFRE.std", "REPSOL.std", "SABADELL.std", "SACYR.std", "SANTANDER.std", "TELEFONICA.std", "TUBACEX.std"]
#TO_DO = ["TUBOS_REUNIDOS.std", "VIDRALA.std", "VISCOFAN.std"]
TO_DO = "all"
pairs = []
u_v_list = []

if not os.path.exists("./register/results.csv"):
    f = open(r"./register/results.csv", "w")
    print("Instance         |   Ratio   |         Time       |      Pred. Qual.     |     (u,v)\n----------------------------------------------------------------------------------\n", file=f)
    f.close()

with open(r"./register/results.csv") as f:
    for line in f:
        if not line.startswith("Instance") and not line.startswith("---"):
            line = line.split()
            if line != []:
                DONE.append(line[0] + ".std")

for filename in os.listdir(INSTANCES):

    if filename.endswith(".std") and filename not in DONE and (filename in TO_DO or TO_DO == "all" ):

        instance = filename[:-4]

        print(f"Solving {instance}...")
        
        try:
            result = subprocess.run(
                [sys.executable, SOLVER],
                input=instance,
                capture_output=True,
                text=True,
                timeout=3600
            )

            if result.returncode != 0:
                errors.append(instance)
                print(f"\t{instance} caught an error.")
                print(f"\tReturn code: {result.returncode}")
                print("\tstdout:")
                print(result.stdout)
                print("\tstderr:")
                print(result.stderr)
                continue

        except subprocess.TimeoutExpired:
            print(f"\t{instance} timed out.")
            timeouts.append(instance)
            continue

        print(f"\t{instance} solved.")

        time_value = None
        ratio_value = None
        u_v_pair = None

        for line in result.stdout.splitlines():

            if line.startswith("Total time spent solving the problem:"):
                time_value = line.split(":")[-1]

            elif line.startswith("With best guessing_rate:"):
                ratio_value = line.split(":")[-1]

            elif line.startswith("Optimal (u,v) list:"):
                pairs = re.findall( r'\(\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\)', line )
                u_v_list.extend((float(u), float(v)) for u, v in pairs)

            elif line.startswith("Obtained quality of the automaton:"):
                match = re.search(r'=\s*([\d.]+%)', line)
                if match:
                    quality_value = match.group(1)

        results.append( [ instance, ratio_value, time_value, quality_value, pairs] )


with open("./register/results.csv", "a") as f:

    for line in results:
        tabs = ""
        for i in range(5 - (len(line[0])//4)):
            tabs += "\t"
        print(f"{line[0]}" + tabs + f"{line[1]}" + f"\t {round(float(line[2]),2)}" + f"\t\t\t\t{line[3]}" + f"\t\t\t {line[4]}", file= f)
    
    for instance in timeouts:
        print(instance + "\t\t\t\t\t\t\tTIMED OUT", file= f)

    for instance in errors:
        print(instance + "\t\t\t\t\t\t\tERROR", file= f)


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

def sort_from_third_line():
    with open(r"./register/results.csv", "r", encoding="utf-8") as f:
        lines = f.readlines()

    lines[2:] = sorted(lines[2:])

    with open(r"./register/results.csv", "w", encoding="utf-8") as f:
        f.writelines(lines)

if __name__ == "__main__":
    sort_from_third_line()


print("Finished.")