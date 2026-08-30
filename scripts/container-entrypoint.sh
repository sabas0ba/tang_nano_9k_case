#!/bin/sh
set -eu

profile=${CASE_PROFILE:-/nix/var/nix/profiles/tang-nano-9k-case}

if [ ! -e "$profile" ]; then
  echo "development profile not found: $profile" >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  exec nix develop "$profile" --command bash
fi

exec nix develop "$profile" --command "$@"
