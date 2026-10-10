import re
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

GRAPH_DIR = Path("./experiments/graphs")
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

# Colors assigned to input files in order
LINE_COLORS = [
    "red",
    "orange",
    "gold",
    "lime",
    "green",
    "lightblue",
    "blue",
    "purple",
    "pink",
    "grey",
    "black",
]


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


# Add .csv extension if necessary
filenames = [
    filename if filename.lower().endswith(".csv")
    else filename + ".csv"
    for filename in filenames
]

# Look for the files in GRAPH_DIR
filepaths = [GRAPH_DIR / filename for filename in filenames]


# ----------------------------------------------------------------------
# Read the files
# ----------------------------------------------------------------------

data = {}

for filename, filepath in zip(filenames, filepaths):

    if not filepath.exists():
        print(f"File not found: {filepath}")
        exit()

    instances = []
    qualities = []

    with open(filepath, "r", encoding="utf-8") as file:

        for line in file:
            line = line.strip()

            match = re.match(
                r"^(\S+)\s+\d+\s*/\s*\d+\s+[\d.]+\s+"
                r"(?:\*\*)?([\d.]+)%(?:\*\*)?\s+\[",
                line
            )

            if match:
                instance = match.group(1)
                quality = float(match.group(2))

                instances.append(instance)
                qualities.append(quality)

    if not instances:
        print(f"No data found in: {filepath}")
        exit()

    data[filename] = dict(zip(instances, qualities))


# ----------------------------------------------------------------------
# Create graph
# ----------------------------------------------------------------------

# Use the instance order from the first file
instances = list(data[filenames[0]].keys())

x = np.arange(len(instances))

plt.figure(
    figsize=(max(12, len(instances) * 0.3), 7)
)


# Create lines
for i, filename in enumerate(filenames):

    values = [
        data[filename].get(instance, np.nan)
        for instance in instances
    ]

    # Use the corresponding rainbow color
    color = LINE_COLORS[i]

    plt.plot(
        x,
        values,
        marker="o",
        linewidth=1.5,
        color=color,
        label=Path(filename).stem,
        zorder=2
    )


# ----------------------------------------------------------------------
# Formatting
# ----------------------------------------------------------------------

# 50% reference line
# zorder=3 ensures it is rendered ON TOP of the lines.
plt.axhline(
    y=50,
    color="red",
    linestyle=":",
    alpha=0.7,
    linewidth=1.5,
    zorder=3
)

plt.xlabel("Instance")
plt.ylabel("Predictive Quality (%)")

plt.xticks(
    x,
    instances,
    rotation=90
)

plt.ylim(0, 100)

if len(filenames) > 1:
    plt.legend()

plt.grid(
    axis="y",
    alpha=0.2,
    zorder=1
)

plt.tight_layout()


# ----------------------------------------------------------------------
# Ask for output filename
# ----------------------------------------------------------------------

print()
print("Enter the name of the output PNG file.")

output_name = input("> ").strip()

if not output_name:
    print("No output filename was provided.")
    exit()

if not output_name.lower().endswith(".png"):
    output_name += ".png"

output_path = GRAPH_DIR / output_name


# ----------------------------------------------------------------------
# Save graph
# ----------------------------------------------------------------------

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(f"Graph saved to: {output_path}")

# Cadical300 cryptominisat5 Glucose421 Kissat404 Minisat22 -> solver
# no_redund redund -> redundancies
# pairwise sequential sortnetwrk cardnetwrk bitwise ladder totalizer mtotalizer kmtotalizer -> card_encodings
# no_pblib pblib -> pblib
# optimal_uv_1 optimal_uv_2 optimal_uv_3 optimal_uv_4 optimal_uv_5 -> optimal_uv
# final_res -> final_res final_res_2
# n4 n5 n6 n7 n8 n9 n10 -> n_qual n_qual_2 n_time n_time_2
# m10 m15 m20 m25 m30 m35 m40 -> m_qual m_qual_2 m_time m_time_2