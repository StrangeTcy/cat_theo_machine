# `colab/` — the laptop and a notebook as one mesh, and a Neo4j dump as shards

Two notebooks, one runbook. Both come from the same observation: the machine already
runs distributed across processes on one box (`networking/`, W2/W16), but a Colab VM
has none of the three things that design quietly assumed — a shared filesystem, an
address anyone can dial, and certificates that name the address in front of you. W20
removes those assumptions from the transport (`networking/README.md`, "Beyond one
filesystem"); W19 moves the one job a laptop should not have to do (running Neo4j to
decode a dump) into the notebook.

| File | What it is |
|---|---|
| `mesh_worker.ipynb` | A Colab worker of the laptop's coordinator: outbound only, identity-verified, artifacts over the wire. |
| `neo4j_dump_to_shards.ipynb` | Neo4j `.dump` → APOC CSV export → split → label-sharded Machine snapshots, all on Colab. |
| this file | The laptop side of both, in order, with what to expect. |

Honesty first: neither notebook has been run by its author. The sandbox the work was done
in has no Neo4j, no Colab and no route to `dist.neo4j.org`. Every command follows the
documented tooling, the Python halves are driven by `validation/test31_wan_mesh_artifacts.py`
(the WAN transport, end to end on loopback through the real CLI) and
`validation/test32_neo4j_export_to_shards.py` (a synthetic APOC export through split and
shard), and the first real run is the trial. When a cell fails, the message is the result
to bring back.

## A — laptop ⇄ Colab mesh

### 0. What travels where

```
laptop                                   tunnel                      Colab
───────────────────────────────          ──────────────              ──────────────────────────
coordinator  --bind 0.0.0.0:7443  <────  HOST:PORT  <────  dials ──  worker --no-inbound
             --artifacts wire            (ciphertext only)           --verify identity --expect coordinator
             --advertise HOST:PORT                                   --artifacts wire --artifact-dir …
jobs.json, inputs, results (authority)                               fetched inputs, produced results (copies)
ca.key stays here                                                    bundle: ca.crt + colab-1.crt + colab-1.key
```

mTLS is end to end: the tunnel is trusted with nothing, and a worker from another CA fails
the handshake exactly as it does on loopback (`test31` phase 1). The worker checks the
coordinator's certificate **name** rather than its address, because a tunnel endpoint is
not something a leaf can be issued for in advance; the CA pin is unchanged.

### 1. Issue the Colab worker's bundle (once per worker name)

```bash
cd /path/above/cat_theo_machine
python -m cat_theo_machine.main mesh --role issue \
    --cert-dir ~/hyge-pki --cert-name colab-1 --bundle-dir ~/hyge-bundles/colab-1
```

`~/hyge-pki` is created on first use (CA + key) — keep it **outside** the repository; the
identity guard refuses to write keys inside the tree. The bundle directory ends up holding
exactly `ca.crt`, `colab-1.crt`, `colab-1.key` and a `bundle.json` saying so. Carry those
three files to the notebook by upload; never through the repository, which is public.

### 2. Start a tunnel to local port 7443

Any TCP forwarder works; the connection is opaque TLS. Three that need no server of yours:

```bash
ngrok tcp 7443                 # prints  tcp://0.tcp.eu.ngrok.io:12345  -> HOST:PORT below
bore local 7443 --to bore.pub  # prints  bore.pub:NNNNN
ssh -R 0.0.0.0:7443:localhost:7443 user@some-vps   # needs GatewayPorts yes on the VPS
```

### 3. Start the coordinator with the jobs it should hand out

```bash
python -m cat_theo_machine.main mesh --role coordinator \
    --cert-dir ~/hyge-pki --bind 0.0.0.0:7443 --advertise HOST:PORT \
    --artifacts wire --jobs jobs.json --run-seconds 7200
```

* `--bind 0.0.0.0` so the tunnel's local end can reach it; `--advertise` is what the
  coordinator tells peers to dial (it appears in the discovery record and in gossip).
* `--artifacts wire` is the mode switch. A job's `result_ref` is still a path — *your*
  path: the result arrives in frames and is written there by the coordinator itself, with
  a `.manifest.json` sidecar beside it, exactly as a local worker would have left it. A
  job whose manifest names a `unit_path` (W16 units) has that file served to the worker
  on request; nothing else on your disk is reachable (`test31` phase 2 tries).
* Workers on the same laptop can still join in the usual way; mixing is fine.

`jobs.json` is the same file `mesh.load_jobs` always read:

```json
{"jobs": [{"job_id": "wan-1", "mode": "dfs", "result_ref": "/home/me/results/wan-1.json", "manifest": {}}]}
```

### 4. Run `mesh_worker.ipynb`

Fill in `COORDINATOR = "HOST:PORT"`, `CERT_NAME = "colab-1"`, upload the three files when
cell 2 asks, run cell 3. The worker boots the packs once (~20 s on Colab's CPU, more on a
cold VM) and then serves jobs until `RUN_SECONDS` or until the coordinator sends `shutdown`.

What the coordinator's log shows for a healthy run:

```
[mesh:coordinator] listening on 0.0.0.0:7443 (mTLS, mutual authentication required)
[mesh:coordinator] announcing HOST:PORT to peers
[mesh:coordinator] artifacts travel over the wire
[mesh:coordinator] submitted 1 job(s): wan-1
…
[mesh:coordinator] summary: {"completed": 1, "failed": 0, …}
```

and `~/hyge-pki/ledger.json` afterwards holds the event sequence — for a wire job the
load-bearing events are `artifact-served` (an input went out), `artifact-incoming` /
`artifact-received` (the result and its sidecar came back, digest verified) and only then
`job-result`. A worker that reports success without its bytes having arrived is recorded
as `result-without-artifact` and the job is marked failed, not trusted.

### 5. Things that are deliberately not solved here

* **Stealing from Colab.** A no-inbound worker steals from others but cannot be stolen
  from; with one laptop worker and one Colab worker that is the only asymmetry, and it is
  reported (`steal-unreachable`, backed off) rather than retried at loop speed.
* **Colab's clock.** Sessions end; `--run-seconds` and the coordinator's lease recovery
  (a lost member's running job is re-dispatched, W2) cover it. Nothing is checkpointed
  mid-job across the wire.
* **Bandwidth.** Chunks are 3 MiB per frame, base64 on the wire (~33 % overhead), one
  transfer at a time per link. A 100 MB result over a 10 Mbit/s uplink is ~2 minutes;
  the result size is the search's, not the transport's, to reduce.

## B — Neo4j dump → shards

Run `neo4j_dump_to_shards.ipynb` with the dump uploaded (or on Drive) and
`NEO4J_VERSION` set to the **major version that wrote the dump** (a 4.x dump into 4.4; a
5.x dump into 5.x; 4.x into 5.x only with `MIGRATE_AFTER_LOAD`). The notebook:

1. installs the matching Java and a Neo4j Community tarball, copies the APOC core jar that
   ships in `labs/` into `plugins/`, enables file export, disables auth (it is a throwaway
   VM bound to localhost);
2. `neo4j-admin … load`s the dump and starts the server;
3. `CALL apoc.export.csv.all("all.csv", {})` — one CSV, header = the union of every
   property, node rows with `_id`/`_labels`, relationship rows with `_start`/`_end`/`_type`;
4. `importers/split_apoc_export.py` → `nodes.csv` + `edges.csv` + `split.json` (the
   first-label histogram is the list of shards to come, with sizes — check it against the
   ~10 KB-per-edge build cost before step 5);
5. `importers/sharded_import.py` → `shards/<Label>.json` + `manifest.json`;
6. zips the shards for download or Drive.

What the importers do with the content is unchanged from before (`SWARM_EVOLUTION_DAG.md`
§6, ingest path): nodes are named `Char`s, relationships `Pair(rel, Pair(a, Pair(b, …)))`,
labels and properties hyperedges keyed `(key, node, value)` with a whole property string in
one `Char` — arrays and numbers included, as text. Relationship properties become their own
edges keyed `TYPE:prop` whose target is the value, so a value can appear as a stub node in
a shard; that is the representation's choice, visible in the manifest, not a defect of the
split.

Booting a shard on the laptop:

```python
from cat_theo_machine import main as MA, runtime as RT
runtime = RT.boot_from_snapshot("/path/to/shards/Person.json", MA._runtime_namespace())
```
