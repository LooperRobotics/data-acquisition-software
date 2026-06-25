#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGE="${IMAGE:-data-acquisition}"
CONTAINER="${CONTAINER:-data-acquisition}"
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
    --volume "${BAG_DIR}:/data-acquisition" \
    --entrypoint /bin/bash \
    "${IMAGE}"

echo ""
echo "Container '${CONTAINER}' is running."
echo ""
echo "Run traj_score:"
echo "  docker exec ${CONTAINER} traj_score /data-acquisition/<bag_name>"
echo ""
echo "Open a shell:"
echo "  docker exec -it ${CONTAINER} bash"
