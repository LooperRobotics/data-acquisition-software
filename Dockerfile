FROM ros:humble-ros-base

RUN apt-get update && apt-get install -y \
    ros-humble-rosbag2-py \
    ros-humble-rosbag2-storage-default-plugins \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ws
COPY core/ core/

RUN chmod +x core/traj_score.py

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
