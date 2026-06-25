#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
exec /usr/bin/python3 /ws/core/traj_score.py "$@"
