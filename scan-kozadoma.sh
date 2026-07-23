#!/bin/bash
set -euo pipefail
cd /opt/harken
for q in козадома kozadoma 'коза дома'; do
  docker compose exec -T harken harken track "$q" || true
done
