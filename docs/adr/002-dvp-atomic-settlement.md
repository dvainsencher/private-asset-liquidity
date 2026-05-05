# ADR-002: Atomic DVP as the Settlement Primitive

## The Question That Prompted This Decision

The permissioned DLT decision (ADR-001) established the shared ledger layer. But a
shared ledger alone does not solve settlement. It solves the record-keeping problem —
who owns what, verified by all parties. Settlement is a different problem: how do two
parties exchange an asset for payment in a way that neither can be left exposed if the
other defaults mid-transaction?

The traditional answer to that question is T+2 settlement: trade today, exchange asset
and payment two business days later, with a central counterparty (CCP) or custodian
absorbing the counterparty risk in between. T+2 exists not because two days is the
natural time required to move an asset and a payment — it exists because verifying,
reconciling, and guaranteeing the two legs of a transaction across institutions that
do not share systems takes time and requires an intermediary to absorb the risk.

The question this decision addresses: if we have a shared permissioned ledger, can we
do better than T+2? And what does "better" actually mean — faster, cheaper, safer, or
all three?

---

## What Is DVP and Why the "Atomic" Part Matters

DVP — Delivery versus Payment — is the principle that the asset transfer and the
payment transfer happen as a linked pair: you get the asset if and only if I get the
payment. This principle already exists in traditional settlement; it is what CCPs
enforce. The problem is how it is enforced: through a multi-step process involving
matching, confirmation, netting, and settlement across multiple systems, with a time
window during which one leg has happened and the other has not.

That window is where counterparty risk lives. If a broker delivers the asset but the
buyer's payment fails after the fact, the broker is exposed. The T+2 window exists
partly to allow time for that risk to be managed — checks run, netting calculated,
guarantees posted. The intermediary that stands between the two parties earns its
margin by absorbing that risk.

"Atomic" DVP means the two legs of the transaction — asset delivery and payment —
execute in a single indivisible operation. Either both complete or neither does. There
is no state in which the asset has transferred but the payment has not, or vice versa.
The counterparty risk window collapses to zero because the window does not exist.

This is not a marginal improvement on T+2. It is a structural elimination of the
problem T+2 was designed to manage.

---

## Why Traditional Settlement Infrastructure Cannot Do This

The reason T+2 exists is not that atomic settlement is technically impossible — it is
that atomic settlement requires both legs of a transaction to be controlled by the
same system at the same moment. In traditional market infrastructure, asset records
live in one custodian's system, payment records live in another institution's system,
and those systems do not share a single transactional boundary. You cannot atomically
commit two operations across two independent systems without distributed transaction
coordination — which, at the scale and trust level of capital markets, is equivalent
to the settlement infrastructure that T+2 already provides, just slower.

A shared permissioned ledger changes this. When both the asset token and the payment
token exist on the same ledger, they can be transferred in a single transaction that
either commits both or rolls back both. The shared ledger provides the transactional
boundary that traditional multi-system infrastructure lacks.

This is the architectural reason DVP on DLT is qualitatively different from DVP in
traditional settlement — not a faster version of the same process, but a different
process that eliminates the intermediate states where risk accumulates.

---

## How Atomic DVP Works in a Permissioned DLT

At the protocol level, atomic DVP on a shared ledger can be implemented in a few ways.
Understanding the options clarifies the trade-offs.

**Escrow-based approach.** A smart contract acts as a neutral escrow. The seller locks
the asset token into the contract; the buyer locks the payment token into the contract.
The contract then releases both simultaneously — asset to buyer, payment to seller —
upon validating that both legs are present and conditions are met (counterparty identity
verified, suitability checked, transfer restrictions satisfied).

The failure modes are structurally clean. If the buyer fails to lock payment before the
timeout window expires, the seller recovers the asset — no transfer has occurred. If
the buyer locks but the compliance check fails at release time, both parties receive
refunds. Neither party can unilaterally retrieve funds from escrow outside the timeout
path. Critically, the compliance checks execute inside the `settle()` function as a
precondition of the state change — not as an application-layer call that a developer
remembers to make. Compliance cannot be bypassed at the settlement primitive.

This requires both legs on the same ledger. It is the correct model for same-ledger
settlement.

**Hash Time Locked Contracts (HTLCs).** A cryptographic approach designed for
cross-network scenarios. The seller generates a random secret and shares only its hash
with the buyer. Two independent contracts are created — an asset contract on the
permissioned ledger, a payment contract on the payment network (e.g., Drex) — both
locked against the same hash. The seller reveals the secret to claim payment; that
secret is then publicly readable on-chain and the buyer uses it to claim the asset.
The two contracts are linked cryptographically, not transactionally.

The timeout ordering is load-bearing: the payment contract expires before the asset
contract, ensuring the seller must claim payment first. Once the seller reveals the
secret to claim payment, it is permanently on-chain — a network outage between the two
legs does not break the buyer's ability to claim the asset; it only delays it. If the
seller never reveals the secret, both contracts time out and both parties are refunded.

HTLCs are the mechanism that preserves atomic guarantees across a network boundary.
For Drex integration — where the asset is on the permissioned ledger and payment is
on the BCB's network — HTLC is the correct model.

**Transaction finality.** The atomic guarantee is only credible if finality is
deterministic. In Proof of Work chains, finality is probabilistic: a block can be
orphaned if a longer competing chain emerges, making "probably settled" the best
achievable state. For DVP settlement, this is structurally incompatible — you cannot
build a no-chargeback guarantee on a foundation where chargebacks are probabilistically
possible.

BFT consensus achieves deterministic finality through a three-phase commit protocol.
When a transaction is proposed, nodes exchange prepare messages; a node advances to
commit only after receiving `2f + 1` matching responses (where `f` is the maximum
number of faulty nodes and `N ≥ 3f + 1` total nodes). The mathematical guarantee: any
two groups of `2f + 1` nodes overlap by at least `f + 1` honest nodes. An honest node
that committed a transaction will not commit a conflicting one — so two conflicting
commits cannot both reach quorum. Once committed, the transaction is final; the
protocol provides no reversal path.

Network partition behavior is worth understanding explicitly. BFT prioritizes
consistency over availability. A minority partition cannot reach `2f + 1` quorum — it
halts rather than committing in an inconsistent state. When the partition heals, the
minority syncs to the majority's committed history. A partition causes a settlement
outage, not a settlement inconsistency. Outage is recoverable; inconsistency in a
financial ledger is not. This is the correct trade-off.

The "no chargebacks" property follows mechanically from the protocol, not from policy.
There is no reversal mechanism. A mistaken transaction requires a new correcting
transaction — a forward correction, not a rollback. Operational processes and user
interfaces must be designed around this.

---

## The Payment Leg Problem

Atomic DVP on a shared ledger solves the asset leg cleanly — the asset token transfers
on the same ledger. The payment leg is harder.

If payment is fiat currency transferred outside the ledger (a bank wire, a PIX
transfer), atomicity is broken: the asset can be locked in escrow while the external
payment is in flight, reintroducing the exposure that atomic DVP was designed to
eliminate. True atomicity requires both legs on the same transactional boundary.

Three approaches to the payment leg, in order of increasing atomicity:

**Off-ledger payment with confirmation.** Payment happens outside the DLT (PIX, TED,
bank transfer), and the custodian or an authorized party confirms receipt on-chain,
triggering asset release from escrow. Faster than T+2 but not truly atomic — there is
still a window between payment initiation and on-chain confirmation. Suitable as an
interim solution.

**Tokenized cash on the same ledger.** A tokenized representation of BRL held on the
permissioned network, controlled by regulated participants (banks, payment institutions).
Both legs are on the same ledger, atomicity is real. Requires issuing or integrating
a tokenized cash instrument, which has its own regulatory and operational surface.

**Drex integration.** When Drex matures as a wholesale CBDC, it provides exactly this:
a tokenized BRL on a permissioned network operated by the BCB, designed for atomic DVP
settlement in capital markets. The settlement interface should be designed as pluggable
(see ADR-001) so that Drex can be adopted as the payment leg when it is available,
without redesigning the asset leg architecture. The transition from off-ledger payment
confirmation to Drex is then an infrastructure upgrade, not an architectural change.

This is the concrete form of the Drex integration strategy: it is not about competing
with Drex, it is about designing the payment leg interface so that Drex slots in as
the natural solution when the regulatory and technical conditions allow.

---

## What This Decision Constrains

**Network participation for settlement.** For DVP to be atomic, both counterparties
must either be on the same permissioned network or have a trusted bridge between their
respective ledgers. A buyer who is not a network participant cannot settle atomically —
they require an intermediary (a member custodian) to act on their behalf. This shapes
the onboarding model: direct participants versus client participants operating through
a custodian.

**Finality and operational design.** Deterministic finality means no reversals. Every
user-facing flow that touches settlement — confirmation screens, error states, support
processes — must be designed around this. The "undo" model of most software does not
apply at the settlement layer.

**Compliance at the settlement primitive.** Because the settlement transaction is the
moment of legal transfer of ownership, it is the correct place to enforce compliance
checks: suitability, KYC status, transfer restrictions, reporting triggers. Enforcing
these in the smart contract that executes settlement ensures they cannot be bypassed
at the application layer. This depends on compliance rules being encodable — which
loops back to the regulatory surface stability question raised in ADR-001.

**The interim payment model is temporary by design.** Starting with off-ledger payment
confirmation is pragmatic — it allows the platform to operate before Drex is available.
But it reintroduces a settlement window and should be treated as a transitional state,
not a permanent architecture. The design must not accumulate dependencies on the
interim model that would make the Drex migration expensive.

---

## Conclusion

The decision is: atomic DVP as the settlement primitive, implemented via smart contract
escrow on the permissioned ledger for same-network settlement, with HTLC as the
cross-network mechanism for Drex integration, and the payment leg designed as a
pluggable interface to support both a transitional off-ledger confirmation model and
the Drex path.

The reasoning follows from what T+2 actually is: not a technical requirement but a
consequence of multi-system, multi-party trust infrastructure that cannot share a
transactional boundary. A shared permissioned ledger provides that boundary. Atomic
DVP is what becomes possible when the boundary exists — and it eliminates the
counterparty risk window structurally rather than managing it through intermediaries.

The finality guarantee sharpens this further. The moment BFT consensus commits the
`settle()` transaction, both the asset transfer and the payment transfer are
simultaneously and irrevocably done — not "probably done" but definitively so. The
counterparty risk window does not shrink; it does not exist as a state. This changes
the operational model in a non-trivial way: every user-facing flow that touches
settlement must be designed around forward correction, not reversal. The "undo" model
of most software does not apply at the settlement layer.

The uncertainty in this decision is concentrated in the payment leg. The asset leg is
architecturally clean; the finality protocol is well-understood. The payment leg
requires either an interim operational workaround or a dependency on Drex's timeline.
Both are manageable, but the design must be explicit about which state it is in and
what the migration path looks like. The HTLC model for Drex integration preserves
atomic guarantees across the network boundary — but it introduces timeout management
and cross-network monitoring as operational responsibilities that do not exist in the
same-ledger escrow model.
