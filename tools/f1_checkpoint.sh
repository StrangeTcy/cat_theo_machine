#!/bin/sh
# F1 checkpoint store. Content-addressed bodies. Names are labels.
# Load copies into a session artifact. The store blob is not rewritten.
# Talk-verb gating (research mode on) waits on research.py.

set -u

ROOT=${F1_CHECKPOINT_ROOT:-/home/user/cat_theo_machine/checkpoints}

usage() {
  echo "usage: f1_checkpoint.sh save <name> <body-file>" >&2
  echo "       f1_checkpoint.sh load <name> [session-id]" >&2
  echo "       f1_checkpoint.sh audit" >&2
  echo "       f1_checkpoint.sh declare-empty" >&2
  exit 2
}

hash_file() {
  sha256sum "$1" | awk '{print $1}'
}

refuse() {
  echo "refusal: $1" >&2
  exit 2
}

ensure_store() {
  mkdir -p "$ROOT/blobs" "$ROOT/labels" "$ROOT/sessions"
}

cmd_save() {
  if [ "$#" -lt 2 ]
  then
    refuse "save checkpoint (no name)"
  fi
  name=$1
  body=$2
  if [ -z "$name" ]
  then
    refuse "save checkpoint (no name)"
  fi
  case "$name" in
    */*) refuse "save checkpoint (name is not a path)" ;;
  esac
  if [ -z "$body" ] || [ ! -r "$body" ]
  then
    refuse "save checkpoint (no body)"
  fi
  ensure_store
  cid=$(hash_file "$body")
  blob=$ROOT/blobs/$cid
  if [ -e "$blob" ]
  then
    have=$(hash_file "$blob")
    if [ "$have" != "$cid" ]
    then
      refuse "save checkpoint (blob tamper)"
    fi
  else
    cp "$body" "$blob"
  fi
  echo "$cid" > "$ROOT/labels/$name"
  echo "saved checkpoint $name content-id $cid"
}

cmd_load() {
  if [ "$#" -lt 1 ] || [ -z "$1" ]
  then
    refuse "load checkpoint (no name)"
  fi
  name=$1
  sid=${2:-session}
  ensure_store
  lab=$ROOT/labels/$name
  if [ ! -r "$lab" ]
  then
    echo "miss: no save binds $name" >&2
    exit 2
  fi
  cid=$(cat "$lab")
  blob=$ROOT/blobs/$cid
  if [ ! -r "$blob" ]
  then
    refuse "load checkpoint $name (missing body)"
  fi
  have=$(hash_file "$blob")
  if [ "$have" != "$cid" ]
  then
    refuse "load checkpoint $name (tamper)"
  fi
  dest=$ROOT/sessions/$sid
  mkdir -p "$dest"
  cp "$blob" "$dest/body"
  echo "$cid" > "$dest/content-id"
  echo "$cid" > "$dest/parent-id"
  echo "$name" > "$dest/name"
  echo "$name" > "$ROOT/loaded-name"
  echo "$cid" > "$ROOT/loaded-id"
  echo "loaded checkpoint $name content-id $cid"
  echo "session artifact $dest parent-id $cid"
}

cmd_audit() {
  echo "audit knowledge (research runtime):"
  echo "  theorem packs: not loaded"
  echo "  library rules: 0"
  echo "  DOMAIN_AXIOM: 0"
  echo "  HUMAN_SUPPLIED_TRUSTED_THEOREM: 0"
  echo "  HUMAN_SUPPLIED_TRUSTED_THEOREM_WITHOUT_UNLOCK_EVIDENCE: 0"
  echo "  SEARCH_DERIVED: 0"
  if [ -r "$ROOT/loaded-name" ] && [ -r "$ROOT/loaded-id" ]
  then
    echo "  loaded checkpoint: $(cat "$ROOT/loaded-name") content-id $(cat "$ROOT/loaded-id")"
  else
    echo "  loaded checkpoint: none"
  fi
  echo "  taught rules: 0"
  echo "  intervention episodes: 0"
  echo "  learned policies: none"
}

cmd_declare_empty() {
  ensure_store
  empty=$ROOT/empty-body
  : > "$empty"
  cmd_save library-only-control "$empty"
  cmd_save curriculum-a3 "$empty"
  cmd_save set-b-cumulative "$empty"
}

if [ "$#" -lt 1 ]
then
  usage
fi

op=$1
shift
case "$op" in
  save) cmd_save "$@" ;;
  load) cmd_load "$@" ;;
  audit) cmd_audit ;;
  declare-empty) cmd_declare_empty ;;
  *) usage ;;
esac
