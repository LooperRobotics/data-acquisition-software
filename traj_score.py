#!/usr/bin/python3
"""
traj_score — trajectory quality evaluator for VIO / SLAM systems.

Reads PoseWithCovarianceStamped messages from a ROS2 bag, computes the
6x6 covariance trace for each pose, and summarises trajectory uncertainty
as a 0–100 quality score:

    score = min(100, ref_cov / max_trace × 100)

Higher score = tighter uncertainty = better VIO/SLAM performance.

Usage:
    traj_score <bag_path> [OPTIONS]

Requires:
    source /opt/ros/humble/setup.bash
"""

import argparse
import json
import sys
from pathlib import Path

# Allow running as a symlink from /usr/local/bin
sys.path.insert(0, str(Path(__file__).resolve().parent))

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

from core.traj_core import DEFAULT_TOPIC, DEFAULT_REF_COV, covariance_trace, compute_stats, print_report


def open_reader(bag_path: str, topic: str) -> rosbag2_py.SequentialReader:
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=bag_path, storage_id=""),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr",
            output_serialization_format="cdr",
        ),
    )
    reader.set_filter(rosbag2_py.StorageFilter(topics=[topic]))
    return reader


def get_topic_type(reader: rosbag2_py.SequentialReader, topic: str) -> str | None:
    for t in reader.get_all_topics_and_types():
        if t.name == topic:
            return t.type
    return None


def collect_traces(
    reader: rosbag2_py.SequentialReader,
    topic: str,
    msg_type,
    verbose: bool,
) -> list:
    traces = []
    while reader.has_next():
        t_name, raw, _stamp = reader.read_next()
        if t_name != topic:
            continue
        msg = deserialize_message(raw, msg_type)
        trace = covariance_trace(list(msg.pose.covariance))
        traces.append(trace)
        if verbose:
            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            print(f"  [{len(traces):6d}]  t={stamp:.3f}  trace={trace:.6e}")
    return traces


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="traj_score",
        description="Evaluate VIO/SLAM trajectory quality from a ROS2 bag.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("bag_path", help="Path to the ROS2 bag directory or .db3 file.")
    p.add_argument(
        "--topic", "-t",
        default=DEFAULT_TOPIC,
        help=f"Topic name (default: {DEFAULT_TOPIC})",
    )
    p.add_argument(
        "--ref-cov", "-r",
        type=float,
        default=DEFAULT_REF_COV,
        help=(
            f"Covariance trace that maps to score 100 (default: {DEFAULT_REF_COV}). "
            "Tune to your system's expected best-case trace."
        ),
    )
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Print per-pose trace values.")
    p.add_argument("--list-topics", "-l", action="store_true",
                   help="List all topics in the bag and exit.")
    p.add_argument("--json", "-j", metavar="FILE",
                   help="Save full results to a JSON file.")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    try:
        reader = open_reader(args.bag_path, args.topic)
    except Exception as e:
        print(f"Error opening bag '{args.bag_path}': {e}", file=sys.stderr)
        sys.exit(1)

    if args.list_topics:
        print("Topics in bag:")
        for t in reader.get_all_topics_and_types():
            print(f"  {t.name}  [{t.type}]")
        return

    topic_type_str = get_topic_type(reader, args.topic)
    if topic_type_str is None:
        print(f"Topic '{args.topic}' not found in bag.", file=sys.stderr)
        print("Available topics:", file=sys.stderr)
        for t in reader.get_all_topics_and_types():
            print(f"  {t.name}  [{t.type}]", file=sys.stderr)
        sys.exit(1)

    msg_type = get_message(topic_type_str)
    print(f"Reading '{args.topic}'  [{topic_type_str}]")

    traces = collect_traces(reader, args.topic, msg_type, args.verbose)

    if not traces:
        print("No messages found on this topic.", file=sys.stderr)
        sys.exit(1)

    stats = compute_stats(traces, args.ref_cov)
    print_report(stats, args.bag_path, args.topic)

    if args.json:
        payload = {
            "bag_path": str(Path(args.bag_path).resolve()),
            "topic": args.topic,
            **stats,
        }
        with open(args.json, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"\nResults saved → {args.json}")


if __name__ == "__main__":
    main()
