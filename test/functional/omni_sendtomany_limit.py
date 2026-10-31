#!/usr/bin/env python3
# Copyright (c) 2026 The Omni Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test the receiver limit of omni_sendtomany.

Send-to-many is created as Class C (OP_RETURN) transaction. With the default
-datacarriersize of 83 bytes, up to 7 receivers fit. More receivers must fail
with a clear error instead of falling back to Class B (bare multisig), and
raising -datacarriersize allows more receivers in Class C.
"""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal, assert_raises_rpc_error


class OmniSendToManyLimitTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def send_to_many(self, node, sender, receivers):
        mapping = [{"address": r, "amount": "1"} for r in receivers]
        txid = node.omni_sendtomany(sender, 1, mapping)
        self.generatetoaddress(node, 1, sender)
        assert_equal(node.omni_gettransaction(txid)["valid"], True)
        tx = node.decoderawtransaction(node.gettransaction(txid)["hex"])
        types = [vout["scriptPubKey"]["type"] for vout in tx["vout"]]
        assert_equal(types.count("nulldata"), 1)
        assert_equal(types.count("multisig"), 0)
        for receiver in receivers:
            assert_equal(node.omni_getbalance(receiver, 1)["balance"], "1.00000000")

    def run_test(self):
        node = self.nodes[0]
        sender = node.getnewaddress("", "legacy")
        self.generatetoaddress(node, 110, sender)
        # Get some OMNI from the regtest moneyman address
        node.sendmany("", {"moneyqMan7uh8FqdCA2BV5yZ8qVrc9ikLP": 10, sender: 4})
        self.generatetoaddress(node, 1, sender)

        self.log.info("7 receivers fit into one Class C transaction")
        self.send_to_many(node, sender, [node.getnewaddress("", "legacy") for _ in range(7)])

        self.log.info("8 receivers fail with a clear error instead of using Class B")
        receivers = [node.getnewaddress("", "legacy") for _ in range(8)]
        mapping = [{"address": r, "amount": "1"} for r in receivers]
        assert_raises_rpc_error(-8, "Send at most 7 receivers per transaction", node.omni_sendtomany, sender, 1, mapping)

        self.log.info("Raising -datacarriersize allows more receivers in Class C")
        self.restart_node(0, ["-datacarriersize=200"])
        self.send_to_many(node, sender, receivers)

        self.log.info("Without OP_RETURN, send-to-many fails")
        self.restart_node(0, ["-datacarrier=0"])
        assert_raises_rpc_error(-8, "requires Class C", node.omni_sendtomany, sender, 1,
                                [{"address": node.getnewaddress("", "legacy"), "amount": "1"}])


if __name__ == '__main__':
    OmniSendToManyLimitTest().main()
