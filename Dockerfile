ARG ROS_DISTRO=humble
FROM ros:${ROS_DISTRO}-ros-base

SHELL ["/bin/bash", "-lc"]

ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=${ROS_DISTRO}

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ros-${ROS_DISTRO}-rosbag2-py \
    ros-${ROS_DISTRO}-rosbag2-storage-default-plugins \
 && rm -rf /var/lib/apt/lists/*

RUN if getent group "${USER_GID}" >/dev/null; then \
      EXISTING_GROUP="$(getent group "${USER_GID}" | cut -d: -f1)"; \
    else \
      groupadd --gid "${USER_GID}" "${USERNAME}"; \
      EXISTING_GROUP="${USERNAME}"; \
    fi \
 && if getent passwd "${USER_UID}" >/dev/null; then \
      EXISTING_USER="$(getent passwd "${USER_UID}" | cut -d: -f1)"; \
    else \
      useradd --uid "${USER_UID}" --gid "${USER_GID}" -m "${USERNAME}"; \
      EXISTING_USER="${USERNAME}"; \
    fi \
 && if [[ "${EXISTING_USER}" != "${USERNAME}" ]]; then \
      usermod --login "${USERNAME}" --move-home --home /home/${USERNAME} "${EXISTING_USER}"; \
      EXISTING_USER="${USERNAME}"; \
    fi \
 && usermod --gid "${EXISTING_GROUP}" "${EXISTING_USER}" \
 && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/${USERNAME} \
 && chmod 0440 /etc/sudoers.d/${USERNAME}

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/${USERNAME}/.bashrc

WORKDIR /workspaces/data-acquisition
COPY --chown=${USERNAME}:${USERNAME} core/ core/
COPY --chown=${USERNAME}:${USERNAME} entrypoint.sh /entrypoint.sh
RUN chmod +x core/traj_score.py /entrypoint.sh \
 && ln -sf /entrypoint.sh /usr/local/bin/traj_score

USER ${USERNAME}

ENTRYPOINT ["/entrypoint.sh"]
