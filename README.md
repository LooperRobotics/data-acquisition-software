# traj_score

A command-line tool for evaluating **VIO / SLAM trajectory quality** from ROS2 bag files.

It reads `PoseWithCovarianceStamped` messages, computes the **covariance trace** for each pose, and reports comprehensive statistics and a single **0–100 quality score**.

## Score formula

```
score = min(100, ref_cov / max_trace × 100)
```

The score is driven by the **worst-case pose**: a single covariance spike drags the whole trajectory score down.  
`ref_cov` (default `1e-3`) is the covariance trace that maps to a perfect score of 100; tune it to your hardware.

| Score  | Quality   |
|--------|-----------|
| 90–100 | Excellent |
| 70–89  | Good      |
| 50–69  | Fair      |
| 0–49   | Poor      |

## Project structure

```
core/
    traj_score.py   # main script: scoring logic + ROS2 bag I/O + CLI
scripts/
    build_container.sh  # build image and recreate the container
Dockerfile
entrypoint.sh
```

## Requirements

- ROS2 Humble
- Python ≥ 3.10

## Quick start (Docker — recommended)

Docker is the easiest way to run `traj_score` without installing ROS2 locally.

```bash
git clone https://github.com/LooperRobotics/data-acquisition-software.git
cd data-acquisition-software

# Build image and create a persistent container
# BAG_DIR defaults to ~/bags — override to point at your bag directory
BAG_DIR=/path/to/your/bags bash scripts/build_container.sh
```

Run against a bag:

```bash
docker exec traj_score traj_score /bags/<bag_name>
```

Open an interactive shell inside the container:

```bash
docker exec -it traj_score bash
```

To update the container after a code change, re-run `build_container.sh` — it rebuilds the image and recreates the container automatically.

## Native installation (ROS2 already installed)

```bash
git clone https://github.com/LooperRobotics/data-acquisition-software.git
cd data-acquisition-software
source /opt/ros/humble/setup.bash
chmod +x core/traj_score.py
```

> **Important:** `rosbag2_py` C extensions are compiled for the system Python 3.10
> (`/usr/bin/python3`). Do **not** run with a conda or venv interpreter — the
> script shebang (`#!/usr/bin/python3`) handles this automatically.

Make `traj_score` available system-wide:

```bash
sudo ln -sf "$(pwd)/core/traj_score.py" /usr/local/bin/traj_score
```

## Usage

```bash
# Basic evaluation (uses default topic)
traj_score /path/to/bag

# Specify a different topic
traj_score /path/to/bag --topic /my/pose_topic

# Adjust the reference covariance (tune to your system)
traj_score /path/to/bag --ref-cov 5e-4

# Save full results to JSON
traj_score /path/to/bag --json results.json

# List all topics in the bag
traj_score /path/to/bag --list-topics

# Print per-pose trace values
traj_score /path/to/bag --verbose
```

## Example output

```
======================================================
  Trajectory Quality Report
  Bag   : /data/run_001
  Topic : /camera/camera/vio_image_cov
------------------------------------------------------
  Poses processed  : 12450
  Mean cov trace   : 4.231823e-04
  Std  cov trace   : 1.102345e-04
  Min  cov trace   : 2.018432e-04
  Max  cov trace   : 9.876543e-03
  p50  cov trace   : 3.987654e-04
  p90  cov trace   : 6.543210e-04
  p99  cov trace   : 1.234567e-03
------------------------------------------------------
  Reference cov    : 1.000000e-03  (= score 100)
  Score            : 68.3 / 100  [Good]  (driven by max trace)
======================================================
```

## JSON output schema

```json
{
  "bag_path": "/absolute/path/to/bag",
  "topic": "/camera/camera/vio_image_cov",
  "n_poses": 12450,
  "mean_trace": 4.231823e-4,
  "std_trace":  1.102345e-4,
  "min_trace":  2.018432e-4,
  "max_trace":  9.876543e-3,
  "p50_trace":  3.987654e-4,
  "p90_trace":  6.543210e-4,
  "p99_trace":  1.234567e-3,
  "ref_cov":    1e-3,
  "score":      100.0,
  "quality":    "Excellent"
}
```

## License

MIT
