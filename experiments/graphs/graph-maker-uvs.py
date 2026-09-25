import os
import ast
import re
import matplotlib.pyplot as plt
from datetime import datetime, timezone


FOLDER = r"./experiments/graphs"


# Ask the user for the CSV files
files_input = input(
    "Enter the names of the .csv files to process, separated by spaces: "
)

filenames = files_input.split()


# Set used to automatically remove duplicate points
u_v_set = set()


for filename in filenames:

    # Add .csv automatically if it was omitted
    if not filename.endswith(".csv"):
        filename += ".csv"

    filepath = os.path.join(FOLDER, filename)

    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue

    print(f"Processing {filename}...")

    with open(filepath, "r") as file:

        for line in file:

            # Ignore empty lines
            if not line.strip():
                continue

            # Ignore instances that timed out
            if "TIMED OUT" in line:
                continue

            # Find the list of (u,v) pairs
            match = re.search(r"(\[\(.*\)\])", line)

            if match:

                uv_string = match.group(1)

                try:
                    # Convert string representation into a Python list
                    uv_list = ast.literal_eval(uv_string)

                    # Add every point to the set
                    for u, v in uv_list:
                        u_v_set.add((float(u), float(v)))

                except (ValueError, SyntaxError):
                    print(f"Could not parse line:\n{line}")


# Convert set to list
u_v_list = list(u_v_set)


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

    # Save in the same folder as the input CSV files
    output_file = os.path.join(
        FOLDER,
        "optimal_uv_pairs "
        + str(datetime.now(timezone.utc))[:19]
        + ".png"
    )

    plt.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"Saved plot with {len(u_v_list)} unique points "
        f"to {output_file}"
    )

else:
    print("No (u,v) pairs were found.")