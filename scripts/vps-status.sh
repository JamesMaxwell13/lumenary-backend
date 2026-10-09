#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/vps-common.sh"
require_runtime

compose ps
site_url="$(env_value SITE_URL)"
curl --fail --show-error --silent "$site_url/healthz"
echo
curl --fail --show-error --silent "$site_url/api/v1/health/"
echo
