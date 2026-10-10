"""Cluster (u,v) pairs from experiment graph CSV files with HDBSCAN.

The input files are expected under ./experiments/graphs and to contain rows
similar to:

    ACCIONA   39 / 40   2568.2538170814514   [('0.0021', '0.0127'), ...]
    ACERINOX                          TIMED OUT

Only the (u,v) pairs are used for clustering.  Quality, time, instance name,
and TIMED OUT rows are ignored.

Dependencies:
    pip install hdbscan numpy

Run directly with:
    python hdbscan_representatives.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timezone

try:
    import hdbscan
except ImportError as exc:
    raise SystemExit(
        "The 'hdbscan' package is required. Install it with: pip install hdbscan numpy"
    ) from exc


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

GRAPH_DIR = Path("./experiments/graphs")

# HDBSCAN parameters.  Change these if you want finer/coarser clusters.
MIN_CLUSTER_SIZE = 5
MIN_SAMPLES = None
CLUSTER_SELECTION_METHOD = "eom"

# Plot configuration.
PLOT_DPI = 300
PLOT_FIGSIZE = (7, 7)
POINT_SIZE = 8
REPRESENTATIVE_SIZE = 90
NOISE_SIZE = 6

# One actual data point is selected as the representative of each cluster.
# The representative is the point nearest that cluster's arithmetic centroid.


# Accept both single-quoted and double-quoted coordinates, e.g.
# ('0.0021', '0.0127') or ("0.0021", "0.0127")
PAIR_RE = re.compile(
    r"\(\s*['\"]([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)['\"]"
    r"\s*,\s*['\"]([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)['\"]\s*\)"
)


@dataclass(frozen=True)
class Point:
    """A parsed (u,v) pair together with its source information."""

    u: float
    v: float
    filename: str
    line_number: int
    instance: str


@dataclass(frozen=True)
class ClusterRepresentative:
    """Representative of one HDBSCAN cluster."""

    cluster_id: int
    u: float
    v: float
    cluster_size: int
    cluster_probability: float
    source_filename: str
    source_line: int
    source_instance: str


def _instance_from_line(line: str) -> str:
    """Best-effort extraction of the instance name from a result row."""

    # Everything before the quality/time columns is the instance name.
    # For normal result rows this captures names such as ACCIONA or BODEGAS_RIOJANAS.
    match = re.match(r"^\s*(.*?)\s+\d+\s*/\s*\d+\s+[-+]?\d", line)
    if match:
        return match.group(1).strip()

    # Timeout rows do not contain quality/time columns.
    timeout_match = re.match(r"^\s*(.*?)\s+TIMED\s+OUT\s*$", line, re.IGNORECASE)
    if timeout_match:
        return timeout_match.group(1).strip()

    return ""


def parse_file(filepath: Path) -> list[Point]:
    """Extract every (u,v) pair from one graph file.

    Pairs are kept indiscriminately, including duplicate coordinates.
    """

    points: list[Point] = []

    try:
        text = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # A fallback that is useful for files produced by older scripts.
        text = filepath.read_text(encoding="latin-1")

    for line_number, line in enumerate(text.splitlines(), start=1):
        pairs = PAIR_RE.findall(line)
        if not pairs:
            continue

        instance = _instance_from_line(line)
        for u_text, v_text in pairs:
            points.append(
                Point(
                    u=float(u_text),
                    v=float(v_text),
                    filename=filepath.name,
                    line_number=line_number,
                    instance=instance,
                )
            )

    return points


def load_points(filepaths: Iterable[Path]) -> list[Point]:
    """Load and concatenate all (u,v) pairs from the selected files."""

    all_points: list[Point] = []

    for filepath in filepaths:
        if not filepath.is_file():
            print(f"WARNING: file not found: {filepath}")
            continue

        points = parse_file(filepath)
        print(f"{filepath.name}: {len(points)} (u,v) pairs found")
        all_points.extend(points)

    return all_points


def choose_cluster_representative(
    coordinates: np.ndarray,
    labels: np.ndarray,
    probabilities: np.ndarray,
    cluster_id: int,
    points: list[Point],
) -> ClusterRepresentative:
    """Pick the actual point closest to the cluster centroid."""

    indices = np.flatnonzero(labels == cluster_id)
    cluster_coordinates = coordinates[indices]

    centroid = cluster_coordinates.mean(axis=0)
    distances = np.linalg.norm(cluster_coordinates - centroid, axis=1)
    representative_index = indices[int(np.argmin(distances))]

    source = points[int(representative_index)]

    # Use the membership probability of the selected actual point as a simple
    # indication of how strongly HDBSCAN associates it with its cluster.
    probability = float(probabilities[representative_index])

    return ClusterRepresentative(
        cluster_id=int(cluster_id),
        u=float(coordinates[representative_index, 0]),
        v=float(coordinates[representative_index, 1]),
        cluster_size=int(len(indices)),
        cluster_probability=probability,
        source_filename=source.filename,
        source_line=source.line_number,
        source_instance=source.instance,
    )


def cluster_points(
    points: list[Point],
    *,
    min_cluster_size: int = MIN_CLUSTER_SIZE,
    min_samples: int | None = MIN_SAMPLES,
    cluster_selection_method: str = CLUSTER_SELECTION_METHOD,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[ClusterRepresentative]]:
    """Cluster all points and return labels, probabilities and representatives.

    Returns:
        labels:
            HDBSCAN label for every point.  -1 means noise.
        probabilities:
            HDBSCAN membership strength for every point.
        coordinates:
            N x 2 array containing all input coordinates.
        representatives:
            One actual input point per discovered non-noise cluster.
    """

    if not points:
        raise ValueError("No (u,v) pairs were found in the selected files.")

    if min_cluster_size < 2:
        raise ValueError("min_cluster_size must be at least 2.")

    coordinates = np.asarray([(point.u, point.v) for point in points], dtype=float)

    if len(coordinates) < min_cluster_size:
        raise ValueError(
            f"Found only {len(coordinates)} points, but min_cluster_size is "
            f"{min_cluster_size}."
        )

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        cluster_selection_method=cluster_selection_method,
    )

    labels = clusterer.fit_predict(coordinates)
    probabilities = np.asarray(clusterer.probabilities_, dtype=float)

    cluster_ids = sorted(int(label) for label in set(labels) if label != -1)

    representatives = [
        choose_cluster_representative(
            coordinates,
            labels,
            probabilities,
            cluster_id,
            points,
        )
        for cluster_id in cluster_ids
    ]

    # Put the largest clusters first: these are usually the most representative
    # regions of the complete point cloud.
    representatives.sort(key=lambda rep: (-rep.cluster_size, rep.cluster_id))

    return labels, probabilities, coordinates, representatives


def print_all_points(points: list[Point]) -> None:
    """Print every parsed (u,v) pair in input order, without deduplication."""

    print("\n" + "=" * 78)
    print("ALL (u,v) PAIRS")
    print("=" * 78)
    print("[")

    for point in points:
        print(
            f"    ({point.u!r}, {point.v!r}), "
            f"# {point.filename}:{point.line_number} "
            f"{point.instance or '?'}"
        )

    print("]")


def print_results(
    points: list[Point],
    labels: np.ndarray,
    probabilities: np.ndarray,
    representatives: list[ClusterRepresentative],
) -> None:
    """Print the clustering summary and representative list."""

    total_points = len(points)
    noise_count = int(np.sum(labels == -1))
    cluster_ids = sorted(int(label) for label in set(labels) if label != -1)

    print("\n" + "=" * 78)
    print("HDBSCAN SUMMARY")
    print("=" * 78)
    print(f"Total (u,v) pairs : {total_points}")
    print(f"Clusters found    : {len(cluster_ids)}")
    print(f"Noise points      : {noise_count}")

    if cluster_ids:
        clustered_count = total_points - noise_count
        print(f"Clustered points  : {clustered_count}")
        print(
            f"Cluster coverage : {100.0 * clustered_count / total_points:.2f}%"
        )

    print("\n" + "=" * 78)
    print("POSSIBLE REPRESENTATIVES")
    print("=" * 78)

    if not representatives:
        print("No non-noise clusters were found.")
        return

    print(
        f"{'Cluster':>7}  {'Size':>6}  {'u':>12}  {'v':>12}  "
        f"{'Prob.':>8}  Source"
    )
    print("-" * 78)

    for rep in representatives:
        source = (
            f"{rep.source_instance or '?'} "
            f"({rep.source_filename}:{rep.source_line})"
        )
        print(
            f"{rep.cluster_id:>7}  {rep.cluster_size:>6}  "
            f"{rep.u:>12.7f}  {rep.v:>12.7f}  "
            f"{rep.cluster_probability:>8.4f}  {source}"
        )

    print("\nRepresentatives as Python tuples:")
    print("[")
    for rep in representatives:
        print(f"    ({rep.u!r}, {rep.v!r}),")
    print("]")

    # Useful diagnostic: points HDBSCAN considered noise are deliberately not
    # represented in the main candidate list.
    if noise_count:
        noise_probabilities = probabilities[labels == -1]
        print(
            "\nNote: HDBSCAN marked "
            f"{noise_count} point(s) as noise; they are not included above."
        )


def compute_weighted_representative_average(
    representatives: list[ClusterRepresentative],
) -> tuple[list[tuple[tuple[float, float], int]], tuple[float, float] | None]:
    """Build ((u_i, v_i), k_i) entries and compute their weighted average.

    For every non-noise cluster i, the list contains its selected representative
    (u_i, v_i) and its cardinality k_i.  The weighted average is then computed
    using the cluster cardinalities as weights.

    Returns:
        representative_list:
            [((u_0, v_0), k_0), ((u_1, v_1), k_1), ...]
        weighted_average:
            (u', v'), or None if no clusters exist.
    """

    representative_list = [
        ((rep.u, rep.v), rep.cluster_size)
        for rep in representatives
    ]

    if not representative_list:
        return representative_list, None

    K = sum(k for (_, _), k in representative_list)

    weighted_u = sum(u * k for ((u, _), k) in representative_list) / K
    weighted_v = sum(v * k for ((_, v), k) in representative_list) / K

    return representative_list, (weighted_u, weighted_v)


def print_weighted_representative_average(
    representatives: list[ClusterRepresentative],
) -> None:
    """Print the weighted representative list and its weighted average."""

    representative_list, weighted_average = compute_weighted_representative_average(
        representatives
    )

    print("\n" + "=" * 78)
    print("WEIGHTED REPRESENTATIVES")
    print("=" * 78)

    if weighted_average is None:
        print("No non-noise clusters were found; weighted average cannot be computed.")
        return

    print("List of ((u_i, v_i), k_i):")
    print("[")
    for (u, v), k in representative_list:
        print(f"    (({u!r}, {v!r}), {k}),")
    print("]")

    K = sum(k for (_, _), k in representative_list)
    weighted_u, weighted_v = weighted_average

    print(f"\nK = {K}")
    print(
        "Weighted average (u', v') = "
        f"({weighted_u!r}, {weighted_v!r})"
    )


def save_cluster_plot(
    points: list[Point],
    labels: np.ndarray,
    representatives: list[ClusterRepresentative],
    weighted_average: tuple[float, float] | None,
) -> Path:
    """Save a PNG showing HDBSCAN clusters and their representatives.

    Every input point is plotted, including duplicate coordinates. Points
    belonging to the same HDBSCAN cluster share a color. HDBSCAN noise points
    (label -1) are shown in gray. Representatives are highlighted with star
    markers and annotated with their cluster number.
    """
    coordinates = np.asarray([(point.u, point.v) for point in points], dtype=float)

    output_file = (
        GRAPH_DIR
        / (
            "hdbscan_clusters "
            + str(datetime.now(timezone.utc))[:19].replace(":", "-")
            + ".png"
        )
    )

    fig, ax = plt.subplots(figsize=PLOT_FIGSIZE)

    cluster_ids = sorted(int(label) for label in set(labels) if label != -1)
    cmap = plt.get_cmap("tab20")
    cluster_colors = {
        cluster_id: cmap(index % cmap.N)
        for index, cluster_id in enumerate(cluster_ids)
    }

    for cluster_id in cluster_ids:
        mask = labels == cluster_id
        cluster_size = int(np.sum(mask))
        ax.scatter(
            coordinates[mask, 0],
            coordinates[mask, 1],
            s=POINT_SIZE,
            color=cluster_colors[cluster_id],
            label=f"Cluster {cluster_id} ({cluster_size} points)",
            alpha=0.75,
            edgecolors="none",
        )

    noise_mask = labels == -1
    if np.any(noise_mask):
        ax.scatter(
            coordinates[noise_mask, 0],
            coordinates[noise_mask, 1],
            s=NOISE_SIZE,
            color="lightgray",
            label=f"Noise ({int(np.sum(noise_mask))} points)",
            alpha=0.65,
            edgecolors="none",
        )

    for rep in representatives:
        ax.scatter(
            rep.u,
            rep.v,
            s=REPRESENTATIVE_SIZE,
            marker="*",
            color=cluster_colors[rep.cluster_id],
            edgecolor="black",
            linewidth=0.8,
            zorder=10,
        )
        ax.annotate(
            f"R{rep.cluster_id}",
            (rep.u, rep.v),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            fontweight="bold",
            zorder=11,
        )

    # Plot the weighted average of the cluster representatives.
    if weighted_average is not None:
        average_u, average_v = weighted_average
        ax.scatter(
            average_u, average_v,
            s=140, marker="X", color="black", edgecolor="white",
            linewidth=1.2, zorder=20,
            label=f"Weighted average ({average_u:.6f}, {average_v:.6f})",
        )

    if coordinates.size:
        min_x, max_x = float(np.min(coordinates[:, 0])), float(np.max(coordinates[:, 0]))
        min_y, max_y = float(np.min(coordinates[:, 1])), float(np.max(coordinates[:, 1]))
        margin_x = max((max_x - min_x) * 0.1, 0.01)
        margin_y = max((max_y - min_y) * 0.1, 0.01)
        if weighted_average is not None:
            average_u, average_v = weighted_average
            min_x = min(min_x, average_u)
            max_x = max(max_x, average_u)
            min_y = min(min_y, average_v)
            max_y = max(max_y, average_v)
            margin_x = max((max_x - min_x) * 0.1, 0.01)
            margin_y = max((max_y - min_y) * 0.1, 0.01)

        ax.set_xlim(max(0, min_x - margin_x), max_x + margin_x)
        ax.set_ylim(max(0, min_y - margin_y), max_y + margin_y)

    ax.set_xlabel("u")
    ax.set_ylabel("v")
    ax.set_title("HDBSCAN clusters of (u,v) pairs")
    ax.grid(True)
    ax.set_aspect("equal", adjustable="box")

    if cluster_ids or np.any(noise_mask):
        ax.legend(loc="best", fontsize=8)

    fig.savefig(output_file, dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)

    print(
        f"\\nSaved cluster plot with {len(points)} points and "
        f"{len(representatives)} representatives to {output_file}"
    )
    return output_file

def main() -> None:
    # ----------------------------------------------------------------------
    # Ask for the files
    # ----------------------------------------------------------------------

    print("Enter the names of the CSV files to compare.")
    print("Separate multiple filenames with spaces.")
    print("The .csv extension is added automatically.")

    filenames = input("> ").split()

    if not filenames:
        print("No files were provided.")
        raise SystemExit


    # Add .csv extension if necessary
    filenames = [
        filename if filename.lower().endswith(".csv")
        else filename + ".csv"
        for filename in filenames
    ]

    # Look for the files in GRAPH_DIR
    filepaths = [GRAPH_DIR / filename for filename in filenames]

    # ----------------------------------------------------------------------
    # Read all (u,v) pairs
    # ----------------------------------------------------------------------

    points = load_points(filepaths)

    if not points:
        print("No (u,v) pairs were found in the selected files.")
        raise SystemExit

    print(f"\nTotal pairs loaded: {len(points)}")
    print_all_points(points)

    # ----------------------------------------------------------------------
    # HDBSCAN
    # ----------------------------------------------------------------------

    try:
        labels, probabilities, _, representatives = cluster_points(points)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc

    print_results(points, labels, probabilities, representatives)

    # ----------------------------------------------------------------------
    # Weighted average of cluster representatives
    # ----------------------------------------------------------------------

    # Compute the weighted average once so it can be both printed and plotted.
    representative_list, weighted_average = compute_weighted_representative_average(
        representatives
    )

    # Print the weighted representatives and the weighted average.
    print_weighted_representative_average(representatives)

    # ----------------------------------------------------------------------
    # Plot clusters, representatives, and weighted average
    # ----------------------------------------------------------------------

    save_cluster_plot(points, labels, representatives, weighted_average)


if __name__ == "__main__":
    main()

# optimal_uv_1 optimal_uv_2 optimal_uv_3 optimal_uv_4 optimal_uv_5 -> optimal_uv_clusters