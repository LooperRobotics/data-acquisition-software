# data-acquisition-software

Tools for collecting and evaluating robot sensor data, built on ROS2 Humble.

## Tools

| Tool | Description |
|------|-------------|
| `traj_score` | Evaluate VIO / SLAM trajectory quality from a ROS2 bag |

## Project structure

```
core/
    traj_score.py       # trajectory quality scorer: bag I/O + scoring logic + CLI
scripts/
    build_container.sh  # build Docker image and recreate the container
Dockerfile
entrypoint.sh
```

## Requirements

- ROS2 Humble
- Python ≥ 3.10

---

## Quick start (Docker — recommended)

Docker is the easiest way to run any tool without installing ROS2 locally.

### 1. Clone the repo

```bash
git clone https://github.com/LooperRobotics/data-acquisition-software.git
cd data-acquisition-software
```

### 2. Build the image and start the container

Use the helper script — it builds the Docker image and recreates the persistent container in one step:

```bash
# BAG_DIR defaults to ~/bags — set it to wherever your ROS2 bags live
BAG_DIR=/path/to/your/bags bash scripts/build_container.sh
```

What the script does internally:

```bash
docker build -t data-acquisition .
docker rm -f data-acquisition          # remove old container if it exists
docker run -dit \
    --name data-acquisition \
    --volume /path/to/your/bags:/data-acquisition \
    --entrypoint /bin/bash \
    data-acquisition
```

> Re-run `build_container.sh` after any code change — it rebuilds the image and recreates the container automatically.

### 3. Run a tool

```bash
docker exec data-acquisition traj_score /data-acquisition/<bag_name>
```

### 4. Open an interactive shell

```bash
docker exec -it data-acquisition bash
```

---

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

---

## traj_score

Reads `PoseWithCovarianceStamped` messages from a ROS2 bag, computes the **covariance trace** for each pose, and reports comprehensive statistics plus a single **0–100 quality score**.

### Score formula

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

### Usage

```bash
# Basic evaluation (uses default topic /camera/camera/vio_image_cov)
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

### Example output

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

### JSON output schema

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

---

## License

MIT
