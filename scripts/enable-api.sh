#!/usr/bin/env bash
# Enable the GLPI REST API on a disposable test instance and print the
# environment the integration suite expects.
#
#     ./scripts/enable-api.sh <glpi-service> <db-service> <http-port>
#     ./scripts/enable-api.sh glpi11 db11 8011
#
# A fresh container installs GLPI on first boot, which takes several minutes;
# this waits for that to finish before touching anything.
#
# Test-only. Never point this at a real instance: it rewrites API settings and
# the 'glpi' user's API token.
set -uo pipefail

GLPI_SERVICE="${1:-glpi11}"
DB_SERVICE="${2:-db11}"
PORT="${3:-8011}"

APP_TOKEN="glpipy_test_app_token_0123456789"
USER_TOKEN="glpipy_test_user_token_9876543210"

# Git Bash on Windows rewrites /container/paths into C:\... before they reach
# docker; this disables that for every docker call below.
export MSYS_NO_PATHCONV=1

compose() { docker compose -f docker-compose.test.yml "$@"; }

echo "Waiting for GLPI to answer on port ${PORT}..."
ready=0
for _ in $(seq 1 120); do
  if [ "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:${PORT}/")" = "200" ]; then
    ready=1
    break
  fi
  sleep 5
done
if [ "${ready}" -ne 1 ]; then
  echo "GLPI never came up. Check: docker compose -f docker-compose.test.yml logs ${GLPI_SERVICE}" >&2
  exit 1
fi

version=$(compose exec -T "${DB_SERVICE}" mysql -uglpi -pglpi glpi -N -e \
  "SELECT value FROM glpi_configs WHERE name='version';" 2>/dev/null | tr -d '\r')
echo "GLPI ${version:-unknown} is up."

echo "Enabling the REST API..."
compose exec -T "${DB_SERVICE}" mysql -uglpi -pglpi glpi 2>/dev/null <<'SQL'
UPDATE glpi_configs SET value='1'
 WHERE name IN ('enable_api',
                'enable_api_login_credentials',
                'enable_api_login_external_token');
SQL

echo "Registering the test API client..."
# Done through GLPI's own classes rather than SQL: since 11.0.3 app tokens are
# stored encrypted, so a plaintext INSERT fails at authentication time.
compose cp scripts/seed_api_client.php "${GLPI_SERVICE}":/tmp/seed_api_client.php >/dev/null
compose exec -T \
  -e SEED_APP_TOKEN="${APP_TOKEN}" \
  -e SEED_USER_TOKEN="${USER_TOKEN}" \
  "${GLPI_SERVICE}" php /tmp/seed_api_client.php

compose exec -T "${GLPI_SERVICE}" \
  php /var/www/glpi/bin/console cache:clear --allow-superuser >/dev/null 2>&1

echo "Verifying authentication..."
response=$(curl -s \
  -H "App-Token: ${APP_TOKEN}" \
  -H "Authorization: user_token ${USER_TOKEN}" \
  "http://localhost:${PORT}/apirest.php/initSession")
case "${response}" in
  *session_token*) echo "OK - the API accepted both tokens." ;;
  *) echo "FAILED: ${response:-no response}" >&2; exit 1 ;;
esac

cat <<ENV

Ready. Export these, then run: pytest tests/test_integration.py -v

export GLPI_TEST_URL=http://localhost:${PORT}/apirest.php
export GLPI_TEST_APP_TOKEN=${APP_TOKEN}
export GLPI_TEST_USER_TOKEN=${USER_TOKEN}
export GLPI_TEST_USERNAME=glpi
export GLPI_TEST_PASSWORD=glpi
ENV
