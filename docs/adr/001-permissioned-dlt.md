# ADR-001: Permissioned DLT as the Foundational Ledger Layer

## The Question That Made DLT Relevant

The starting point for this decision was not "should we use blockchain?" That framing
invites the wrong kind of reasoning — technology-first, looking for a problem to fit.
The right question was: what kind of record-keeping does this market actually require,
and what architecture satisfies it?

The private asset secondary market involves multiple parties — custodians, brokers,
issuers, investors, regulators — each maintaining their own records of the same
underlying positions. Settlement today means reconciling those records across parties
who do not trust each other's systems. That reconciliation is where T+2 settlement
windows live. It is where operational cost floors are set. It is where small-ticket
transactions become economically unviable, because the cost of verifying across
institutions scales with the number of parties, not with the transaction size.

The question, stated precisely: how do you create a shared, authoritative record of
asset ownership and transactions between parties who do not trust each other's internal
systems — and who cannot be asked to trust a single central operator?

That framing is what makes DLT relevant. It is also what constrains which kind of DLT
is appropriate.

---

## Why Not a Centralized Database?

A centralized database is the right architecture when a single institution manages
its own records. Within one custodian, one broker, one fund manager, it is faster,
cheaper, and simpler than any distributed alternative. If this were a single-operator
problem, the answer would be a well-engineered relational database, and there would
be no interesting architectural question.

The problem is the multi-party trust model. Each institution has its own system of
record. No single participant is in a position — commercially, legally, or
operationally — to be designated the authoritative source of truth for all others.
A custodian will not accept a broker's database as definitive. A fund manager will
not give an issuer's system authority over its own positions.

A central operator could, in principle, solve this: build a neutral clearinghouse
that all parties agree to trust. But this requires every participant to accept that
the operator's record supersedes their own, that the operator's infrastructure is
reliable enough to stake regulated obligations on, and that the operator will not act
adversarially with the data it accumulates about every participant's positions and
trading activity. In a competitive market with regulatory obligations around data,
those conditions do not hold reliably. The central database approach trades the
reconciliation problem for a trust problem — which is a different problem, not a
solved one.

DLT's structural advantage is that the ledger is not owned by any single party but
is verifiable by all. The reconciliation problem disappears not because one party
wins the authority contest, but because there is no authority contest.

---

## Why Not a Public Blockchain?

Public chains were the natural starting reference point — they are the most visible
instances of DLT, and the properties that make them interesting (immutability,
decentralization, programmability) are genuinely relevant to this use case. But two
properties make them unsuitable for regulated capital markets, and neither is about
throughput.

**Transaction visibility.** On a public blockchain, all transactions are visible to
all participants globally, permanently. A fund's trading activity, position changes,
counterparty relationships, and timing would be exposed to anyone who reads the chain.
This is not a marginal privacy concern — it is structurally incompatible with
competitive confidentiality and with regulatory requirements around market-sensitive
information. A fund manager cannot legally or commercially accept that their order
flow is public.

**Permissionless participation.** Public chains are designed for environments where
participants are anonymous and potentially adversarial. Anyone can join, transact,
and hold assets pseudonymously. The regulatory frameworks governing capital markets
in Brazil — CVM, BCB, ANBIMA — require KYC'd, identifiable participants at every
point in the transaction chain. There is no way to enforce this on a public chain
without adding an identity and permissioning layer that effectively recreates a
permissioned system on top of the public one. At that point, the public chain is
providing the security model of an adversarial environment (computationally expensive
consensus, global replication) for a use case that does not have adversarial
participants — an expensive solution to a problem you have not reduced.

It is worth being explicit about what did *not* disqualify public chains: throughput.
The throughput gap between public blockchains and centralized databases is real, but
framing the choice as "DLT is slower but more trustworthy" is a category error. The
right comparison is between a shared permissioned ledger and the current bilateral
reconciliation process, where the bottleneck is not compute — it is the trust and
verification overhead between institutions. A shared ledger removes that overhead
structurally; the transactions-per-second comparison is beside the point.

---

## Why Permissioned DLT — and What That Means Architecturally

Permissioned DLT restricts network participation to vetted entities. This is not a
compromise between "real" decentralization and centralized control — it is the correct
architecture for an environment where participants must be identifiable but no single
participant can be trusted as the sole authority.

Understanding what this decision actually commits to requires going one level deeper
into how permissioned networks work.

**Consensus mechanism.** Public chains use Proof of Work or Proof of Stake — consensus
mechanisms designed for environments with anonymous, potentially adversarial
participants where you cannot enumerate or exclude bad actors. The consensus cost
(energy, latency) is the price of that adversarial tolerance. Permissioned chains
typically use Byzantine Fault Tolerant (BFT) consensus instead. BFT assumes a known,
bounded set of participants and has a formal mathematical property: it can reach
correct consensus as long as at most ⌊(N−1)/3⌋ nodes are behaving incorrectly —
whether by crashing, sending wrong data, or acting maliciously. With 10 nodes, 3 can
be faulty; beyond that threshold, correctness cannot be guaranteed. This bound is a
realistic assumption in a vetted network of regulated institutions. The actual
trade-off: BFT requires the participant set to be known and bounded in advance, and
in exchange you give up censorship resistance and anonymous participation. In return
you get better performance and governance control — the right trade for this use case.

**Node roles and participant authority.** In architectures like Hyperledger Fabric,
nodes have distinct roles with different responsibilities and different levels of
access. Ordering nodes sequence transactions and provide consensus; peer nodes
maintain the ledger and execute smart contract logic; clients submit transactions.
This separation means different participants can hold different roles with different
levels of authority and visibility. A custodian — a regulated institution that holds
and safeguards assets on behalf of clients and maintains the authoritative ownership
record under CVM supervision — can be a peer node that validates and sees only the
transactions relevant to its own clients, not the full network transaction history.
This is not a workaround; it is the design.

**Channels and confidential positions.** Permissioned DLT typically supports
sub-networks — channels in Fabric's terminology — where a subset of participants
share a private ledger with its own state. Privacy here means privacy from other
commercial participants, not from regulators — the CVM or BCB can be channel members
or granted access on demand. This mirrors how bilateral OTC trades work today:
private between counterparties, reported to regulators.

The typical pattern: price negotiation happens on a private channel visible only to
the two counterparties and the regulatory supervisor; the settlement instruction then
goes to a shared settlement channel where the custodian validates the ownership
transfer. Concrete example: Pension Fund A and Broker B agree on a CRI purchase on
a private channel. Once agreed, a settlement instruction is submitted to the shared
channel. The custodian validates that Fund A has the capital and Broker B holds the
asset. Ownership transfers atomically. The final ownership record is updated on the
shared ledger, visible to all network participants. The negotiated price remains
visible only to the channel members and the regulator.

**Smart contracts as compliance infrastructure.** Programmable logic — chaincode in
Fabric's terminology, smart contracts more generally — runs on the ledger itself and
is executed by all validating nodes as part of transaction validation. A transfer
restriction encoded in an asset token's smart contract is enforced by the network's
consensus mechanism, not by a developer remembering to call an API at settlement
time. This is the architectural lever that turns compliance from a per-transaction
manual process into a scalable infrastructure layer. The validity of a transaction
is checked automatically against the rules embedded in the asset — KYC status,
investor suitability, transfer restrictions, reporting triggers — before the
transaction is committed to the ledger.

---

## What This Decision Constrains

Choosing permissioned DLT as the foundational layer shapes several subsequent decisions
that cannot be deferred.

**Network governance.** Someone must decide who can join as a network participant,
under what conditions, and what happens when a participant needs to be removed. A
public blockchain eliminates this problem by making participation permissionless; a
permissioned network creates it as a deliberate design choice. This governance
responsibility is a centralization point worth watching: a network that is controlled
by one party is not structurally different from a centralized database. The governance
model must be designed to distribute authority meaningfully across participants, and
it must be designed before the network has enough participants to make the politics
complicated.

**Drex integration.** The settlement layer should be designed as a pluggable interface
from day one. Pluggable means the settlement layer is accessed through a defined
interface that abstracts the underlying mechanism — application logic calls something
like `settle(asset, payment, counterparty)` without depending on whether the
implementation is an internal ledger, a Drex-connected rail, or something else. When
Drex matures as a wholesale settlement rail, adopting it becomes an integration
project (implement a new adapter) rather than a redesign (change every place in the
codebase that assumes a specific settlement mechanism). Permissioned DLT's participant
and governance model is architecturally compatible with how Drex structures its own
network — the migration path exists, but only if the interface is kept clean from the
start. The cost of not doing this compounds as application code grows around a
specific settlement dependency. Full analysis of the Drex timeline and strategic
posture is in [`docs/drex-strategy.md`](../drex-strategy.md).

**Compliance encoding.** The decision to encode compliance rules in smart contracts
depends on the regulatory surface being stable enough to encode reliably. CVM
Resolution 88 established the framework for tokenized securities, but it is still
being shaped by regulatory guidance and interpretation. Rules that are volatile in
their details should be parameterized and upgradeable rather than hard-coded into
contract logic. This is a constraint on implementation, not a reason to defer the
architectural decision.

---

## Conclusion

Permissioned DLT as the foundational ledger layer, with the settlement interface
abstracted so the specific implementation can evolve.

The reasoning is not that DLT is technologically superior to centralized alternatives.
A well-engineered centralized system can handle the transaction volume this market
will produce. The reasoning is structural: the trust model of a multi-party secondary
market requires a shared ledger that no single party controls, and the regulatory
model of Brazilian capital markets requires that all participants be identified and
accountable. Those two constraints together select permissioned DLT. They disqualify
centralized databases for one reason — the trust model — and public blockchains for
a different reason — the accountability model. The architecture follows from the
constraints, not from a preference for the technology.

The uncertainty in this decision is not whether permissioned DLT is the right
architecture — that follows clearly from the constraints above. The uncertainty is
in the implementation details: which specific protocol, which governance structure,
how to handle the network bootstrapping problem when participants are still few. Those
are the decisions that will need to be revisited as the network matures.
