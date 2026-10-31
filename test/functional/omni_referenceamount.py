#!/usr/bin/env python3
# Copyright (c) 2026 The Omni Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test the bitcoin amount of the reference (receiver) output of Omni sends.

The reference output carries the "Omni dust" amount, which is three times the
Bitcoin Core dust threshold at -minrelaytxfee (default 1000 sat/kvB), as in
Omni Core 0.12 and earlier:

- P2PKH:  3 * 182 * 1000 / 1000 = 546 sat
- P2WPKH: 3 *  98 * 1000 / 1000 = 294 sat

It must follow -minrelaytxfee. It must not be based on DUST_RELAY_TX_FEE
(3000 sat/kvB), which would triple it again (1638 sat for P2PKH).
"""

from decimal import Decimal

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

SAT = Decimal("0.00000001")


class OmniReferenceAmountTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def reference_value(self, node, txid, receiver):
        tx = node.decoderawtransaction(node.gettransaction(txid)["hex"])
        values = [vout["value"] for vout in tx["vout"]
                  if vout["scriptPubKey"].get("address") == receiver]
        assert_equal(len(values), 1)
        return int(values[0] / SAT)

    def send_and_get_reference(self, node, sender, address_type):
        receiver = node.getnewaddress("", address_type)
        txid = node.omni_send(sender, receiver, 1, "1")
        self.generatetoaddress(node, 1, sender)
        assert_equal(node.omni_gettransaction(txid)["valid"], True)
        return self.reference_value(node, txid, receiver)

    def run_test(self):
        node = self.nodes[0]
        sender = node.getnewaddress("", "legacy")
        self.generatetoaddress(node, 110, sender)
        # Get some OMNI from the regtest moneyman address
        node.sendmany("", {"moneyqMan7uh8FqdCA2BV5yZ8qVrc9ikLP": 10, sender: 4})
        self.generatetoaddress(node, 1, sender)

        self.log.info("Reference outputs use 3x the dust threshold at the default -minrelaytxfee")
        assert_equal(self.send_and_get_reference(node, sender, "legacy"), 546)
        assert_equal(self.send_and_get_reference(node, sender, "bech32"), 294)

        self.log.info("Reference outputs follow -minrelaytxfee")
        self.restart_node(0, ["-minrelaytxfee=0.00002"])
        assert_equal(self.send_and_get_reference(node, sender, "legacy"), 1092)


if __name__ == '__main__':
    OmniReferenceAmountTest().main()
