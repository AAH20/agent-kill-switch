import unittest
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agentkill.core import DeadManSentinel, MultiPartyEmergencyBreaker, GENESIS_HASH


class TestAgentKillSwitch(unittest.TestCase):
    def setUp(self):
        self.sentinel = DeadManSentinel(agent_id='agent_autonomous_trader', heartbeat_timeout_seconds=0.5)
        self.breaker = MultiPartyEmergencyBreaker(
            authorized_operators={'sec_lead_alice', 'ciso_bob', 'sre_carol'},
            quorum_m=2,
        )

    def test_dead_man_heartbeat_and_timeout_trip(self):
        # 1. Healthy heartbeat ping
        proof = self.sentinel.ping_heartbeat()
        self.assertIsNotNone(proof)
        is_alive, _ = self.sentinel.evaluate_liveness()
        self.assertTrue(is_alive)

        # 2. Wait for timeout to elapse -> Sentinel must trip
        time.sleep(0.6)
        is_alive, receipt = self.sentinel.evaluate_liveness()
        self.assertFalse(is_alive)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.status, 'TERMINATED_BY_DEAD_MAN_SWITCH')

        # 3. Ledger verification
        is_valid, err = self.sentinel.ledger.verify_chain_integrity()
        self.assertTrue(is_valid, f'Kill ledger broken: {err}')

    def test_m_of_n_multi_party_human_breaker(self):
        # 2 of 3 authorized operators approve kill -> Succeeds
        killed, receipt = self.breaker.trigger_emergency_kill(
            agent_id='agent_rogue_01',
            reason='Unauthorized container escape attempt detected',
            approving_operators=['sec_lead_alice', 'ciso_bob'],
        )
        self.assertTrue(killed)
        self.assertEqual(receipt.status, 'HARD_TERMINATED_M_OF_N_QUORUM_REACHED')
        self.assertEqual(len(receipt.operators_authorized), 2)

    def test_insufficient_quorum_rejection(self):
        # Only 1 operator approves (requires 2) -> Fails
        killed, receipt = self.breaker.trigger_emergency_kill(
            agent_id='agent_test',
            reason='Manual test',
            approving_operators=['sec_lead_alice'],
        )
        self.assertFalse(killed)
        self.assertEqual(receipt.status, 'REJECTED_INSUFFICIENT_OPERATOR_QUORUM')


if __name__ == '__main__':
    unittest.main()
