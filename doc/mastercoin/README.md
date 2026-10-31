# Mastercoin

Mastercoin is a private-by-default, cheap transfer layer for tokens that already exist on the Omni ledger. Omni stays the base protocol: there is no chain split and no consensus change. A bridge takes an ordinary Omni send, credits the same amount on an existing off-chain Bitcoin protocol, and sends it back to Omni when the holder exits. Transfers on the layer are meant to be shared across one Bitcoin transaction and visible to the sender and the receiver, while a regulated issuer keeps a way to freeze and an auditor can be given a view key. This draft recommends RGB as the first protocol to bridge to. It is a proposal for the Omni team, not a shipped feature.

The design is in [DESIGN.md](DESIGN.md). Fees computed from the vbyte model are in [FEES.md](FEES.md). Regenerate the fee page's figures with `python3 contrib/mastercoin/size.py`.
