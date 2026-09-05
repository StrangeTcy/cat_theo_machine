#!/bin/sh
# F1: save, load, printed id matches. Host-side until research.py exists.

set -u

TOOL=/home/user/cat_theo_machine/tools/f1_checkpoint.sh
ROOT=/tmp/f1-checkpoint-test-$$
export F1_CHECKPOINT_ROOT=$ROOT
fail=0

fail_at() {
  echo "FAIL: $1" >&2
  fail=1
}

mkdir -p "$ROOT"
echo 'probe-body' > "$ROOT/probe.txt"

out=$($TOOL save probe "$ROOT/probe.txt")
echo "$out"
cid=$(echo "$out" | awk '{print $NF}')
if [ -z "$cid" ]
then
  fail_at "save printed no content-id"
fi

out2=$($TOOL load probe t1)
echo "$out2"
cid2=$(echo "$out2" | awk '/^loaded checkpoint/{print $NF}')
if [ "$cid" != "$cid2" ]
then
  fail_at "load id $cid2 does not match save id $cid"
fi

parent=$(cat "$ROOT/sessions/t1/parent-id")
if [ "$parent" != "$cid" ]
then
  fail_at "session parent-id $parent does not match $cid"
fi

# equal bodies share an id
echo 'probe-body' > "$ROOT/probe2.txt"
out3=$($TOOL save other "$ROOT/probe2.txt")
cid3=$(echo "$out3" | awk '{print $NF}')
if [ "$cid3" != "$cid" ]
then
  fail_at "equal bodies produced distinct ids"
fi

# missing name does not invent a body
if $TOOL load nosuch tmiss 2>/dev/null
then
  fail_at "missing load did not refuse"
fi
if [ -e "$ROOT/sessions/tmiss/body" ]
then
  fail_at "missing load invented a body"
fi

# tamper: rewrite blob bytes, load must refuse, session artifact unchanged
blob=$ROOT/blobs/$cid
cp "$blob" "$ROOT/blob.bak"
echo tamper > "$blob"
if $TOOL load probe t2 2>/dev/null
then
  fail_at "tamper load did not refuse"
fi
cp "$ROOT/blob.bak" "$blob"
if [ -e "$ROOT/sessions/t2/body" ]
then
  fail_at "tamper load wrote a session body"
fi

audit=$($TOOL audit)
echo "$audit"
echo "$audit" | grep -q "loaded checkpoint: probe content-id $cid" || fail_at "audit missing loaded checkpoint line"
echo "$audit" | grep -q "theorem packs:" || fail_at "audit missing theorem packs"
echo "$audit" | grep -q "DOMAIN_AXIOM:" || fail_at "audit missing DOMAIN_AXIOM"
echo "$audit" | grep -q "HUMAN_SUPPLIED_TRUSTED_THEOREM:" || fail_at "audit missing HUMAN_SUPPLIED"
echo "$audit" | grep -q "SEARCH_DERIVED:" || fail_at "audit missing SEARCH_DERIVED"

if [ "$fail" -ne 0 ]
then
  echo "F1 checkpoint test: FAIL"
  exit 1
fi
echo "F1 checkpoint test: PASS save/load id match $cid"
exit 0
