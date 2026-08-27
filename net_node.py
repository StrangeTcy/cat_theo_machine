"""Arc N & O & P: Replicated log, distributed cycles, semantic verification,
and node coordination over mTLS.

The wire is the boundary: only wire.py bytes cross sockets.
Coordinator is the single writer/activator. Workers never activate.
"""

from __future__ import annotations

import json
import socket
import ssl

from . import machine as M
from . import labels as Lmod
from . import graph as Gmod
from . import wire as Wmod
from . import net_transport as Tmod

SNAPSHOT_WINDOW_CAP = 1000
WORKER_DEADLINE_CAP = 100
RECONNECT_ATTEMPT_CAP = 100


class NodeConfig:
    def __init__(
        self,
        name,
        role,
        cert_path,
        key_path,
        ca_path,
        host="127.0.0.1",
        port=7433,
        peers=None,
        authority_cns=None,
        budgets=None,
    ):
        self.name = name
        self.role = role
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        self.host = host
        self.port = port
        self.peers = peers or {}
        self.authority_cns = authority_cns or []
        self.budgets = budgets or {}


def load_config(config_source):
    """Load and validate NodeConfig from JSON file or JSON string.

    Enforces exactly one coordinator and forbids worker CNs in authority_cns.
    """
    try:
        with open(config_source, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, TypeError):
        data = json.loads(config_source)

    name = data.get("name", "")
    role = data.get("role", "")
    if role != "coordinator" and role != "worker":
        raise ValueError("Role must be coordinator or worker")

    peers = data.get("peers", {})
    coordinator_count = 0
    if role == "coordinator":
        coordinator_count += 1
    for peer_name, peer_info in peers.items():
        try:
            peer_role = peer_info.get("role", "worker")
        except AttributeError:
            peer_role = "worker"
        if peer_role == "coordinator":
            coordinator_count += 1
    if coordinator_count != 1:
        raise ValueError("Exactly one coordinator allowed")

    authority_cns = data.get("authority_cns", [])
    if role == "worker" and name in authority_cns:
        raise ValueError("Worker node CN cannot be in authority_cns")
    for peer_name, peer_info in peers.items():
        try:
            peer_role = peer_info.get("role", "worker")
        except AttributeError:
            peer_role = "worker"
        if peer_role == "worker" and peer_name in authority_cns:
            raise ValueError("Worker node CN cannot be in authority_cns")

    return NodeConfig(
        name=name,
        role=role,
        cert_path=data.get("cert_path", ""),
        key_path=data.get("key_path", ""),
        ca_path=data.get("ca_path", ""),
        host=data.get("host", "127.0.0.1"),
        port=data.get("port", 7433),
        peers=peers,
        authority_cns=authority_cns,
        budgets=data.get("budgets", {}),
    )


def strip_approval_annotations(store):
    """Strip any attached Approved or Countersigned terms on receipt."""
    entries = Gmod.ProposalStoreEntries(store)()
    reversed_entries = M.EmptyList
    remaining = entries
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        entry = M.Head(remaining)()
        proposal = Gmod.ProposalEntryProposal(entry)()
        annotations = Gmod.ProposalEntryAnnotations(entry)()
        cleaned_annotations = M.EmptyList
        curr_ann = annotations
        while M.IdentityCompare(curr_ann, M.EmptyList)() is M.false_value:
            ann = M.Head(curr_ann)()
            tag = M.Head(ann)() if M.IsPair(ann)() is M.truth_value else ann
            if (
                M.TermEqual(tag, Lmod.ApprovedLabel)() is M.false_value
                and M.TermEqual(tag, Lmod.CountersignedLabel)() is M.false_value
            ):
                cleaned_annotations = M.Pair(ann, cleaned_annotations)
            curr_ann = M.Tail(curr_ann)()
        cleaned_entry = Gmod.ProposalEntry(
            proposal,
            Gmod.Reverse(cleaned_annotations)(),
        )()
        reversed_entries = M.Pair(cleaned_entry, reversed_entries)
        remaining = M.Tail(remaining)()
    return Gmod.ProposalStore(Gmod.Reverse(reversed_entries)())()


def verify_incoming(artifact_kind, payload_bytes, local_state):
    """Step 58: Never trust decrypted input; semantic re-verification."""
    try:
        term = Wmod.deserialize_term(payload_bytes)
    except Exception:
        return M.Pair(
            Lmod.ReasonNetworkLabel,
            M.Pair(M.Char("deserialization-failed"), M.EmptyList),
        )

    if artifact_kind == "proposals":
        stripped_store = strip_approval_annotations(term)
        entries = Gmod.ProposalStoreEntries(stripped_store)()
        remaining = entries
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            proposal = Gmod.ProposalEntryProposal(entry)()
            classification = Gmod.ClassifyProposal(proposal)()
            if M.IdentityCompare(classification, M.EmptyList)() is M.truth_value:
                return M.Pair(
                    Lmod.ReasonNetworkLabel,
                    M.Pair(M.Char("unknown-proposal-class"), M.EmptyList),
                )
            law = Gmod.ProposalLaw(proposal)()
            if Gmod.LawMapsComplete(law)() is M.false_value:
                return M.Pair(
                    Lmod.ReasonNetworkLabel,
                    M.Pair(M.Char("law-maps-incomplete"), M.EmptyList),
                )
            remaining = M.Tail(remaining)()
        return stripped_store

    if artifact_kind == "ledger_records":
        remaining_records = term
        while M.IdentityCompare(remaining_records, M.EmptyList)() is M.false_value:
            record = M.Head(remaining_records)()
            law = Gmod.FiringRecordLaw(record)()
            if local_state is not None:
                if (
                    Gmod.ChainHasTerm(
                        Gmod.InstalledLaws(local_state)(),
                        law,
                    )()
                    is M.false_value
                ):
                    return M.Pair(
                        Lmod.ReasonNetworkLabel,
                        M.Pair(M.Char("unknown-law"), M.EmptyList),
                    )
            remaining_records = M.Tail(remaining_records)()
        return term

    if artifact_kind == "delta":
        return Wmod.apply_delta(local_state, payload_bytes)

    if artifact_kind == "snapshot":
        try:
            version = M.Head(term)()
            store = M.Head(M.Tail(term)())()
            re_serialized = Wmod.serialize_term(term)
            if Wmod.content_hash(re_serialized) != Wmod.content_hash(payload_bytes):
                return M.Pair(
                    Lmod.ReasonNetworkLabel,
                    M.Pair(M.Char("hash-mismatch"), M.EmptyList),
                )
            return term
        except Exception:
            return M.Pair(
                Lmod.ReasonNetworkLabel,
                M.Pair(M.Char("snapshot-corrupt"), M.EmptyList),
            )

    return term


class NetworkNode:
    def __init__(self, config, initial_version=None, initial_store=None, initial_ledger=None):
        self.config = config
        self.version = initial_version or Gmod.GraphVersion(
            M.EmptyList, M.EmptyList, M.EmptyList
        )()
        self.store = initial_store or Gmod.ProposalStore(M.EmptyList)()
        self.ledger = initial_ledger or Gmod.FiringLedger(M.EmptyList)
        self.history_window = []  # sliding window of (hash, version, delta_bytes)
        self.record_history(self.version, None)
        self.server_socket = None
        self.connected_workers = {}  # session_peer_cn -> session
        self.coordinator_session = None

    def head_hash(self):
        return Wmod.content_hash(Wmod.serialize_version(self.version))

    def record_history(self, version, delta_bytes):
        h = Wmod.content_hash(Wmod.serialize_version(version))
        self.history_window.append((h, version, delta_bytes))
        if len(self.history_window) > SNAPSHOT_WINDOW_CAP:
            self.history_window.pop(0)

    def find_deltas_since(self, from_hash):
        matching_index = -1
        for i in range(len(self.history_window)):
            if self.history_window[i][0] == from_hash:
                matching_index = i
                break
        if matching_index == -1:
            return None
        deltas = []
        for i in range(matching_index + 1, len(self.history_window)):
            if self.history_window[i][2] is not None:
                deltas.append(self.history_window[i][2])
        return deltas

    def start_server(self):
        ctx = Tmod.make_server_context(
            self.config.cert_path,
            self.config.key_path,
            self.config.ca_path,
        )
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_sock.bind((self.config.host, self.config.port))
        raw_sock.listen(10)
        self.server_socket = ctx.wrap_socket(raw_sock, server_side=True)
        return self.server_socket

    def accept_one_worker(self):
        conn, addr = self.server_socket.accept()
        peer_cn = Tmod.extract_peer_cn(conn)
        session = Tmod.TransportSession(conn, peer_cn)
        self.connected_workers[peer_cn] = session
        return session

    def handle_annotate_request(self, session, payload_bytes):
        """Step 62: ANNOTATE accepted only when sender CN is in authority_cns."""
        if session.peer_cn not in self.config.authority_cns:
            refused = M.Pair(
                Lmod.ReasonNetworkLabel,
                M.Pair(M.Char("unauthorized-authority"), M.EmptyList),
            )
            Tmod.send_frame(session, Tmod.ERR, Wmod.serialize_term(refused))
            return False

        annotation_term = Wmod.deserialize_term(payload_bytes)
        verb = M.Head(annotation_term)()
        target = M.Head(M.Tail(annotation_term)())()
        authority_cn_atom = M.Char(session.peer_cn)

        from . import session as Smod

        ann = Smod.make_annotation(verb, target, authority_cn_atom)

        if M.IdentityCompare(ann, M.EmptyList)() is M.false_value:
            self.store = Gmod.ProposalStoreAttach(self.store, target, ann)()
            Tmod.send_frame(session, Tmod.ACK, Wmod.serialize_term(M.Char("ok")))
            return True
        return False

    def sync_worker_with_coordinator(self, session):
        """Worker side sync protocol with coordinator."""
        hello_payload = Wmod.serialize_term(
            M.Pair(
                M.Char(self.config.name),
                M.Pair(
                    M.GMPRep(str(Tmod.PROTOCOL_VERSION)),
                    M.Pair(M.Char(self.head_hash()), M.EmptyList),
                ),
            )
        )
        Tmod.send_frame(session, Tmod.HELLO, hello_payload)

        msg_type, payload = Tmod.recv_frame(session)
        if msg_type != Tmod.HEADS:
            return False
        coord_heads_term = Wmod.deserialize_term(payload)
        coord_head_hash = M.Head(coord_heads_term)().symbol

        if self.head_hash() == coord_head_hash:
            return True

        get_deltas_payload = Wmod.serialize_term(
            M.Pair(M.Char(self.head_hash()), M.EmptyList)
        )
        Tmod.send_frame(session, Tmod.GET_DELTAS, get_deltas_payload)

        resp_type, resp_payload = Tmod.recv_frame(session)
        if resp_type == Tmod.DELTAS:
            deltas_chain = Wmod.deserialize_term(resp_payload)
            curr = deltas_chain
            while M.IdentityCompare(curr, M.EmptyList)() is M.false_value:
                delta_atom = M.Head(curr)()
                delta_bytes = delta_atom().encode("latin1")
                verified = verify_incoming("delta", delta_bytes, self.version)
                if (
                    M.IsPair(verified)() is M.truth_value
                    and M.TermEqual(M.Head(verified)(), Lmod.ReasonNetworkLabel)()
                    is M.truth_value
                ):
                    return False
                self.version = verified
                curr = M.Tail(curr)()
            return True

        if resp_type == Tmod.SNAPSHOT:
            verified = verify_incoming("snapshot", resp_payload, None)
            if (
                M.IsPair(verified)() is M.truth_value
                and M.TermEqual(M.Head(verified)(), Lmod.ReasonNetworkLabel)()
                is M.truth_value
            ):
                return False
            self.version = M.Head(verified)()
            self.store = M.Head(M.Tail(verified)())()
            return True

        return False

    def close(self):
        for s in self.connected_workers.values():
            s.close()
        self.connected_workers.clear()
        if self.coordinator_session is not None:
            self.coordinator_session.close()
            self.coordinator_session = None
        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None


def net_distributed_cycle(coordinator_node, budgets):
    """Step 57: Distributed cycle over the network.

    Broadcast head -> collect PROPOSALS & LEDGER_RECORDS under WORKER_DEADLINE_CAP
    -> sort worker inputs by (node CN, serialized bytes)
    -> MergeFrontiers -> AutonomyCycle for activation -> broadcast deltas.
    """
    coord_head = coordinator_node.head_hash()
    heads_payload = Wmod.serialize_term(
        M.Pair(M.Char(coord_head), M.EmptyList)
    )

    sorted_worker_cns = sorted(coordinator_node.connected_workers.keys())
    slice_count_text = str(len(sorted_worker_cns)) if sorted_worker_cns else "1"

    worker_results = []

    for idx, cn in enumerate(sorted_worker_cns):
        session = coordinator_node.connected_workers[cn]
        Tmod.send_frame(session, Tmod.HEADS, heads_payload)

        poll_counter = 0
        received_props = None
        received_records = None
        while poll_counter < WORKER_DEADLINE_CAP:
            poll_counter += 1
            msg_type, payload = Tmod.recv_frame(session)
            if msg_type == Tmod.PROPOSALS:
                received_props = payload
            elif msg_type == Tmod.LEDGER_RECORDS:
                received_records = payload
            elif msg_type == Tmod.ANNOTATE:
                if session.peer_cn in coordinator_node.config.authority_cns:
                    coordinator_node.handle_annotate_request(session, payload)
                else:
                    coordinator_node.handle_annotate_request(session, payload)
            elif msg_type == Tmod.ERR:
                break
            if received_props is not None and received_records is not None:
                break

        if received_props is not None and received_records is not None:
            worker_results.append((cn, received_props, received_records))

    # Deterministic CN-based sort: sort worker outputs by (node CN, serialized bytes)
    worker_results.sort(key=lambda item: (item[0], item[1]))

    reversed_claims = M.EmptyList
    merged_store = coordinator_node.store

    for cn, prop_bytes, record_bytes in worker_results:
        verified_store = verify_incoming("proposals", prop_bytes, coordinator_node.version)
        if (
            M.IsPair(verified_store)() is M.truth_value
            and M.TermEqual(M.Head(verified_store)(), Lmod.ReasonNetworkLabel)()
            is M.truth_value
        ):
            continue
        verified_records = verify_incoming(
            "ledger_records", record_bytes, coordinator_node.version
        )
        if (
            M.IsPair(verified_records)() is M.truth_value
            and M.TermEqual(M.Head(verified_records)(), Lmod.ReasonNetworkLabel)()
            is M.truth_value
        ):
            continue

        reversed_claims = M.Pair(verified_records, reversed_claims)
        merged_store = verified_store

    worker_records = M.EmptyList
    while M.IdentityCompare(reversed_claims, M.EmptyList)() is M.false_value:
        worker_records = M.Pair(M.Head(reversed_claims)(), worker_records)
        reversed_claims = M.Tail(reversed_claims)()

    merged = Gmod.MergeFrontiers(
        coordinator_node.version,
        worker_records,
        coordinator_node.ledger,
    )()
    merged_version = M.Head(merged)()
    conflicts = M.Head(M.Tail(merged)())()

    gen_config = M.Pair(
        M.Pair(
            Gmod.AUTONOMY_GENERATOR_SLICE_INDEX_KEY,
            M.Pair(M.GMPRep("0"), M.EmptyList),
        ),
        M.Pair(
            M.Pair(
                Gmod.AUTONOMY_GENERATOR_SLICE_COUNT_KEY,
                M.Pair(M.GMPRep(slice_count_text), M.EmptyList),
            ),
            M.EmptyList,
        ),
    )

    prev_version = coordinator_node.version
    cycle_out = Gmod.AutonomyCycle(
        merged_version,
        merged_store,
        coordinator_node.ledger,
        budgets,
        gen_config,
    )()
    final_version = M.Head(cycle_out)()
    final_store = M.Head(M.Tail(cycle_out)())()
    report = M.Head(M.Tail(M.Tail(cycle_out)())())()

    coordinator_node.version = final_version
    coordinator_node.store = final_store

    fire_rec = M.Pair(M.Char("cycle-firing"), M.EmptyList)
    new_delta = Wmod.serialize_delta(prev_version, final_version, fire_rec)
    coordinator_node.record_history(final_version, new_delta)

    delta_frame_payload = Wmod.serialize_term(
        M.Pair(M.Char(new_delta.decode("latin1")), M.EmptyList)
    )
    for session in coordinator_node.connected_workers.values():
        Tmod.send_frame(session, Tmod.DELTAS, delta_frame_payload)

    return M.Pair(
        final_version,
        M.Pair(
            final_store,
            M.Pair(report, M.Pair(conflicts, M.EmptyList)),
        ),
    )
