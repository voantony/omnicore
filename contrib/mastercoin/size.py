#!/usr/bin/env python3
"""Virtual-size and fee model for Omni sends and a Mastercoin anchor.

Extends the vbyte model supplied with the October 2026 cost notes. A simple-send
OP_RETURN of 20 bytes is 31 bytes on the wire, matching that model:

    value (8) + compact size (1) + OP_RETURN (1) + push (1) + "omni" (4) + payload (16)

The notes record a check of this model against two mainnet transactions:
320 vB modeled, 319 vB observed. Signatures here are the 72-byte DER size
(typical range 71–72). A 71-byte signature makes a non-witness input 1 vB
smaller, which is the same 1 vB gap. This script does not identify those
transactions.

Send-to-many payload layout follows CreatePayload_SendToMany on develop
(commit 9352212e8): version uint16, type uint16, property uint32, count uint8,
then (vout uint8, amount uint64) per receiver. The Class C push is the 4-byte
"omni" marker plus that payload.

No figure in this file is a measured RGB, Taproot Assets, or Ark transaction.
Anchor rows are lower bounds under the assumptions printed with them.
"""

import math

SIG = 72  # ECDSA DER signature + sighash byte. Typical chain values are 71 or 72.
PUB = 33
P2PKH_REDEEM = 25  # OP_DUP OP_HASH160 <20> OP_EQUALVERIFY OP_CHECKSIG

# (non-witness bytes, witness bytes including the stack-item count)
IN = {
    "P2PKH": (32 + 4 + 1 + (1 + SIG + 1 + PUB) + 4, 0),
    "P2SH-P2PKH": (32 + 4 + 1 + ((1 + SIG) + (1 + PUB) + (1 + P2PKH_REDEEM)) + 4, 0),
    "P2SH-P2WPKH": (32 + 4 + 1 + 23 + 4, 1 + 1 + SIG + 1 + PUB),
    "P2WPKH": (32 + 4 + 1 + 0 + 4, 1 + 1 + SIG + 1 + PUB),
    "P2TR": (32 + 4 + 1 + 0 + 4, 1 + 1 + 64),
}
# Serialized CTxOut: 8 byte value + compact size + scriptPubKey.
OUT = {
    "P2PKH": 34,
    "P2SH-P2PKH": 32,
    "P2SH-P2WPKH": 32,
    "P2WPKH": 31,
    "P2TR": 43,
}

SIMPLE_SEND_DATA = 4 + 16  # "omni" + version/type/property/amount
MARKER = 4
# This repository: src/script/standard.h MAX_OP_RETURN_RELAY.
# IsStandard rejects a null-data script larger than this (policy.cpp).
MAX_OP_RETURN_RELAY = 83
RATES = (2, 10, 50)


def push_header_len(n):
    if n <= 75:
        return 1
    if n <= 255:
        return 2  # OP_PUSHDATA1 + length
    if n <= 65535:
        return 3  # OP_PUSHDATA2 + length
    raise ValueError("data length does not fit this model: %s" % n)


def compact_size_len(n):
    if n < 253:
        return 1
    if n <= 0xFFFF:
        return 3
    if n <= 0xFFFFFFFF:
        return 5
    return 9


def null_data_script_size(data_len):
    """scriptPubKey bytes for OP_RETURN <data_len bytes>."""
    return 1 + push_header_len(data_len) + data_len


def opreturn_out_size(data_len):
    script = null_data_script_size(data_len)
    return 8 + compact_size_len(script) + script


def vsize(ins, out_sizes):
    """BIP141 virtual size. Input and output counts must be below 253."""
    if len(ins) >= 253 or len(out_sizes) >= 253:
        raise ValueError("varint counts above 252 are not modeled")
    base = 4 + 4 + 1 + 1 + sum(IN[i][0] for i in ins) + sum(out_sizes)
    wit = sum(IN[i][1] for i in ins)
    weight = base * 4 + ((2 + wit) if wit else 0)
    return math.ceil(weight / 4)


def send_to_many_data_len(n):
    """Marker + payload. Payload is 9 + 9*n bytes; see module docstring."""
    if n < 1 or n > 255:
        raise ValueError(n)
    return MARKER + (2 + 2 + 4 + 1 + n * (1 + 8))


def dust_sats(address_type, sat_per_kvb):
    """OmniGetDustThreshold = 3 * GetDustThreshold(txout, minRelayTxFee).

    GetDustThreshold adds 148 bytes for a non-witness spend and 67 bytes for
    any witness program (policy.cpp: 107/4 + 41). GetFee truncates
    (feerate.cpp). This is bitcoin locked in outputs, not the miner fee.
    """
    out_size = OUT[address_type]
    spend = 67 if address_type in ("P2WPKH", "P2TR") else 148
    one = (out_size + spend) * sat_per_kvb // 1000
    return 3 * one


def fee_sats(vb, sat_per_vb):
    return vb * sat_per_vb


def fmt_sats(n):
    if isinstance(n, float):
        return "{:.4f}".format(n).rstrip("0").rstrip(".")
    return str(n)


def row(label, tx_vb, transfers, note):
    fees = [fee_sats(tx_vb, r) for r in RATES]
    per = [f / transfers for f in fees]
    return {
        "label": label,
        "tx_vb": tx_vb,
        "transfers": transfers,
        "per_vb": tx_vb / transfers,
        "fees": fees,
        "per_fees": per,
        "note": note,
    }


def simple_send(address_type):
    outs = [opreturn_out_size(SIMPLE_SEND_DATA), OUT[address_type], OUT[address_type]]
    return vsize([address_type], outs)


def send_to_many(address_type, n):
    data_len = send_to_many_data_len(n)
    outs = [opreturn_out_size(data_len)] + [OUT[address_type]] * n + [OUT[address_type]]
    return vsize([address_type], outs), data_len, null_data_script_size(data_len)


def tapret_anchor_vb():
    """Lower bound: one P2TR input, two P2TR outputs, no extra witness.

    RGB v0.12 RC1 describes a tapret commitment as not visible inside the
    bitcoin transaction. No extra bytes are added for a witness script,
    because this repository has no measured tapret witness.
    """
    return vsize(["P2TR"], [OUT["P2TR"], OUT["P2TR"]])


def opret_anchor_vb():
    """Anchor that carries a 32-byte OP_RETURN commitment and one P2TR change.

    The same RGB note describes this shape: a 32-byte OP_RETURN commitment,
    with a higher transaction price than tapret and visible to chain analysis.
    """
    return vsize(["P2TR"], [opreturn_out_size(32), OUT["P2TR"]])


def check():
    assert IN["P2PKH"][0] == 148
    assert IN["P2SH-P2PKH"][0] == 174
    assert IN["P2SH-P2WPKH"] == (64, 108)
    assert IN["P2WPKH"][0] == 41
    assert IN["P2TR"][1] == 66
    assert opreturn_out_size(SIMPLE_SEND_DATA) == 31
    assert simple_send("P2PKH") == 257
    # N=7 fits this repository's 83-byte null-data script limit. N=8 does not.
    _, data7, script7 = send_to_many("P2WPKH", 7)
    _, data8, script8 = send_to_many("P2WPKH", 8)
    assert data7 == 76 and script7 == 79 and script7 <= MAX_OP_RETURN_RELAY
    assert data8 == 85 and script8 == 88 and script8 > MAX_OP_RETURN_RELAY
    # Original one-liner undercounted the push byte once data exceeded 75.
    # 8+1+1+1+76 = 87; the serialized output is 88.
    assert opreturn_out_size(76) == 88
    assert tapret_anchor_vb() == vsize(["P2TR"], [43, 43])


def print_table(title, rows):
    print(title)
    print()
    hdr = "| Case | Tx vB | Per transfer vB | " + " | ".join(
        "%d sat/vB tx (split)" % r for r in RATES
    ) + " |"
    sep = "| --- | ---: | ---: | " + " | ".join("---:" for _ in RATES) + " |"
    print(hdr)
    print(sep)
    for r in rows:
        cells = []
        for fee, per in zip(r["fees"], r["per_fees"]):
            if r["transfers"] == 1:
                cells.append(fmt_sats(fee))
            else:
                cells.append("%s (%s)" % (fmt_sats(fee), fmt_sats(per)))
        per_vb = fmt_sats(r["per_vb"]) if r["transfers"] != 1 else fmt_sats(r["tx_vb"])
        print("| %s | %d | %s | %s |" % (r["label"], r["tx_vb"], per_vb, " | ".join(cells)))
    print()
    for r in rows:
        if r["note"]:
            print("- %s: %s" % (r["label"], r["note"]))
    print()


def main():
    check()
    print("contrib/mastercoin/size.py")
    print("Assumptions: 1 input, SIG=%d bytes, recipient output plus change," % SIG)
    print("Class C simple send data = %d bytes, OP_RETURN output = %d bytes." % (
        SIMPLE_SEND_DATA, opreturn_out_size(SIMPLE_SEND_DATA)))
    print("Fees are vsize * sat/vB, in satoshis. A parenthesized number is the")
    print("even split of that transaction fee across the transfers in the row.")
    print("Splits are accounting, not a second miner fee. Estimates are marked.")
    print()

    today = []
    for t, note in (
        ("P2PKH", "Legacy 1… input. Allowed on mainnet today."),
        ("P2SH-P2PKH", "P2SH wrapping a P2PKH redeem script (not wrapped SegWit). Output is a 3… script."),
        ("P2SH-P2WPKH", "Wrapped SegWit, the usual 3… spend. Allowed on mainnet today as a P2SH input."),
    ):
        vb = simple_send(t)
        today.append(row("Simple send %s" % t, vb, 1, note))
    print_table("Today: Omni Class C simple send (one recipient)", today)

    segwit = []
    for t, note in (
        ("P2WPKH", "Native SegWit. develop mainnet WITNESS_V0_BLOCK = 999999, so this input is not accepted on mainnet yet."),
        ("P2TR", "Taproot key-path spend. develop mainnet WITNESS_V1_BLOCK = 999999, so this input is not accepted on mainnet yet."),
    ):
        segwit.append(row("Simple send %s" % t, simple_send(t), 1, note))
    print_table("With SegWit and Taproot: same simple send, one input", segwit)

    batches = []
    for t in ("P2PKH", "P2SH-P2WPKH", "P2WPKH"):
        for n in (7, 10, 50):
            vb, data_len, script = send_to_many(t, n)
            singles = n * simple_send(t)
            if script <= MAX_OP_RETURN_RELAY:
                note = (
                    "Class C script is %d bytes (data %d), within this repo's "
                    "MAX_OP_RETURN_RELAY of %d. Send-to-many itself is not active "
                    "on mainnet (develop MSC_SEND_TO_MANY_BLOCK = 999999). "
                    "%d separate simple sends of this input type are %d vB."
                    % (script, data_len, MAX_OP_RETURN_RELAY, n, singles)
                )
            else:
                note = (
                    "DOES NOT FIT this repo's %d-byte null-data limit "
                    "(script %d bytes, data %d). Size only. Bitcoin Core 30's "
                    "default -datacarriersize is 100,000, which is above this script; "
                    "Omni still has to activate send-to-many. "
                    "%d separate simple sends of this input type are %d vB."
                    % (MAX_OP_RETURN_RELAY, script, data_len, n, singles)
                )
            batches.append(row("Send-to-many %s N=%d" % (t, n), vb, n, note))
    print_table(
        "Send-to-many (type 7): one Class C transaction, N recipient outputs + change",
        batches,
    )

    tapret = tapret_anchor_vb()
    opret = opret_anchor_vb()
    layer = []
    for n in (10, 100, 1000):
        layer.append(row(
            "ESTIMATE tapret anchor / %d" % n,
            tapret,
            n,
            "Lower bound, not a measured RGB transaction. One ordinary P2TR "
            "1-in-2-out (%d vB) is assumed to anchor %d transfers because a tapret "
            "commitment adds no extra output. Real witnesses can be larger. "
            "Even split of %d vB." % (tapret, n, tapret),
        ))
        layer.append(row(
            "ESTIMATE 32-byte OP_RETURN anchor / %d" % n,
            opret,
            n,
            "Estimate of the visible-commitment alternative: P2TR input, "
            "32-byte OP_RETURN, P2TR change (%d vB), split across %d transfers. "
            "Not a measured transaction." % (opret, n),
        ))
    print_table(
        "Mastercoin layer: amortised anchor (estimates; the layer does not exist)",
        layer,
    )
    print(
        "The tapret anchor and the 32-byte OP_RETURN anchor are both %d vB."
        % tapret
    )
    print(
        "A 32-byte OP_RETURN output is %d bytes, the same serialized size as a"
        % opreturn_out_size(32)
    )
    print(
        "P2TR output (%d bytes), so the byte cost matches. The OP_RETURN"
        % OUT["P2TR"]
    )
    print("commitment is visible to a chain observer. The tapret commitment is not.")
    print()

    # Session estimate. Peg uses native SegWit simple sends, the cheaper shape
    # once witness inputs are activated. Marginal transfer is 1/100 of a tapret anchor.
    peg = simple_send("P2WPKH")
    transfers = 20
    share_n = 100
    anchor_fee = [fee_sats(tapret, r) for r in RATES]
    peg_fee = [fee_sats(peg, r) for r in RATES]
    print("Session estimate (not a measurement)")
    print()
    print("Assumption: one P2WPKH peg-in, one P2WPKH peg-out, and %d in-layer" % transfers)
    print("transfers. Each in-layer transfer is an even 1/%d share of one %d vB" % (share_n, tapret))
    print("tapret anchor. Peg transactions are not shared. In-layer operator")
    print("premiums are not included, because none are specified.")
    print()
    print("| sat/vB | Peg-in | Peg-out | %d x 1/%d anchor | Session total | Per transfer in the session |" % (
        transfers, share_n))
    print("| ---: | ---: | ---: | ---: | ---: | ---: |")
    for rate, afee, pfee in zip(RATES, anchor_fee, peg_fee):
        marginal = transfers * (afee / share_n)
        total = pfee + pfee + marginal
        print("| %d | %d | %d | %s | %s | %s |" % (
            rate, pfee, pfee, fmt_sats(marginal), fmt_sats(total), fmt_sats(total / transfers)))
    print()
    print("Dust locked in one spendable output, in satoshis. Not a miner fee.")
    print("Omni multiplies Bitcoin Core's dust threshold by 3 (script.cpp).")
    print("Rate 1000 sat/kvB is DEFAULT_MIN_RELAY_TX_FEE on this branch (validation.h).")
    print("Rate 3000 sat/kvB is DUST_RELAY_TX_FEE. On develop, omnicore.cpp sets")
    print("minRelayTxFee to that 3000 sat/kvB value before the extra factor of 3.")
    print()
    print("| Output | Dust at 1000 sat/kvB, x3 | Dust at 3000 sat/kvB, x3 |")
    print("| --- | ---: | ---: |")
    for t in ("P2PKH", "P2SH-P2WPKH", "P2WPKH", "P2TR"):
        print("| %s | %d | %d |" % (t, dust_sats(t, 1000), dust_sats(t, 3000)))
    print()
    print("Plain bitcoin 1-in-2-out vB, for scale: " + ", ".join(
        "%s %d" % (t, vsize([t], [OUT[t], OUT[t]])) for t in
        ("P2PKH", "P2SH-P2WPKH", "P2WPKH", "P2TR")
    ))


if __name__ == "__main__":
    main()
