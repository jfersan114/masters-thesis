import re
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

GRAPH_DIR = Path("./experiments/graphs")
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

# Colors assigned to files according to their input order
COLORS = [
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
    "black"
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
# Check number of files against available colors
# ----------------------------------------------------------------------

if len(filenames) > len(COLORS):
    print(
        f"Too many files. A maximum of {len(COLORS)} files "
        "can be displayed with the predefined colors."
    )
    exit()


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
# Sort each file independently by quality
#
# Higher quality = better performance.
#
# Therefore:
#
#     x = 1 -> highest quality instance
#     x = 2 -> second-highest quality instance
#     x = 3 -> third-highest quality instance
#     ...
#
# The same x-axis position may represent a different instance
# for each file.
# ----------------------------------------------------------------------

sorted_data = {}

for filename, file_data in data.items():

    sorted_data[filename] = sorted(
        file_data.items(),
        key=lambda item: item[1],
        reverse=True
    )


# ----------------------------------------------------------------------
# Create graph
# ----------------------------------------------------------------------

max_instances = max(
    len(file_data)
    for file_data in sorted_data.values()
)

# X-axis represents the rank within each file
x = np.arange(1, max_instances + 1)

plt.figure(
    figsize=(max(12, max_instances * 0.3), 7)
)


# ----------------------------------------------------------------------
# Create lines
# ----------------------------------------------------------------------

for file_index, (filename, sorted_instances) in enumerate(
    sorted_data.items()
):

    positions = np.arange(
        1,
        len(sorted_instances) + 1
    )

    values = [
        quality
        for instance, quality in sorted_instances
    ]

    plt.plot(
        positions,
        values,
        marker="o",
        linewidth=1.5,
        color=COLORS[file_index],
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

plt.xlabel("Instance rank (highest quality → lowest quality)")
plt.ylabel("Predictive Quality (%)")

plt.xticks(
    x
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