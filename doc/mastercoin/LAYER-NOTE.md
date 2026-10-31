# Layer note: a base for provable privacy

Draft, October 2026. Builds on [DESIGN.md](DESIGN.md) and [FEES.md](FEES.md). Omni stays the ledger. The bar is privacy that is private by default and provable, transfers that stay cheap, and a receiver path with little ceremony. Fees at 2 and 20 sat/vB are from `python3 contrib/mastercoin/size.py` unless a cell says the figure is cited. Estimates are marked. No OMNI price.

## Which base to reuse

RGB, Ark, and Taproot Assets are running code. The shielded row is a Zcash-style note, nullifier, and zero-knowledge spend. The specification read here is Shielded Bitcoin (Shikhelman, Komarov, Moskvin, 24 September 2026), which publishes each envelope on Bitcoin. A federation, or a BitVM-style bridge, is how the same pool can sit off to the side. The paper treats both as boundary designs. Its peg is out of scope.

| | Chain observer | Operator | Per transfer at 2 and 20 sat/vB | UX | Maturity and licence |
| --- | --- | --- | --- | --- | --- |
| RGB | Tapret: no asset payload in the transaction (v0.12 note, 20 May 2025). OP_RETURN seal: a visible 32-byte commitment. | Not a party to a direct handoff. | **Estimate.** Script: 154 vB tapret tx, assumed split by 100: **3.08 sat** and **30.8 sat**. Real witnesses can be larger. | Receiver must receive and store the consignment. Losing it loses the spend. No operator liveness for the handoff. The seal needs Bitcoin. | `RGB-WG/rgb-core` **v0.12.0** (10 Jul 2025) says mainnet issuance is allowed. `RGB-WG/rgb` latest release **v0.12.0-rc.2** (3 Jun 2025). `rgb-protocol/rgb-consensus` **0.11.2-rc.1** (9 Oct 2026). All three `LICENSE` files are Apache-2.0. `RGB-WG/yellowpaper` has no `LICENSE`. |
| Ark | The round transaction, plus a user's branch if they exit unilaterally ([Optech](https://bitcoinops.org/en/topics/ark/)). | Co-signs and sees payments. Sender plus operator can double-spend until the next round. | **Not measured.** No round vsize found. Floor **estimate** if a round were that 154 vB tx / 100: same 3.08 / 30.8 sat. A real round is larger. | Operator must be online to pay. Refresh before the VTXO timelock. Backup is the pre-signed branch. | `arkade-os/arkd` **v0.9.16** (25 Aug 2026). README lists mainnet. MIT `LICENSE` (copyright 2024 Ark Labs). |
| Taproot Assets | A Taproot transaction. Amounts are in off-chain proofs. Confidential transfers are listed as future work. | A universe operator sees uploaded proofs. A pocket universe holds the on-chain key, not the asset keys ([FAQ](https://docs.lightning.engineering/the-lightning-network/taproot-assets/faq)). | **Estimate,** same 3.08 / 30.8 sat under the same 100-way split. A lone asset transaction was not measured. No routing fee is stated here. | Receiver needs the proof. A universe can deliver it later; that upload is visible to its operator. README: back up `tapd` data. | Mainnet since **v0.3.0** (18 Oct 2023). Latest **v0.8.8** (22 Oct 2026). README: still alpha. MIT `LICENSE` (copyright 2022 Lightning Labs). |
| Shielded pool | **L1 profile:** nullifiers, ciphertexts, proof, carrier tx. Amount and parties are not plaintext. Timing, input/output counts, fee, and the carrier's inputs stay public (paper). **Federation:** chain sees pegs only, if transfers are not published. | **L1:** indexers see envelopes, not plaintext, and hold no spend key (abstract). **Federation:** operators see the log they keep. BitVM is a comparison point in the paper, not a shipped peg. | **L1, script,** paper's 610-byte envelope in one P2TR-in, 625-byte OP_RETURN, P2TR change: **736 vB**, **1,472 sat** and **14,720 sat**. Table 4's witness pair is **438 vB cited**; ×2 and ×20 is **876** and **8,760 sat**, not a fee in the paper. **Estimate,** unpublished federation transfers: **0 sat**. P2WPKH Omni peg, script: 172 vB, **344** and **3,440 sat** each way. | L1: receiver scans; they need not be in the tx. Chain stores envelopes; seed decrypts. Claims need an honest setup whose trapdoor is gone (assumption A3). Federation must be live to accept and to peg out. | Paper, 24 Sep 2026, no licence text. `bitsagarob/shielded-btc-probe`: Apache-2.0 `LICENSE-APACHE`; README says mainnet and signet, public Groth16 seed, insecure, not usable. `77ph/shielded-bitcoin`: no license file. `BitVM/BitVM` **v0.1.2-dev** (16 Dec 2025), MIT. |

This tree rejects a null-data script above 83 bytes (`MAX_OP_RETURN_RELAY`). The paper's 614-byte OP_RETURN needs Bitcoin Core 30's default `-datacarriersize` of 100,000, which is policy, not consensus. The 736 vB figure is this script, not a transaction seen on mainnet. The paper's 154 vB prepay row matches this script's tapret anchor. The 284 vB reveal was not recomputed.

**Recommendation.** Do not reuse RGB, Ark, or Taproot Assets as the privacy mechanism. None proves a spend is unlinkable inside an anonymity set. Ark fails because the operator co-signs. Taproot Assets fails when proofs sit on a universe, and amounts are not hidden in the current docs. RGB is still the best existing handoff if a proof system is not ready.

Reuse the shielded **statement** (encrypted note, public nullifier, zero-knowledge membership and value conservation). Do not reuse Shielded Bitcoin's per-transfer publication: 736 vB, or the cited 438 vB pair, is a full Bitcoin fee every payment. For the proof of concept, run the statement in a small federation so an in-pool transfer creates no Bitcoin transaction, and peg with ordinary Omni sends. BitVM is how that federation's trust could shrink later, not the first build. If a second implementation will not accept the proof, stop and use RGB for a private hop that is checked by absence of payload, not by a zero-knowledge statement.

## What "provable" means

**Cryptographic.** A verifier accepts a spend only when the public statement holds, and the statement omits sender, receiver, and amount. For a note pool that statement is: the nullifiers open notes in the commitment tree, those notes are unspent, the spender is authorized, and inputs conserve to outputs, without naming the leaf or the value. That is unlinkability inside the tree the proof covers, amount hiding, and no plaintext graph on the envelope. The set's size is itself public. A proof against a one-note tree hides nothing. Shielded Bitcoin states this, and states what stays public: timing, arity, fees, carrier metadata. Assumption A3: the claims hold only if the common reference string was generated honestly and the trapdoor is unavailable. The probe's public Groth16 seed breaks that on purpose. A proof under that setup is not evidence.

**Checked, not proved.** RGB tapret is real: read the transaction and the asset payload is absent. There is no anonymity set, and the receiver of a consignment sees the history they were handed. That is inspection, not a proof of unlinkability.

**Auditable.** A public spec, a second implementation that replays the same chain to the same root, reproducible builds, and a review of the circuit against the spec. Those bind software to a document. They do not make a false statement true. The paper's replay rule is the audit hook. RGB's yellowpaper is a spec repo, and it has no `LICENSE` file.

A view key is selective disclosure. It is not a proof that the issuer learned nothing. Freeze and an honest peg-out are watched on Omni and against published liabilities. They are not zero-knowledge statements.

## In, out, and OMNI

Peg-in and peg-out are ordinary Omni sends. Class C debits the first input's address. The pooled M-of-N, the missing unilateral exit, and the later pre-signed refund are in [DESIGN.md](DESIGN.md). The carrier that funds a peg can still be tied to the Omni address that sent it. In-pool privacy starts after the peg and ends at the next one. If operators stop, a pooled reserve does not move. The proof of concept has to show that, not hide it.

Shielded Bitcoin does not define the boundary. It says a federation and a BitVM-style bridge differ in custody and liveness, and it does not claim entry or exit is trustless or private. `BitVM/BitVM` `v0.1.2-dev` (16 December 2025, MIT) is not the first exit.

**OMNI, with no price and no amount.** A voluntary OMNI send to the operators needs no consensus change. OMNI left at a published address is a bond users can see. Consensus will not slash it. A mandatory fee would be a consensus change and is not in this note.

## Smallest proof of concept

Signet for Bitcoin, Omni testnet or signet for the tokens. No consensus patch.

**Components.** Signet bitcoind. Three operator keys and one process holding the note tree and nullifier set. Two wallets (seed plus scanner). One circuit, labeled insecure if the trapdoor exists, so the run measures plumbing rather than soundness. An Omni simple send into a 2-of-3 address and one send back. Optionally, one 610-byte envelope, to compare a real transaction with the script's 736 vB.

**Scope.** One test property, two wallets, about ten in-pool transfers, one peg each way, one halt of two operators. Not a wallet product and not BitVM.

**Measure, and label the script figures as the hypothesis.**

- **vB and fees.** Actual virtual size and satoshis for each peg, each in-pool transfer, and the envelope. Hypothesis: peg 172 vB, in-pool 0 vB, carrier 736 vB.
- **Observer-visible data.** Raw peg hex and, if published, the envelope's nullifiers, counts, and fee. Write what a stranger learns.
- **Receiver latency.** Submit until the receiver can spend, once online and once scanning later.
- **Failure.** With two operators stopped, does a peg-out confirm? If a pre-signed refund exists, does Omni accept it? If not, the result is that the reserve did not move.

Replace the estimates above with those measurements before any mainnet talk.

## Sources read for this note

Script and `MAX_OP_RETURN_RELAY`: this repo. Shielded Bitcoin PDF (24 Sep 2026): <https://www.allocinit.xyz/uploads/shielded-bitcoin.pdf>. RGB tapret: <https://rgb.tech/blog/release-v0-12-rc-1/>. Releases and `LICENSE` files: `RGB-WG/rgb`, `RGB-WG/rgb-core`, `rgb-protocol/rgb-consensus`, `arkade-os/arkd`, `lightninglabs/taproot-assets`, `BitVM/BitVM`, `bitsagarob/shielded-btc-probe` (`LICENSE-APACHE`). Ark behaviour: <https://bitcoinops.org/en/topics/ark/>. Taproot Assets FAQ: <https://docs.lightning.engineering/the-lightning-network/taproot-assets/faq>. Core 30 datacarrier: <https://bitcoincore.org/en/releases/30.0/>.
