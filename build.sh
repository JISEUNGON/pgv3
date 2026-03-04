#!/usr/bin/env bash
set -euo pipefail

IMAGE_BASE="repo.iris.tools/irisdev/pgv3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TODAY="$(date +%Y%m%d)"

if GIT_HASH="$(git -C "${SCRIPT_DIR}" rev-parse --short=7 HEAD 2>/dev/null)"; then
  :
else
  GIT_HASH="nogit"
fi

DEFAULT_TAG="${IMAGE_BASE}:${TODAY}-${GIT_HASH}"
IMAGE_TAG="${DEFAULT_TAG}"
BUILD_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag|-t)
      shift
      if [[ $# -eq 0 ]]; then
        echo "Error: --tag requires a value" >&2
        exit 1
      fi
      VALUE="$1"
      # VALUE 안에 / 또는 : 가 있으면 전체 이미지 이름으로 간주
      if [[ "${VALUE}" == *"/"* || "${VALUE}" == *":"* ]]; then
        IMAGE_TAG="${VALUE}"
      else
        IMAGE_TAG="${IMAGE_BASE}:${VALUE}"
      fi
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--tag TAG] [extra sudo podman build args...]"
      echo "  기본: ${DEFAULT_TAG}"
      echo "  --tag mytag        -> ${IMAGE_BASE}:mytag"
      echo "  --tag repo/img:tag -> repo/img:tag"
      exit 0
      ;;
    *)
      BUILD_ARGS+=("$1")
      shift
      ;;
  esac
done

echo "Building image: ${IMAGE_TAG}"
sudo podman buildx build --platform linux/amd64 -t "${IMAGE_TAG}" "${BUILD_ARGS[@]}" "${SCRIPT_DIR}"

echo "Done. Built image: ${IMAGE_TAG}"

