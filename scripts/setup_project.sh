#!/usr/bin/env bash
set -euo pipefail
: "${OWNER_OR_ORG:?Set OWNER_OR_ORG (user or org login)}"
: "${PROJECT_TITLE:=SMDaI Board}"

command -v gh >/dev/null || { echo "gh CLI required"; exit 1; }

# Получим node id владельца (user или org)
echo "Running: gh api graphql (resolve owner id)"
OWNER_ID=$(gh api graphql -f query='
query($login:String!){
  user(login:$login){ id __typename }
  organization(login:$login){ id __typename }
}' -f login="$OWNER_OR_ORG" --jq '.data.user.id // .data.organization.id')

# Создадим Project v2
echo "Running: gh api graphql (create project)"
RESP=$(gh api graphql -f query='
mutation($owner:ID!, $title:String!){
  createProjectV2(input:{ownerId:$owner, title:$title}){ projectV2{ id number url } }
}' -f owner="$OWNER_ID" -f title="$PROJECT_TITLE")

URL=$(echo "$RESP" | jq -r '.data.createProjectV2.projectV2.url')
echo "Project created: $URL"
echo "→ Add this URL to repo Settings → Secrets → Actions → PROJECT_URL"
