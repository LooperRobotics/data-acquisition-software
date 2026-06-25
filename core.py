"""
core.py — pure-Python logic for traj_score (no ROS2 dependencies).
"""

import math

DEFAULT_TOPIC = "/camera/camera/vio_image_cov"
DEFAULT_REF_COV = 1e-3

# (min_score, label) — first match wins
QUALITY_TIERS = [
    (90, "Excellent"),
    (70, "Good"),
    (50, "Fair"),
    (0,  "Poor"),
]


def covariance_trace(cov36: list) -> float:
    """Sum of the diagonal of a 6×6 row-major covariance matrix."""
    return sum(cov36[i * 7] for i in range(6))


def percentile(sorted_data: list, p: float) -> float:
    n = len(sorted_data)
    if n == 0:
        return 0.0
    k = (n - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, n - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (k - lo)


def quality_label(score: float) -> str:
    for threshold, label in QUALITY_TIERS:
        if score >= threshold:
            return label
    return "Poor"


def compute_stats(traces: list, ref_cov: float) -> dict:
    n = len(traces)
    mean = sum(traces) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in traces) / n)
    s = sorted(traces)
    # score driven by worst-case pose: one covariance spike tanks the whole trajectory
    score = min(100.0, ref_cov / s[-1] * 100.0)
    return {
        "n_poses":    n,
        "mean_trace": mean,
        "std_trace":  std,
        "min_trace":  s[0],
        "max_trace":  s[-1],
        "p50_trace":  percentile(s, 50),
        "p90_trace":  percentile(s, 90),
        "p99_trace":  percentile(s, 99),
        "ref_cov":    ref_cov,
        "score":      round(score, 2),
        "quality":    quality_label(score),
    }


def print_report(stats: dict, bag_path: str, topic: str) -> None:
    W = 54
    print("=" * W)
    print("  Trajectory Quality Report")
    print(f"  Bag   : {bag_path}")
    print(f"  Topic : {topic}")
    print("-" * W)
    print(f"  Poses processed  : {stats['n_poses']}")
    print(f"  Mean cov trace   : {stats['mean_trace']:.6e}")
    print(f"  Std  cov trace   : {stats['std_trace']:.6e}")
    print(f"  Min  cov trace   : {stats['min_trace']:.6e}")
    print(f"  Max  cov trace   : {stats['max_trace']:.6e}")
    print(f"  p50  cov trace   : {stats['p50_trace']:.6e}")
    print(f"  p90  cov trace   : {stats['p90_trace']:.6e}")
    print(f"  p99  cov trace   : {stats['p99_trace']:.6e}")
    print("-" * W)
    print(f"  Reference cov    : {stats['ref_cov']:.6e}  (= score 100)")
    print(f"  Score            : {stats['score']:.1f} / 100  [{stats['quality']}]  (driven by max trace)")
    print("=" * W)
