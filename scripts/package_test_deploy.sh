#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist"
DATE_TAG="$(date +%Y%m%d-%H%M%S)"
PACKAGE_NAME="crm-system-test-deploy-${DATE_TAG}"
STAGE_DIR="${DIST_DIR}/${PACKAGE_NAME}"
ARCHIVE_PATH="${DIST_DIR}/${PACKAGE_NAME}.tar.gz"

mkdir -p "${DIST_DIR}"
rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}/backend" "${STAGE_DIR}/frontend" "${STAGE_DIR}/docs"

cp "${PROJECT_ROOT}/README.md" "${STAGE_DIR}/"
cp "${PROJECT_ROOT}/docker-compose.yml" "${STAGE_DIR}/"
cp "${PROJECT_ROOT}/deploy/test/docker-compose.env.example" "${STAGE_DIR}/"

cp \
  "${PROJECT_ROOT}/docs/deployment-guide.md" \
  "${PROJECT_ROOT}/docs/multi-env-deployment.md" \
  "${PROJECT_ROOT}/docs/troubleshooting-guide.md" \
  "${PROJECT_ROOT}/docs/test-env-package-guide.md" \
  "${STAGE_DIR}/docs/"

cp \
  "${PROJECT_ROOT}/backend/Dockerfile" \
  "${PROJECT_ROOT}/backend/requirements.txt" \
  "${PROJECT_ROOT}/backend/alembic.ini" \
  "${PROJECT_ROOT}/backend/.env.example" \
  "${PROJECT_ROOT}/backend/.env.test" \
  "${PROJECT_ROOT}/backend/.env.production" \
  "${PROJECT_ROOT}/backend/create_test_user.py" \
  "${PROJECT_ROOT}/backend/seed_dict_data.py" \
  "${STAGE_DIR}/backend/"

cp \
  "${PROJECT_ROOT}/frontend/Dockerfile" \
  "${PROJECT_ROOT}/frontend/nginx.conf" \
  "${PROJECT_ROOT}/frontend/package.json" \
  "${PROJECT_ROOT}/frontend/package-lock.json" \
  "${PROJECT_ROOT}/frontend/tsconfig.json" \
  "${STAGE_DIR}/frontend/"

rsync -a \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  --exclude '.pytest_cache' \
  "${PROJECT_ROOT}/backend/app/" "${STAGE_DIR}/backend/app/"

rsync -a \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "${PROJECT_ROOT}/backend/alembic/" "${STAGE_DIR}/backend/alembic/"

rsync -a \
  --exclude 'node_modules' \
  --exclude 'build' \
  "${PROJECT_ROOT}/frontend/src/" "${STAGE_DIR}/frontend/src/"

rsync -a "${PROJECT_ROOT}/frontend/public/" "${STAGE_DIR}/frontend/public/"

find "${STAGE_DIR}/backend/app" \
  \( -name '*.backup' -o -name '*.bak' -o -name '*.bak*' -o -name 'refactor_main.py' \) \
  -delete

find "${STAGE_DIR}" -type f | sed "s#${STAGE_DIR}/##" | sort > "${STAGE_DIR}/PACKAGE_MANIFEST.txt"

tar -czf "${ARCHIVE_PATH}" -C "${DIST_DIR}" "${PACKAGE_NAME}"

printf 'Package directory: %s\n' "${STAGE_DIR}"
printf 'Archive: %s\n' "${ARCHIVE_PATH}"
