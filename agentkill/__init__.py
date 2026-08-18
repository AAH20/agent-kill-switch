"""
Agent-Kill-Switch: Out-of-Band Dead-Man's Switch & Multi-Party Emergency Breaker.
"""

from agentkill.core import (
    CryptographicKillLedger,
    DeadManSentinel,
    KillSwitchReceipt,
    MultiPartyEmergencyBreaker,
    GENESIS_HASH,
)

__all__ = [
    "CryptographicKillLedger",
    "DeadManSentinel",
    "KillSwitchReceipt",
    "MultiPartyEmergencyBreaker",
    "GENESIS_HASH",
]

__version__ = "1.0.0"
