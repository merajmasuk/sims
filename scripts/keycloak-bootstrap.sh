#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root regardless of where the script is invoked from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -a
source "$SCRIPT_DIR/../.env"
set +a

KC_CONT=$(docker compose -f "$SCRIPT_DIR/../keycloak/docker-compose.yml" --project-directory "$SCRIPT_DIR/.." ps -q keycloak)

if [ -z "$KC_CONT" ]; then
  echo "Keycloak container not found — is it running?" >&2
  exit 1
fi

docker exec "$KC_CONT" /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 --realm master \
  --user $KEYCLOAK_ADMIN_USER --password $KEYCLOAK_ADMIN_PASSWORD

# Realm
docker exec "$KC_CONT" /opt/keycloak/bin/kcadm.sh create realms \
  -s realm=sims -s enabled=true \
  -s accessTokenLifespan=900 \
  -s ssoSessionIdleTimeout=1800 -s ssoSessionMaxLifespan=36000

# Realm roles
for role in admin student faculty; do
  docker exec -it $KC_CONT /opt/keycloak/bin/kcadm.sh create roles -r sims -s name=$role
done

# Frontend public client
docker exec "$KC_CONT" /opt/keycloak/bin/kcadm.sh create clients -r sims \
  -s clientId=sims-frontend \
  -s publicClient=true \
  -s standardFlowEnabled=true \
  -s directAccessGrantsEnabled=false \
  -s implicitFlowEnabled=false \
  -s 'redirectUris=["http://localhost:4200/*"]' \
  -s 'webOrigins=["http://localhost:4200"]' \
  -s attributes.'"pkce.code.challenge.method"'=S256

# Backend confidential client with service account
docker exec "$KC_CONT" /opt/keycloak/bin/kcadm.sh create clients -r sims \
  -s clientId=sims-backend \
  -s publicClient=false \
  -s serviceAccountsEnabled=true \
  -s standardFlowEnabled=false

CLIENT_UUID=$(docker exec "$KC_CONT" /opt/keycloak/bin/kcadm.sh get clients -r sims -q clientId=sims-backend --fields id --format csv --noquotes | tail -n1)

docker exec "$KC_CONT" /opt/keycloak/bin/kcadm.sh get clients/$CLIENT_UUID/client-secret -r sims

docker exec "$KC_CONT" /opt/keycloak/bin/kcadm.sh add-roles -r sims \
  --uusername service-account-sims-backend \
  --cclientid realm-management \
  --rolename manage-users --rolename view-users
