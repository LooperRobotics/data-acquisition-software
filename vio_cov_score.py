#!/usr/bin/env /usr/bin/python3
"""
CLI tool to evaluate VIO covariance quality from a ROS2 bag file.

Reads all PoseWithCovarianceStamped messages on a given topic, computes the
trace of the 6x6 covariance matrix for each pose, and reports the average
as a score.  Lower score = tighter uncertainty = better VIO performance.

Usage:
    python3 vio_cov_score.py <bag_path> [OPTIONS]

Requires: source /opt/ros/humble/setup.bash
"""

import argparse
import sys

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


DEFAULT_TOPIC = "/camera/camera/vio_image_cov"


def covariance_trace(cov36: list) -> float:
    """Return the trace of a 6x6 row-major covariance matrix (sum of diagonal)."""
    return sum(cov36[i * 7] for i in range(6))


def open_reader(bag_path: str, topic: str) -> rosbag2_py.SequentialReader:
    reader = rosbag2_py.SequentialReader()
    storage_options = rosbag2_py.StorageOptions(uri=bag_path, storage_id="")
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )
    reader.open(storage_options, converter_options)
    storage_filter = rosbag2_py.StorageFilter(topics=[topic])
    reader.set_filter(storage_filter)
    return reader


def get_topic_type(reader: rosbag2_py.SequentialReader, topic: str) -> str | None:
    for t in reader.get_all_topics_and_types():
        if t.name == topic:
            return t.type
    return None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Compute average covariance trace score from a ROS2 bag.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "bag_path",
        help="Path to the ROS2 bag directory or .db3 file.",
    )
    p.add_argument(
        "--topic", "-t",
        default=DEFAULT_TOPIC,
        help=f"Topic to read (default: {DEFAULT_TOPIC})",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print the trace value for every message.",
    )
    p.add_argument(
        "--list-topics", "-l",
        action="store_true",
        help="List all topics in the bag and exit.",
    )
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
    print(f"Bag    : {args.bag_path}")
    print()

    traces: list[float] = []

    while reader.has_next():
        topic, raw, _stamp = reader.read_next()
        if topic != args.topic:
            continue

        msg = deserialize_message(raw, msg_type)
        trace = covariance_trace(list(msg.pose.covariance))
        traces.append(trace)

        if args.verbose:
            t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            print(f"  [{len(traces):5d}]  t={t:.3f}  trace={trace:.6e}")

    n = len(traces)
    print()
    print("=" * 50)
    print(f"  Messages processed : {n}")

    if n == 0:
        print("  No messages found on this topic.")
        sys.exit(1)

    avg = sum(traces) / n
    min_t = min(traces)
    max_t = max(traces)

    print(f"  Avg cov trace (score) : {avg:.6e}  (lower is better)")
    print(f"  Min cov trace         : {min_t:.6e}")
    print(f"  Max cov trace         : {max_t:.6e}")
    print("=" * 50)


if __name__ == "__main__":
    main()
