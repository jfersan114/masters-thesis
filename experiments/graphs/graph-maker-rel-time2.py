import re
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

GRAPH_DIR = Path("./experiments/graphs")

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


# ----------------------------------------------------------------------
# Read all files
# ----------------------------------------------------------------------

data = {}
file_colors = {}

for name in filenames:

    # Automatically add .csv
    filename = name + ".csv"
    filepath = GRAPH_DIR / filename

    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        continue

    # Assign the color according to the order in which valid files
    # are parsed.
    color_index = len(file_colors)

    if color_index >= len(LINE_COLORS):
        print(
            f"ERROR: More than {len(LINE_COLORS)} valid files were provided. "
            "No color is available for this file."
        )
        continue

    file_colors[name] = LINE_COLORS[color_index]

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
            # The instance timed out / was aborted for this file.
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
# Sort each file independently
#
# Each file gets its own ranking:
#
#     1st = timeout (if any)
#     2nd = timeout (if any)
#     ...
#     then largest normalized execution time
#     ...
#     last = smallest normalized execution time
#
# A timeout is considered slower than every successful execution,
# so timeout instances are placed at the beginning of the ranking.
# ----------------------------------------------------------------------

sorted_data = {}

for name, file_data in normalized_data.items():

    # Instances that were not present in this file are considered
    # timed out / aborted.
    timed_out = [
        (instance, None)
        for instance, value in file_data.items()
        if value is None
    ]

    # Successful executions, from slowest to fastest.
    successful = sorted(
        [
            (instance, value)
            for instance, value in file_data.items()
            if value is not None
        ],
        key=lambda item: item[1],
        reverse=True
    )

    # Timeouts first, then successful executions.
    sorted_data[name] = timed_out + successful


# ----------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------

plt.figure(figsize=(12, 6))

for name, file_data in sorted_data.items():

    x = []
    y = []

    for position, (instance, value) in enumerate(file_data, start=1):
        x.append(position)
        y.append(value)

    plt.plot(
        x,
        y,
        marker="o",
        color=file_colors[name],
        label=name
    )


# X-axis now represents the ranking/order within each file
max_instances = max(
    len(file_data)
    for file_data in sorted_data.values()
)

plt.xticks(
    range(1, max_instances + 1)
)

plt.xlabel("Instance rank (slowest → fastest)")
plt.ylabel("Normalized solving time (%)")
plt.title("Normalized solving time by instance rank")

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

# Cadical300 cryptominisat5 Glucose421 Kissat404 Minisat22 -> solver
# no_redund redund -> redundancies
# pairwise sequential sortnetwrk cardnetwrk bitwise ladder totalizer mtotalizer kmtotalizer -> card_encodings
# no_pblib pblib -> pblib
# optimal_uv_1 optimal_uv_2 optimal_uv_3 optimal_uv_4 optimal_uv_5 -> optimal_uv
# final_res -> final_res final_res_2
# n4 n5 n6 n7 n8 n9 n10 -> n_qual n_qual_2 n_time n_time_2
# m10 m15 m20 m25 m30 m35 m40 -> m_qual m_qual_2 m_time m_time_2