import re
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

GRAPH_DIR = Path("./experiments/graphs")


# ----------------------------------------------------------------------
# Ask for the files
# ----------------------------------------------------------------------

print("Enter the names of the CSV files to compare.")
print("Separate multiple filenames with spaces.")
print("The .csv extension is added automatically.")

filenames = input("> ").split()

if not filenames:
    print("No files were provided.")
    exit()


# ----------------------------------------------------------------------
# Read all files
# ----------------------------------------------------------------------

data = {}

for name in filenames:

    # Automatically add .csv
    filename = name + ".csv"
    filepath = GRAPH_DIR / filename

    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        continue

    file_data = {}

    with open(filepath, "r", encoding="utf-8") as f:

        for line in f:

            # Skip header and separator
            if line.startswith("Instance") or line.startswith("-"):
                continue

            line = line.strip()

            if not line:
                continue

            # Example:
            #
            # ACCIONA              37 / 40     1.3131954669952393
            # (0.015, 0.015)       (0, 0)

            match = re.match(
                r"^(\S+)\s+\d+\s*/\s*\d+\s+([0-9.eE+-]+)",
                line
            )

            if match:
                instance = match.group(1)
                time = float(match.group(2))

                file_data[instance] = time

    data[name] = file_data


if not data:
    print("No valid CSV files were found.")
    exit()


# ----------------------------------------------------------------------
# Obtain all instances
# ----------------------------------------------------------------------

instances = []

for file_data in data.values():

    for instance in file_data:

        if instance not in instances:
            instances.append(instance)


# ----------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------

plt.figure(figsize=(12, 6))

for name, file_data in data.items():

    x = []
    y = []

    for i, instance in enumerate(instances):

        if instance in file_data:
            x.append(i)
            y.append(file_data[instance])

    plt.plot(
        x,
        y,
        marker="o",
        label=name
    )


plt.xticks(
    range(len(instances)),
    instances,
    rotation=45,
    ha="right"
)

plt.xlabel("Instance")
plt.ylabel("Solving time (seconds)")
plt.title("Solving time")

plt.grid(True, axis="y")
plt.legend()

plt.tight_layout()


# ----------------------------------------------------------------------
# Save
# ----------------------------------------------------------------------

output_name = input("Enter the name for the resulting PNG file: ").strip()

if not output_name:
    output_name = "solving_times"

# Remove .png if the user included it
if output_name.lower().endswith(".png"):
    output_name = output_name[:-4]

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

output = GRAPH_DIR / f"{output_name}_{timestamp}.png"

plt.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print()
print(f"Saved plot to: {output}")