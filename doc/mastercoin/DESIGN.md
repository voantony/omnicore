# Mastercoin: a private, cheap layer on the Omni ledger

Draft for the Omni team, October 2026. This describes a layer named Mastercoin. It does not change Omni consensus, it does not split the chain, and it does not ship a bridge.

Mastercoin is the name of a transfer layer for tokens that are already Omni properties. Omni remains the ledger of record. Holders who want a cheap, private payment move value across a bridge into an existing Bitcoin protocol (the candidate set is RGB, Taproot Assets, and Ark) and back to Omni for settlement. The layer is private by default: a transfer is for the sender and the receiver. It is still usable by a regulated stablecoin issuer, which means the issuer can freeze and an auditor can be shown the transfers without publishing them to the world.

Numbers for transaction size and fees live in [FEES.md](FEES.md) and are produced by `contrib/mastercoin/size.py`. Anything that depends on how many transfers share one Bitcoin transaction is an estimate. This text does not set a price for OMNI and does not claim a measured mainnet size for an RGB, Taproot Assets, or Ark transaction.

This is an engineering reading of public rules and protocol docs, not a legal opinion.

## Goals

1. **Cheap transfers.** An Omni simple send is a full Bitcoin transaction. In the model, one input and a Class C simple send are 257 vB (P2PKH) or 197 vB (P2SH-P2WPKH). At 2 sat/vB that is 514 or 394 satoshis, before the bitcoin that must sit in the outputs as dust. Send-to-many lowers the per-recipient share, and it is still one on-chain transaction per batch. Mastercoin's marginal transfer is an even share of one anchor transaction. The lower-bound estimate is a 154 vB Taproot transaction shared by many transfers (1.54 vB and 3.08 satoshis at 2 sat/vB if 100 transfers share it). That estimate is not a measurement. See [FEES.md](FEES.md).
2. **Private by default.** Chain observers do not learn the sender, receiver, or amount of a layer transfer. The sender and the receiver do.
3. **The same Omni ledger.** Balances that matter for settlement are Omni balances. The layer is a claim on tokens held at a bridge. Issuance, grant, revoke, and the public Omni history stay where they are.
4. **No consensus change and no chain split.** Peg-in and peg-out are ordinary Omni transactions. Nodes that do not run any Mastercoin software stay in consensus.
5. **Issuer freeze, and a view key for an auditor.** A payment stablecoin that a US permitted issuer can stand behind has to be freezable when a lawful order says so. A crypto-asset service provider in the EU has to be able to know whose account it is keeping. Both are specified below, with the sources.
6. **A way out when an operator fails.** The minimum is a published federation and a refund path. A stronger exit, modeled on Ark's pre-signed unilateral exit, is a later phase and still uses ordinary Omni transactions.

## Why the ledger stays Omni

The ledger is the one these nodes already apply. On this branch the Exodus deadline in `src/omnicore/rules.cpp` is Unix time 1377993600 (1 September 2013), and the consensus code still uses the Mastercoin names (`MSC_` constants, the `mastercore` namespace). A split would be a second set of rules and a second consensus hash. Exchanges, issuers, and existing holders would have to pick a side, and every balance would have to be mapped. Nothing in the cost problem requires that. The cost problem is that every transfer is published as its own Bitcoin transaction. Moving the hot transfers off the publication path, and settling back onto Omni, leaves the consensus hash, the property IDs, and the existing freeze rules in place.

The features that are still gated on block 999,999 on `develop` (commit `9352212e8`) are a release problem for Omni Core, not a reason to fork. On that commit, mainnet `WITNESS_V0_BLOCK`, `WITNESS_V1_BLOCK`, and `MSC_SEND_TO_MANY_BLOCK` are all 999,999 (`src/omnicore/rules.cpp`). Native SegWit, Taproot, and send-to-many are cheaper ways to *publish* an Omni transaction. They are worth activating. They do not make a single recipient's payment share a Bitcoin fee with a hundred other payments. That is what the layer is for. The bridge can be prototyped with today's P2PKH and P2SH simple sends, which mainnet already accepts.

"Lock" on Omni means the tokens sit on a Bitcoin address the holder does not unilaterally spend. Omni associates a balance with an address. For a Class C transaction the sender is the address of the first input (`src/omnicore/omnicore.cpp`, the branch that handles `OMNI_CLASS_C`). There is no covenant in current Omni that freezes a balance without a key that can spend. The bridge's lock is therefore a Bitcoin script: a multisig the operator set holds. P2SH has been standard on mainnet since block 322,000 (`SCRIPTHASH_BLOCK` in `src/omnicore/rules.cpp` on this branch).

## Bridge

### Peg-in

1. The user makes an ordinary Omni send of property `P` and amount `A` to the bridge address. The reference output is that address. The simplest payload is a Class C simple send. Send-to-many can batch several peg-ins once it is active.
2. The bridge credits a layer claim of `P`/`A` to the endpoint the user named, after the Omni transaction has as many confirmations as the operator's published policy requires. This document does not pick that depth.
3. Omni supply of `P` does not change. The bridge address's Omni balance is the reserve. Outstanding layer claims are liabilities against that reserve. They are not a second issuance.

A peg-in is public. Anyone who reads the Omni ledger can see the property, the amount, the sending address, and the bridge address.

### Peg-out

1. The holder asks the bridge to retire a layer claim.
2. A threshold of bridge signers creates an ordinary Omni send from the bridge address to the holder's Omni address, for the amount retired.
3. The layer claim is retired in the same step the signers are willing to sign. If the Omni send confirms and the claim is not retired, the reserve and the liabilities diverge. If the claim is retired and the Omni send never confirms, the holder has lost the layer claim and not received the tokens. The operational rule is: retire the claim only when the peg-out is signed and broadcast, and be able to re-credit if it is dropped from the mempool. The exact state machine is an open question.

### Who operates it

A small published set of signers, the bridge operators. They are not miners and they have no role in Omni consensus. The bridge address is an M-of-N multisig. Spending the reserve, which is what a peg-out is, needs M signatures.

The software that watches Omni and talks to the layer should be a separate program. It should not be a consensus change inside Omni Core. Omni Core already has a long review path, and a bridge has its own failure modes.

### Trust

In the pooled design the holders trust that M signers will sign honest peg-outs and will not send the reserve to themselves. They do not have a unilateral Omni transaction that recovers the reserve if the signers refuse. Bitcoin confirmations protect them against a peg-in that gets reorged only if the operator waits. The layer's own rules protect them against a double spend of the layer claim only to the extent that protocol provides. RGB's single-use seals are that mechanism for the recommended target. They do not move the Omni reserve.

A chain observer trusts nothing about the layer. The observer trusts Omni for the reserve, which is public, and cannot see the liabilities unless the bridge publishes them.

### Failure and exit

**Signers stop, or refuse.** In the pooled design the tokens remain on the bridge address. Users cannot force a peg-out. This is the main residual risk and it should be said in anything the bridge shows a user.

**Signers take the reserve.** Same mechanics as a refusal. An OMNI bond that users can see is a proposal in the section below. Current consensus will not slash it.

**Issuer freezes the bridge address.** Freeze on a managed property stops the frozen address from sending. The RPC for `omni_createpayload_freeze` states that the amount is unused and that a frozen address cannot send. `logicMath_FreezeTokens` in `src/omnicore/tx.cpp` records the address as frozen; the sender must be the issuer or the delegate. Freezing the bridge address stops every peg-out. That is an emergency halt of the reserve, not a way to freeze one user. Freezing a user's Omni address does not stop the bridge from sending *to* that user. It stops that user from sending onward once the tokens are back on Omni.

**Peg-in reorg.** If the operator credited the layer before the Omni send was stable, the layer liabilities exceed the reserve. The mitigation is the published confirmation depth.

**Lost layer history.** On a client-validated protocol the receiver has to keep the proof. A holder who loses it cannot show the claim to the next person or to the bridge. The Omni reserve is unchanged until a peg-out. Backup is part of choosing RGB.

**Stronger exit, later, still without a consensus change.** Each peg-in goes to its own 2-of-2 address (user and operator). Before broadcasting, they pre-sign an Omni Class C simple send that pays the user back, with a Bitcoin `nLockTime`, spending the outpoint at that address. Because a Class C sender is the first input's address, that refund debits the deposit address. The operator cannot move the deposit alone. When the claim changes hands on the layer, the old refund has to be replaced by one that pays the new holder, co-signed by the operator. That is the same shape as an Ark refresh: the operator co-signs, and if the operator disappears the last co-signed refund can be broadcast after the lock time. Designing the fee input, the change output, and the dust so the pre-signed transaction still meets relay rules is open work. It is not something this draft claims a wallet can do.

## Privacy

Privacy starts after a peg-in confirms and ends at peg-out. The Omni ledger itself stays public. A chain observer who watches the bridge learns how much of property `P` entered and left, and which Omni addresses touched the bridge. The observer does not, on the recommended design, learn who paid whom in between.

| Who | What they see |
| --- | --- |
| Sender | The receiver, the amount, and their own layer state. |
| Receiver | The incoming transfer and whatever history the proof carries. On RGB that is the consignment the receiver verifies. It can be more than the latest hop, unless a compression proof replaces the history. |
| Bridge operators | Every peg-in and peg-out, because those are Omni transactions to or from their address. They see a layer transfer only if the protocol makes them a party to it. The recommended target does not. Ark does. |
| Chain observer | The Omni pegs, in full. The Bitcoin anchor: either an ordinary-looking Taproot transaction (tapret) or a transaction with a visible 32-byte commitment (OP_RETURN). Not the layer's sender, receiver, or amount. |
| Issuer with a view key | The layer transfers for that property, plus everything the issuer already sees on the public Omni ledger. |
| Auditor with a view key | The same layer transfers, if the issuer or the bridge has given them a key. They do not need to be a bridge signer. |
| Other users | Their own transfers. Not other people's. |
| Universe or directory operator | Whatever proofs users choose to upload. A public Taproot Assets universe is an extra observer. RGB does not require one for a direct handoff of a consignment. |

The pitch's line, "only the sender and the receiver see the transfer," is the goal for the layer hop. It is not true of the peg, and it is not automatically true of the receiver's proof if that proof contains earlier hops. Those two leaks should be written into any user-facing description.

## Issuer freeze and auditor view keys

### What Omni already does

Managed properties can already be frozen on mainnet. Transaction type 185 freezes an address for one property. The issuer or the delegate must send it. The amount field is unused: the whole address is frozen for that property, and a frozen address cannot send. Type 186 unfreezes. That is the right on-ledger tool, and Mastercoin does not replace it. It is not enough on its own, because a layer transfer is not an Omni transaction, so an Omni freeze of a user address does not by itself stop a layer payment.

### What the layer has to add

For a property whose issuer opts in:

- The issuer can mark a layer holding frozen, so an honest wallet will not accept it and the bridge will not peg it out.
- The issuer can lift that freeze.
- A view key, held by the issuer and shareable with an auditor, reveals that property's layer transfers to the key holder and to nobody else.
- Chain observers still do not see those transfers.
- The bridge address is not the freeze handle for a single user. Freezing it halts the reserve.

The cryptographic form of the view key is not chosen here. It might be a decryption key over transfer data, or a credential that lets a server the issuer runs open a proof. Picking a scheme is open work. Publishing the transfers to meet the rules below would throw away the privacy goal. The rules cited here require the *issuer or the service provider* to be able to act and to know their customer. They do not require the world to see the graph.

A freeze that honest software enforces, but that two colluding clients can ignore, is not enough for a regulated issuer. The bridge must refuse to peg out a frozen claim, and the layer's validation rules must make a frozen claim unspendable to any client that follows the contract. How to write that in RGB, or in a Taproot Asset script, without the issuer co-signing every payment, is the main open technical question. None of the three projects' documents read for this draft describe a finished "issuer freeze" feature.

### United States: GENIUS Act

Public Law 119-27, the Guiding and Establishing National Innovation for U.S. Stablecoins Act, was approved on 18 July 2025. The text below is from the [enrolled public law PDF](https://www.congress.gov/119/plaws/publ27/PLAW-119publ27.pdf).

Section 2(16) defines a "lawful order" as a final order, issued under federal law by a court or an authorized federal agency, that:

> (A) requires a person to seize, freeze, burn, or prevent the transfer of payment stablecoins issued by the person;
> (B) specifies the payment stablecoins or accounts subject to blocking with reasonable particularity; and
> (C) is subject to judicial or administrative review or appeal as provided by law.

Section 4(a)(5)(A) treats a permitted payment stablecoin issuer as a financial institution for Bank Secrecy Act purposes. The required program includes, at (iv), "technical capabilities, policies, and procedures to block, freeze, and reject specific or impermissible transactions that violate Federal or State laws, rules, or regulations."

Section 4(a)(6)(B): "A permitted payment stablecoin issuer may issue payment stablecoins only if the issuer has the technological capability to comply, and will comply, with the terms of any lawful order."

Section 20: the Act takes effect on the earlier of 18 months after enactment, or 120 days after the primary federal payment stablecoin regulators issue final implementing regulations. This draft does not try to say which of those dates will come first.

The White House fact sheet of 18 July 2025 summarizes the same point as: "All stablecoin issuers must possess the technical capability to seize, freeze, or burn payment stablecoins when legally required and must comply with lawful orders to do so." The statutory text above is the one to build against. The fact sheet is here: <https://www.whitehouse.gov/fact-sheets/2025/07/fact-sheet-president-donald-j-trump-signs-genius-act-into-law/>.

A layer that cannot freeze, burn, or stop a transfer of the issuer's own stablecoin cannot be the place that issuer uses, once this duty applies to them.

### European Union: anonymous accounts from 10 July 2027

Regulation (EU) 2024/1624 is the AML Regulation. EUR-Lex presented a bot challenge when this draft was written, so the article text below is taken from Transparency International EU's compilation of the legislative text, [European Union's legislative framework on virtual assets](https://transparency.eu/wp-content/uploads/2026/06/1.1-European-Unions-legislative-framework-on-virtual-assets-crypto-.pdf) (June 2026). Norton Rose Fulbright's note [The new EU AML/CFT regime has arrived](https://www.nortonrosefulbright.com/en/knowledge/publications/644c5392/the-new-eu-amlcft-regime-has-arrived-are-you-ready) (9 July 2024) states the same article and the application date.

Article 79(1), as printed in that compilation:

> Credit institutions, financial institutions and crypto-asset service providers shall be prohibited from keeping anonymous bank and payment accounts, anonymous passbooks, anonymous safe-deposit boxes or anonymous crypto-asset accounts as well as any account otherwise allowing for the anonymisation of the customer account holder or the anonymisation or increased obfuscation of transactions, including through anonymity-enhancing coins.

The compilation then prints the accompanying recital. Norton Rose Fulbright attributes the carve-out to Recital 160 and Article 79. The recital text in the compilation:

> That prohibition does not apply to providers of hardware and software or providers of self-hosted wallets insofar as they do not possess access to or control over those crypto-asset wallets.

Norton Rose Fulbright states that the AML Regulation entered into force on 9 July 2024 and applies from 10 July 2027, except for the obliged entities in Article 3(3)(n) and (o), to which it applies from 10 July 2029. The Transparency International compilation says application is 10 July 2027, with certain sectoral deferrals.

Read as engineering requirements, two different cases follow.

- A self-hosted wallet whose provider never has access to or control of the wallet is outside that prohibition, on the recital's own terms. Private-by-default transfers between such wallets are compatible with the text we have.
- A bridge operator or an issuer that *keeps accounts* for customers is in the prohibition if they are a crypto-asset service provider, a credit institution, or a financial institution. They cannot keep those accounts anonymous, and they cannot offer an account whose purpose is to anonymise the holder or to obfuscate transactions, including through an anonymity-enhancing coin. A view key, or an account the operator can attribute to a customer, is what lets them meet that duty without putting the graph on Bitcoin. Whether a given bridge operator *is* a crypto-asset service provider is a legal question. This draft does not answer it.

"Anonymous account" and "chain observers cannot see a transfer" are different. The layer can be opaque to the chain and still identifiable to the issuer and the auditor. That is the combination the goals ask for.

## RGB, Taproot Assets, and Ark

### RGB

RGB is a client-side validation protocol. The receiver verifies the contract operation. Bitcoin is the anchor: a single-use seal is tied to a Bitcoin transaction so the same state cannot be committed twice. The LNP/BP Standards Association's [v0.12 release candidate note](https://rgb.tech/blog/release-v0-12-rc-1/) (20 May 2025) says a tapret seal "can't be seen inside a bitcoin transaction," and that the older OP_RETURN seal puts a 32-byte commitment on-chain, at a higher fee and with "exposure to chain analysis." The same note says v0.12 is built so history can be compressed with a zk-STARK proof, and that contracts from before this release are not compatible. It is a release candidate in that post, not a claim that every wallet has the compression.

Tether's announcement of [28 August 2025](https://tether.io/news/tether-to-launch-usdt-on-rgb-expanding-native-bitcoin-stablecoin-support/) says RGB had reached mainnet at version 0.11.1 and that Tether plans to issue USD₮ on it, as a private, user-controlled asset that can sit in the same wallet as bitcoin. Tether's [17 August 2023 transition note](https://tether.io/news/tether-makes-strategic-transition-to-meet-community-demands-and-foster-innovation/) had already stopped minting USD₮ on Omni, Kusama, and Bitcoin Cash SLP, and said Tether was contributing to RGB. Those posts do not describe issuer freeze or an auditor view key.

What a chain observer sees, for a tapret transfer, is a Bitcoin transaction with no RGB payload in it. The sender and receiver see the consignment. A bridge operator sees it only if someone sends it to them. Receivers have to store the proof. Version choice matters: 0.11.1 is what Tether named for mainnet, and 0.12 RC1 says earlier contracts will not carry over.

### Taproot Assets

Taproot Assets, from Lightning Labs, commits asset state into a Taproot output with a Merkle sum tree and keeps the witness data off-chain. Their [overview](https://docs.lightning.engineering/the-lightning-network/taproot-assets) says assets can be deposited into Lightning channels and moved over the existing Lightning Network, and that clients verify the lineage back to the genesis output. Confidential transactions and zero-knowledge proofs are listed there as possible future features, so privacy of the amount is not described as the current default.

Their [FAQ](https://docs.lightning.engineering/the-lightning-network/taproot-assets/faq) says a universe is a repository of issuance data and proofs, and that "the criteria for releasing this information is up to a universe or universe operator." A public universe is an observer. A pocket universe batches transfers: one party or a federation holds the Taproot key of the UTXO and does not hold the asset keys. Asset scripts are described as programmable in a way similar to Bitcoin scripts. The FAQ does not describe a finished freeze or a view key. Lightning Labs says stablecoins are the first use they are prioritising.

A chain observer sees Taproot transactions. Someone with the proofs, including a universe they sync, can see the asset graph those proofs cover. The operator of a pocket universe sees the batch they co-ordinate, because they hold the on-chain key, and does not by themselves hold the asset keys.

### Ark

Ark shares one on-chain UTXO among many users through a tree of pre-signed transactions. [Bitcoin Optech's topic page](https://bitcoinops.org/en/topics/ark/) describes rounds co-ordinated by an Ark operator, virtual UTXOs (VTXOs) held off-chain, and a unilateral exit: the user broadcasts their branch and leaf and ends on an output they alone control. VTXOs expire on a timelock. Until a received VTXO is rolled into a new round, a sender can collude with the operator to double-spend it, because each payment is co-signed by the user and the operator. Optech also says Ark runs on Bitcoin today, and that covenants would let one tree cover more users. No user count or byte size is given there.

[Ark Protocol](https://ark-protocol.org/) describes the same client-server shape: users keep control of their bitcoin, and the server co-ordinates. Two implementations are listed, Second and Arkade. [Second's introduction](https://second.tech/docs/learn/intro) says Second's server runs a round every hour. That is one operator's setting, not a protocol constant. [Arkade's docs](https://docs.arkadeos.com/learn) say an application can issue Bitcoin-native assets and control their supply, that the operator co-signs virtual-mempool transactions, that one on-chain transaction "settles funds for thousands of users," and that users can claim funds on-chain if the operator is unavailable. "Thousands" is Arkade's claim about settlement, not a vbyte measurement, and "control their supply" is not the same thing as freezing one holder's coins.

A chain observer sees the round transaction and, if someone unilaterally exits, that user's branch. The operator sees the payments they co-sign. Other users in the round do not get a public graph of everyone else's payments from the single on-chain output, but the operator is not "other users."

### Comparison

| | RGB | Taproot Assets | Ark / Arkade |
| --- | --- | --- | --- |
| What moves | Client-validated contract state, sealed to Bitcoin | Assets committed in Taproot outputs, proofs stored off-chain, transferable on Lightning | Bitcoin VTXOs in a pre-signed tree. Arkade also documents issuing assets |
| Chain observer | Tapret: no payload in the transaction. OP_RETURN seal: a 32-byte commitment | A Taproot transaction. The asset graph is in the proofs | The shared round transaction. An exit reveals that user's branch |
| Operator of the layer | Not a party to a direct transfer | A universe operator sees proofs that are uploaded. A pocket-universe federation holds the on-chain key | Co-signs every payment in the rounds they run, and can collude with a sender until the next round |
| Unilateral exit back to bitcoin | The seal is a Bitcoin outpoint the holder can spend. That spend does not, by itself, release an Omni reserve | The holder can spend the Bitcoin outpoint that commits to the asset, subject to the asset script | Documented: broadcast the pre-signed branch. Arkade: claim on-chain if the operator is down |
| Issuer freeze and view keys in the docs we read | Not described. zk-STARK history compression is a stated direction of v0.12 | Scripts are programmable. Confidential transfers are listed as future work. No freeze or view key | Arkade: issuer can control supply. Operator visibility conflicts with private-by-default |
| Consensus change on Bitcoin or Omni | None for the protocol as documented | None | None. Covenants would make the trees cheaper, and are not required |

## Recommendation

Use **RGB** as the first target for the layer.

The privacy goal is a transfer the chain cannot read and an operator does not have to co-sign. Tapret, as the RGB v0.12 note describes it, is that shape. Ark's operator co-signs, so the operator sees the payment, and Optech's collusion case is the operator plus a sender. Taproot Assets can keep metadata off-chain, and its own overview still lists confidential transactions as future work, while a universe is a place proofs go when someone wants discovery. RGB is also the protocol Tether has named, twice, as the Bitcoin path for USD₮ after it stopped minting on Omni. A bridge aimed at regulated stablecoins should meet that path. Those announcements are not a freeze feature and not a view key.

Taproot Assets is the fallback if a prototype cannot get wallets to store and validate RGB consignments, or cannot express freeze in an RGB contract. Its Lightning tooling and asset scripts are further along in public docs. The cost of the fallback is a weaker default: universe operators and, for a pocket universe, the federation that holds the on-chain key.

Ark is the reference for the later exit work and for packing many people into one on-chain transaction. It is the wrong ledger for the private token. The operator sees and co-signs. Arkade's asset issuance is worth a second look only if the team decides operator visibility is acceptable. This recommendation says it is not, given the goal that the sender and the receiver are the ones who see a layer transfer.

Freeze and a view key are requirements on the contract we would write on top of RGB. They are not reasons to pretend RGB already has them. If a testnet contract cannot freeze a holding without the issuer signing every transfer, and cannot open the history to an auditor alone, the recommendation gets revisited before any mainnet property is bridged. That checkpoint is in the roadmap.

## Possible roles for OMNI

These are proposals for discussion. This draft does not set a fee, a bond size, or a price.

**A voluntary operator payment, in OMNI, with no consensus change.** A user pays a bridge operator with an ordinary Omni send of OMNI. The bridge can refuse service without it. That is a commercial term, not a protocol rule.

**A public bond, with no automatic slash.** Operators send OMNI to a published address and leave it there so users can see the balance. If the operators take the reserve, the bond still sits there unless someone with the keys moves it. Slashing it inside consensus would be a consensus change. This design does not include that change. A bond that signers can withdraw themselves is a signal, not a cryptographic guarantee.

**A protocol-mandatory fee, or a reward paid to watchers from issuance or a new fee type.** Either of those is a consensus change. They are listed so the idea is not confused with the two items above. They are not part of the bridge this document specifies.

**OMNI as a trading pair on the built-in exchange.** OMNI is already a native property. No new role is proposed here.

## Roadmap

**Phase 0, separate from this layer.** Clear the 999,999 gates on `develop`, including send-to-many and witness inputs, and ship a release the bridge can run. Mastercoin does not depend on that to start on testnet with P2PKH and P2SH. It does depend on it for the cheaper pegs in [FEES.md](FEES.md).

**Phase 1.** Agree this spec: RGB as the target, a federated pooled bridge, freeze and a view key as in-scope, Ark-style pre-signed refunds as later work. No code in the consensus path.

**Phase 2, testnet.** An external bridge program. One managed test property. A 2-of-3 bridge address. An RGB contract that either implements freeze and a view key or produces a written finding that the schema cannot, in which case Phase 1's checkpoint fires. No mainnet tokens.

**Phase 3.** Measure real anchor sizes, consignment sizes, and backup failure on that testnet. Replace the estimates in [FEES.md](FEES.md) with those measurements before anyone talks about a mainnet property.

**Phase 4.** Prototype the per-deposit pre-signed Omni refund. Decide whether Ark-style rounds should batch the Bitcoin anchors under the RGB seals. Add auditor tooling that uses the view key and does not publish the graph.

## Open questions

1. Can an RGB contract freeze one holding, and open history to an auditor, without the issuer or the bridge co-signing every transfer and without writing the transfer to Bitcoin? The sources read for this draft do not show that feature. The recommendation depends on the answer.
2. Does the first bridge stay a pooled M-of-N, with no unilateral Omni exit, or is the per-deposit pre-signed refund required before any value that matters is bridged?
3. How does an Omni address freeze map onto layer holdings that are not Omni addresses, and how does the bridge refuse a peg-out of a frozen claim without freezing the bridge address itself?
4. Is a given bridge operator a crypto-asset service provider for Article 79? Self-hosted wallets whose provider has no control are carved out in the recital Norton Rose cites. A lawyer has to draw that line for a real operator. This draft does not.
5. What confirmation depth does the bridge wait, who pays the anchor fee, and how many transfers actually share one anchor? The fee table uses 10, 100, and 1,000 as assumptions so the split is visible. They are not measured round sizes. Arkade's "thousands of users" is their description of settlement, not a byte count.
6. Which RGB consensus line is the contract written against? Tether's August 2025 note names mainnet 0.11.1. The May 2025 v0.12 release candidate says earlier contracts are incompatible.
7. If RGB history or backup fails the Phase 2 prototype, does the team switch to Taproot Assets, accepting universe operators as observers, or stop?
8. Can any OMNI bond be more than a published balance without a consensus change? This design's answer is no.

## Sources

Omni code on this branch, unless noted:

- Class C sender is the first input: `src/omnicore/omnicore.cpp`
- Freeze and unfreeze: `src/omnicore/tx.cpp`, `omni_createpayload_freeze` in `src/omnicore/rpcpayload.cpp`
- Null-data relay limit 83 bytes: `MAX_OP_RETURN_RELAY` in `src/script/standard.h`, checked in `src/policy/policy.cpp`
- Dust: `OmniGetDustThreshold` in `src/omnicore/script.cpp` multiplies `GetDustThreshold` by 3. `DEFAULT_MIN_RELAY_TX_FEE` is 1000 in `src/validation.h`. `DUST_RELAY_TX_FEE` is 3000 in `src/policy/policy.h`
- P2SH activation height: `SCRIPTHASH_BLOCK` in `src/omnicore/rules.cpp`
- Witness and send-to-many gates at 999,999: `develop` commit `9352212e8`, `src/omnicore/rules.cpp`. Send-to-many payload: `CreatePayload_SendToMany` in `src/omnicore/createpayload.cpp` on that commit

External:

- GENIUS Act, Public Law 119-27 (approved 18 July 2025): <https://www.congress.gov/119/plaws/publ27/PLAW-119publ27.pdf>
- White House fact sheet, 18 July 2025: <https://www.whitehouse.gov/fact-sheets/2025/07/fact-sheet-president-donald-j-trump-signs-genius-act-into-law/>
- Regulation (EU) 2024/1624, Article 79, as compiled by Transparency International EU (June 2026): <https://transparency.eu/wp-content/uploads/2026/06/1.1-European-Unions-legislative-framework-on-virtual-assets-crypto-.pdf>
- Norton Rose Fulbright, 9 July 2024, on the AML Regulation's application date and Article 79: <https://www.nortonrosefulbright.com/en/knowledge/publications/644c5392/the-new-eu-amlcft-regime-has-arrived-are-you-ready>
- Bitcoin Core 30.0 release notes, `-datacarriersize` default 100,000: <https://bitcoincore.org/en/releases/30.0/>
- RGB v0.12 RC1, 20 May 2025: <https://rgb.tech/blog/release-v0-12-rc-1/>
- RGB contract operations, client-side verification: <https://docs.rgb.info/rgb-state-and-operations/components-of-a-contract-operation>
- Tether, 17 August 2023, stop minting USD₮-Omni and the RGB note: <https://tether.io/news/tether-makes-strategic-transition-to-meet-community-demands-and-foster-innovation/>
- Tether, 28 August 2025, USD₮ on RGB: <https://tether.io/news/tether-to-launch-usdt-on-rgb-expanding-native-bitcoin-stablecoin-support/>
- Taproot Assets overview and FAQ: <https://docs.lightning.engineering/the-lightning-network/taproot-assets> and <https://docs.lightning.engineering/the-lightning-network/taproot-assets/faq>
- Ark, Bitcoin Optech: <https://bitcoinops.org/en/topics/ark/>
- Ark Protocol: <https://ark-protocol.org/>
- Second, Ark introduction: <https://second.tech/docs/learn/intro>
- Arkade: <https://docs.arkadeos.com/learn>
