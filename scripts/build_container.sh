#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGE="${IMAGE:-traj_score}"
CONTAINER="${CONTAINER:-traj_score}"
BAG_DIR="${BAG_DIR:-${HOME}/bags}"

cd "${REPO_ROOT}"

echo "[1/2] Building image: ${IMAGE}"
docker build -t "${IMAGE}" .

echo "[2/2] Recreating container: ${CONTAINER}"
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    docker rm -f "${CONTAINER}"
fi

docker run -dit \
    --name "${CONTAINER}" \
    --volume "${BAG_DIR}:/bags" \
    --entrypoint /bin/bash \
    "${IMAGE}"

echo ""
echo "Container '${CONTAINER}' is running."
echo ""
echo "Run traj_score:"
echo "  docker exec ${CONTAINER} traj_score /bags/<bag_name>"
echo ""
echo "Open a shell:"
echo "  docker exec -it ${CONTAINER} bash"
