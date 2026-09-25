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
# Normalize times
#
# For each instance:
#
#     normalized time = time / maximum time * 100
#
# Therefore, the slowest solver for each instance is always at 100%.
# ----------------------------------------------------------------------

normalized_data = {}

for name, file_data in data.items():

    normalized_data[name] = {}

    for instance in instances:

        if instance not in file_data:
            normalized_data[name][instance] = None
            continue

        times = [
            other_data[instance]
            for other_data in data.values()
            if instance in other_data
        ]

        maximum = max(times)

        normalized_data[name][instance] = (
            file_data[instance] / maximum * 100
        )


# ----------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------

plt.figure(figsize=(12, 6))

for name, file_data in normalized_data.items():

    x = []
    y = []

    for i, instance in enumerate(instances):

        value = file_data[instance]

        if value is not None:
            x.append(i)
            y.append(value)

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
plt.ylabel("Normalized solving time (%)")
plt.title("Normalized solving time")

plt.ylim(0, 105)
plt.grid(True, axis="y")
plt.legend()

plt.tight_layout()


# ----------------------------------------------------------------------
# Save
# ----------------------------------------------------------------------

output_name = input("Enter the name for the resulting PNG file: ").strip()

if not output_name:
    output_name = "normalized_times"

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