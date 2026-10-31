# Fees

Miner fees below come from `contrib/mastercoin/size.py`. Run it again with:

```
python3 contrib/mastercoin/size.py
```

The rest of this page is that command's output. Parenthesized numbers are an even split of one transaction fee. They are not a second fee paid to miners. Rows marked ESTIMATE depend on how many transfers share an anchor. The script's checks fix the simple-send OP_RETURN at 31 bytes and the 72-byte signature assumption.

The model was checked, in the notes that supplied it, against two mainnet transactions: 320 vB modeled, 319 vB observed. A 71-byte DER signature instead of 72 makes a non-witness input 1 vB smaller. That is the same gap. Those two transactions are not identified here, and the table does not "correct" for them.

Send-to-many of 7 receivers on a P2SH-P2WPKH input is 446 vB in this script. Seven separate simple sends of that input are 1,379 vB. An earlier one-liner of the same model printed about 445 vB for the batch, because it dropped one byte of the `OP_PUSHDATA1` header once the payload passed 75 bytes. The serialized output is 88 bytes, not 87. N=10 and N=50 do not fit this repository's 83-byte null-data script limit (`MAX_OP_RETURN_RELAY` in `src/script/standard.h`). Their rows are sizes only. Bitcoin Core 30.0 raised the default `-datacarriersize` to 100,000 ([release notes](https://bitcoincore.org/en/releases/30.0/)), which is above those scripts. Omni still has to activate send-to-many: on `develop` commit `9352212e8`, mainnet `MSC_SEND_TO_MANY_BLOCK` is 999,999.

The two Mastercoin anchors are both 154 vB. A 32-byte OP_RETURN output serializes to 43 bytes, and a P2TR output is also 43 bytes, so a P2TR input plus that OP_RETURN plus a P2TR change weighs the same as a P2TR input and two P2TR outputs. The fees match. The privacy does not: the OP_RETURN commitment is visible, and the tapret commitment, as the RGB v0.12 note describes it, is not. Neither anchor is a measured RGB, Taproot Assets, or Ark transaction. Real witnesses can be larger, which would raise the estimate.

Dust in the output is bitcoin that must be placed in a spendable output. It is not the miner fee. No euro figure is computed. A euro amount needs a BTC price, and this page does not pick one.

## Script output

contrib/mastercoin/size.py
Assumptions: 1 input, SIG=72 bytes, recipient output plus change,
Class C simple send data = 20 bytes, OP_RETURN output = 31 bytes.
Fees are vsize * sat/vB, in satoshis. A parenthesized number is the
even split of that transaction fee across the transfers in the row.
Splits are accounting, not a second miner fee. Estimates are marked.

Today: Omni Class C simple send (one recipient)

| Case | Tx vB | Per transfer vB | 2 sat/vB tx (split) | 10 sat/vB tx (split) | 50 sat/vB tx (split) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Simple send P2PKH | 257 | 257 | 514 | 2570 | 12850 |
| Simple send P2SH-P2PKH | 279 | 279 | 558 | 2790 | 13950 |
| Simple send P2SH-P2WPKH | 197 | 197 | 394 | 1970 | 9850 |

- Simple send P2PKH: Legacy 1… input. Allowed on mainnet today.
- Simple send P2SH-P2PKH: P2SH wrapping a P2PKH redeem script (not wrapped SegWit). Output is a 3… script.
- Simple send P2SH-P2WPKH: Wrapped SegWit, the usual 3… spend. Allowed on mainnet today as a P2SH input.

With SegWit and Taproot: same simple send, one input

| Case | Tx vB | Per transfer vB | 2 sat/vB tx (split) | 10 sat/vB tx (split) | 50 sat/vB tx (split) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Simple send P2WPKH | 172 | 172 | 344 | 1720 | 8600 |
| Simple send P2TR | 185 | 185 | 370 | 1850 | 9250 |

- Simple send P2WPKH: Native SegWit. develop mainnet WITNESS_V0_BLOCK = 999999, so this input is not accepted on mainnet yet.
- Simple send P2TR: Taproot key-path spend. develop mainnet WITNESS_V1_BLOCK = 999999, so this input is not accepted on mainnet yet.

Send-to-many (type 7): one Class C transaction, N recipient outputs + change

| Case | Tx vB | Per transfer vB | 2 sat/vB tx (split) | 10 sat/vB tx (split) | 50 sat/vB tx (split) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Send-to-many P2PKH N=7 | 518 | 74 | 1036 (148) | 5180 (740) | 25900 (3700) |
| Send-to-many P2PKH N=10 | 647 | 64.7 | 1294 (129.4) | 6470 (647) | 32350 (3235) |
| Send-to-many P2PKH N=50 | 2370 | 47.4 | 4740 (94.8) | 23700 (474) | 118500 (2370) |
| Send-to-many P2SH-P2WPKH N=7 | 446 | 63.7143 | 892 (127.4286) | 4460 (637.1429) | 22300 (3185.7143) |
| Send-to-many P2SH-P2WPKH N=10 | 569 | 56.9 | 1138 (113.8) | 5690 (569) | 28450 (2845) |
| Send-to-many P2SH-P2WPKH N=50 | 2212 | 44.24 | 4424 (88.48) | 22120 (442.4) | 110600 (2212) |
| Send-to-many P2WPKH N=7 | 415 | 59.2857 | 830 (118.5714) | 4150 (592.8571) | 20750 (2964.2857) |
| Send-to-many P2WPKH N=10 | 535 | 53.5 | 1070 (107) | 5350 (535) | 26750 (2675) |
| Send-to-many P2WPKH N=50 | 2138 | 42.76 | 4276 (85.52) | 21380 (427.6) | 106900 (2138) |

- Send-to-many P2PKH N=7: Class C script is 79 bytes (data 76), within this repo's MAX_OP_RETURN_RELAY of 83. Send-to-many itself is not active on mainnet (develop MSC_SEND_TO_MANY_BLOCK = 999999). 7 separate simple sends of this input type are 1799 vB.
- Send-to-many P2PKH N=10: DOES NOT FIT this repo's 83-byte null-data limit (script 106 bytes, data 103). Size only. Bitcoin Core 30's default -datacarriersize is 100,000, which is above this script; Omni still has to activate send-to-many. 10 separate simple sends of this input type are 2570 vB.
- Send-to-many P2PKH N=50: DOES NOT FIT this repo's 83-byte null-data limit (script 467 bytes, data 463). Size only. Bitcoin Core 30's default -datacarriersize is 100,000, which is above this script; Omni still has to activate send-to-many. 50 separate simple sends of this input type are 12850 vB.
- Send-to-many P2SH-P2WPKH N=7: Class C script is 79 bytes (data 76), within this repo's MAX_OP_RETURN_RELAY of 83. Send-to-many itself is not active on mainnet (develop MSC_SEND_TO_MANY_BLOCK = 999999). 7 separate simple sends of this input type are 1379 vB.
- Send-to-many P2SH-P2WPKH N=10: DOES NOT FIT this repo's 83-byte null-data limit (script 106 bytes, data 103). Size only. Bitcoin Core 30's default -datacarriersize is 100,000, which is above this script; Omni still has to activate send-to-many. 10 separate simple sends of this input type are 1970 vB.
- Send-to-many P2SH-P2WPKH N=50: DOES NOT FIT this repo's 83-byte null-data limit (script 467 bytes, data 463). Size only. Bitcoin Core 30's default -datacarriersize is 100,000, which is above this script; Omni still has to activate send-to-many. 50 separate simple sends of this input type are 9850 vB.
- Send-to-many P2WPKH N=7: Class C script is 79 bytes (data 76), within this repo's MAX_OP_RETURN_RELAY of 83. Send-to-many itself is not active on mainnet (develop MSC_SEND_TO_MANY_BLOCK = 999999). 7 separate simple sends of this input type are 1204 vB.
- Send-to-many P2WPKH N=10: DOES NOT FIT this repo's 83-byte null-data limit (script 106 bytes, data 103). Size only. Bitcoin Core 30's default -datacarriersize is 100,000, which is above this script; Omni still has to activate send-to-many. 10 separate simple sends of this input type are 1720 vB.
- Send-to-many P2WPKH N=50: DOES NOT FIT this repo's 83-byte null-data limit (script 467 bytes, data 463). Size only. Bitcoin Core 30's default -datacarriersize is 100,000, which is above this script; Omni still has to activate send-to-many. 50 separate simple sends of this input type are 8600 vB.

Mastercoin layer: amortised anchor (estimates; the layer does not exist)

| Case | Tx vB | Per transfer vB | 2 sat/vB tx (split) | 10 sat/vB tx (split) | 50 sat/vB tx (split) |
| --- | ---: | ---: | ---: | ---: | ---: |
| ESTIMATE tapret anchor / 10 | 154 | 15.4 | 308 (30.8) | 1540 (154) | 7700 (770) |
| ESTIMATE 32-byte OP_RETURN anchor / 10 | 154 | 15.4 | 308 (30.8) | 1540 (154) | 7700 (770) |
| ESTIMATE tapret anchor / 100 | 154 | 1.54 | 308 (3.08) | 1540 (15.4) | 7700 (77) |
| ESTIMATE 32-byte OP_RETURN anchor / 100 | 154 | 1.54 | 308 (3.08) | 1540 (15.4) | 7700 (77) |
| ESTIMATE tapret anchor / 1000 | 154 | 0.154 | 308 (0.308) | 1540 (1.54) | 7700 (7.7) |
| ESTIMATE 32-byte OP_RETURN anchor / 1000 | 154 | 0.154 | 308 (0.308) | 1540 (1.54) | 7700 (7.7) |

- ESTIMATE tapret anchor / 10: Lower bound, not a measured RGB transaction. One ordinary P2TR 1-in-2-out (154 vB) is assumed to anchor 10 transfers because a tapret commitment adds no extra output. Real witnesses can be larger. Even split of 154 vB.
- ESTIMATE 32-byte OP_RETURN anchor / 10: Estimate of the visible-commitment alternative: P2TR input, 32-byte OP_RETURN, P2TR change (154 vB), split across 10 transfers. Not a measured transaction.
- ESTIMATE tapret anchor / 100: Lower bound, not a measured RGB transaction. One ordinary P2TR 1-in-2-out (154 vB) is assumed to anchor 100 transfers because a tapret commitment adds no extra output. Real witnesses can be larger. Even split of 154 vB.
- ESTIMATE 32-byte OP_RETURN anchor / 100: Estimate of the visible-commitment alternative: P2TR input, 32-byte OP_RETURN, P2TR change (154 vB), split across 100 transfers. Not a measured transaction.
- ESTIMATE tapret anchor / 1000: Lower bound, not a measured RGB transaction. One ordinary P2TR 1-in-2-out (154 vB) is assumed to anchor 1000 transfers because a tapret commitment adds no extra output. Real witnesses can be larger. Even split of 154 vB.
- ESTIMATE 32-byte OP_RETURN anchor / 1000: Estimate of the visible-commitment alternative: P2TR input, 32-byte OP_RETURN, P2TR change (154 vB), split across 1000 transfers. Not a measured transaction.

The tapret anchor and the 32-byte OP_RETURN anchor are both 154 vB.
A 32-byte OP_RETURN output is 43 bytes, the same serialized size as a
P2TR output (43 bytes), so the byte cost matches. The OP_RETURN
commitment is visible to a chain observer. The tapret commitment is not.

Session estimate (not a measurement)

Assumption: one P2WPKH peg-in, one P2WPKH peg-out, and 20 in-layer
transfers. Each in-layer transfer is an even 1/100 share of one 154 vB
tapret anchor. Peg transactions are not shared. In-layer operator
premiums are not included, because none are specified.

| sat/vB | Peg-in | Peg-out | 20 x 1/100 anchor | Session total | Per transfer in the session |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 344 | 344 | 61.6 | 749.6 | 37.48 |
| 10 | 1720 | 1720 | 308 | 3748 | 187.4 |
| 50 | 8600 | 8600 | 1540 | 18740 | 937 |

Dust locked in one spendable output, in satoshis. Not a miner fee.
Omni multiplies Bitcoin Core's dust threshold by 3 (script.cpp).
Rate 1000 sat/kvB is DEFAULT_MIN_RELAY_TX_FEE on this branch (validation.h).
Rate 3000 sat/kvB is DUST_RELAY_TX_FEE. On develop, omnicore.cpp sets
minRelayTxFee to that 3000 sat/kvB value before the extra factor of 3.

| Output | Dust at 1000 sat/kvB, x3 | Dust at 3000 sat/kvB, x3 |
| --- | ---: | ---: |
| P2PKH | 546 | 1638 |
| P2SH-P2WPKH | 540 | 1620 |
| P2WPKH | 294 | 882 |
| P2TR | 330 | 990 |

Plain bitcoin 1-in-2-out vB, for scale: P2PKH 226, P2SH-P2WPKH 166, P2WPKH 141, P2TR 154
