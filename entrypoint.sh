#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
exec /usr/bin/python3 /workspaces/traj_score/core/traj_score.py "$@"
