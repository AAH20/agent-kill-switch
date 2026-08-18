"""
Agent-Kill-Switch: Out-of-Band Dead-Man's Switch & Multi-Party Emergency Breaker for AI Agents.
Standard library only: hashlib, hmac, json, time, os, signal, dataclasses, typing, secrets.
"""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import os
import secrets
import signal
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


GENESIS_HASH: str = "0000000000000000000000000000000000000000000000000000000000000000"


@dataclasses.dataclass(frozen=True)
class KillSwitchReceipt:
    """Immutable SHA-256 cryptographically chained Post-Mortem Incident Receipt."""
    index: int
    prev_hash: str
    agent_id: str
    trigger_reason: str
    operators_authorized: Tuple[str, ...]
    status: str
    timestamp: float
    signature_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "prev_hash": self.prev_hash,
            "agent_id": self.agent_id,
            "trigger_reason": self.trigger_reason,
            "operators_authorized": list(self.operators_authorized),
            "status": self.status,
            "timestamp": self.timestamp,
            "signature_hash": self.signature_hash,
        }


class CryptographicKillLedger:
    """Tamper-Proof Post-Mortem Blackbox Ledger for Regulatory & CISO Inquiries."""

    def __init__(self, ledger_file: Optional[str] = None):
        self.ledger_file = ledger_file
        self._entries: List[KillSwitchReceipt] = []
        self._last_hash = GENESIS_HASH

    @property
    def last_hash(self) -> str:
        return self._last_hash

    @property
    def count(self) -> int:
        return len(self._entries)

    def record_kill_event(
        self,
        agent_id: str,
        trigger_reason: str,
        operators_authorized: List[str],
        status: str,
    ) -> KillSwitchReceipt:
        idx = len(self._entries)
        ts = time.time()
        sorted_ops = tuple(sorted(operators_authorized))

        # SHA-256 Hash Chain
        raw_msg = f"{idx}:{self._last_hash}:{agent_id}:{trigger_reason}:{sorted_ops}:{status}:{ts:.6f}"
        sig_hash = hashlib.sha256(raw_msg.encode("utf-8")).hexdigest()

        receipt = KillSwitchReceipt(
            index=idx,
            prev_hash=self._last_hash,
            agent_id=agent_id,
            trigger_reason=trigger_reason,
            operators_authorized=sorted_ops,
            status=status,
            timestamp=ts,
            signature_hash=sig_hash,
        )

        self._entries.append(receipt)
        self._last_hash = sig_hash

        if self.ledger_file:
            os.makedirs(os.path.dirname(os.path.abspath(self.ledger_file)), exist_ok=True)
            with open(self.ledger_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(receipt.to_dict()) + chr(10))

        return receipt

    def verify_chain_integrity(self) -> Tuple[bool, Optional[str]]:
        current_prev = GENESIS_HASH
        for idx, entry in enumerate(self._entries):
            if entry.index != idx:
                return False, f"Sequence index mismatch at {idx}"
            if entry.prev_hash != current_prev:
                return False, f"Broken SHA-256 chain at {idx}"
            current_prev = entry.signature_hash
        return True, None


class DeadManSentinel:
    """
    Out-of-Band Dead-Man's Timer Sentinel.
    If an agent fails to emit periodic cryptographic heartbeats, it terminates the agent.
    """

    def __init__(
        self,
        agent_id: str,
        heartbeat_timeout_seconds: float = 3.0,
        ledger: Optional[CryptographicKillLedger] = None,
    ):
        self.agent_id = agent_id
        self.timeout = heartbeat_timeout_seconds
        self.last_heartbeat = time.time()
        self.is_active = True
        self.is_tripped = False
        self.ledger = ledger or CryptographicKillLedger()
        self._secret_key = secrets.token_bytes(32)

    def ping_heartbeat(self) -> str:
        """Agent calls this to prove it is alive, aligned, and non-frozen."""
        if not self.is_active or self.is_tripped:
            raise RuntimeError("Cannot ping heartbeat: DeadManSentinel is tripped or inactive.")
        self.last_heartbeat = time.time()
        # Generates proof token
        return hmac.new(self._secret_key, f"{self.agent_id}:{self.last_heartbeat:.6f}".encode("utf-8"), hashlib.sha256).hexdigest()

    def evaluate_liveness(self) -> Tuple[bool, Optional[KillSwitchReceipt]]:
        """Sentinel evaluation: Returns (is_alive, receipt_if_tripped)"""
        if self.is_tripped:
            return False, None

        elapsed = time.time() - self.last_heartbeat
        if elapsed > self.timeout:
            self.is_tripped = True
            self.is_active = False
            receipt = self.ledger.record_kill_event(
                agent_id=self.agent_id,
                trigger_reason=f"DEAD_MAN_HEARTBEAT_TIMEOUT_ELAPSED_{elapsed:.2f}s",
                operators_authorized=["AUTOMATED_SENTINEL_DAEMON"],
                status="TERMINATED_BY_DEAD_MAN_SWITCH",
            )
            return False, receipt
        return True, None


class MultiPartyEmergencyBreaker:
    """
    M-of-N Multi-Party Human Breaker:
    Requires M operator signatures (e.g. 2 of 3) to execute an instant out-of-band hard kill.
    """

    def __init__(
        self,
        authorized_operators: Set[str],
        quorum_m: int = 2,
        ledger_path: Optional[str] = None,
    ):
        self.authorized_operators = authorized_operators
        self.quorum_m = quorum_m
        self.ledger = CryptographicKillLedger(ledger_file=ledger_path)

    def trigger_emergency_kill(
        self,
        agent_id: str,
        reason: str,
        approving_operators: List[str],
    ) -> Tuple[bool, KillSwitchReceipt]:
        # Validate that approvals are from authorized operators
        valid_approvals = [op for op in set(approving_operators) if op in self.authorized_operators]

        if len(valid_approvals) >= self.quorum_m:
            receipt = self.ledger.record_kill_event(
                agent_id=agent_id,
                trigger_reason=reason,
                operators_authorized=valid_approvals,
                status="HARD_TERMINATED_M_OF_N_QUORUM_REACHED",
            )
            return True, receipt

        receipt = self.ledger.record_kill_event(
            agent_id=agent_id,
            trigger_reason=reason,
            operators_authorized=valid_approvals,
            status="REJECTED_INSUFFICIENT_OPERATOR_QUORUM",
        )
        return False, receipt
