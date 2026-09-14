# AXM Device Fabric

**Status: pre-alpha / contract experiment v0.1.1**

AXM Device Fabric explores a device-neutral boundary that lets an authorized human or machine intelligence use capabilities provided by a phone, laptop, desktop, VM, browser, robot, or future device without requiring the intelligence itself to live on that device.

The first evidence source is the separate [`axm-artemis-lab`](https://github.com/mike-axiom-mir/axm-artemis-lab), an experimental fork of Google ARTEMIS for real Android control. ARTEMIS remains an upstream Android implementation; this repository owns the AXM-neutral contract.

## Core idea

A device is a **capability-bearing node**, not a special category of intelligence.

```text
human / AI / specialist / buddy
            |
      Device Fabric contract
            |
   +--------+---------+---------+
   |        |         |         |
 Android  laptop    browser     VM   ...
 adapter   adapter    adapter   adapter
```

The neutral contract currently separates four things:

- **DeviceState** — what one adapter can truthfully observe now.
- **Capability** — what the adapter says the device can do, including explicit authority state and the exact operations currently inside that authority.
- **ActionRequest** — one bounded requested operation tied to a specific observed state.
- **ActionReceipt** — the reported outcome and evidence references for that request.

No adapter is allowed to imply that an unavailable, unknown, ungranted, or out-of-scope operation is usable.

## Four-root gate

The internal constitutional merge gate is:

1. **Truth** — observed facts, inference, unknowns, failures, and evidence must stay distinguishable.
2. **Agency / non-domination** — capability authority must not silently expand beyond the active grant or its explicit operation set.
3. **Continuity** — source provenance, state identity, action identity, request identity, and evidence links must survive handoffs.
4. **Wisdom before speed** — ambiguous or stale state should be surfaced rather than hidden for faster execution.

Git permission or implementation power is not canonical authority.

## Repository split

- **`axm-device-fabric`**: platform-neutral contracts, validation, receipts, adapter interface research.
- **`axm-artemis-lab`**: Android/ARTEMIS evidence and experiments.

The fork may teach this repository, but it does not define the generic architecture by itself.

## v0.1.1 implementation

The small Python contract lives in `src/axm_device_fabric/contracts.py`. It intentionally has no Android, ADB, MCP, model, cloud, or network dependency.

The structural request gate currently checks:

- device identity matches;
- the request is tied to the exact observed state digest;
- the device is connected;
- the requested capability was actually advertised;
- the capability is available;
- authority is explicitly granted;
- the action carries the same grant reference;
- the requested operation is explicitly inside that capability grant.

A separate receipt continuity check verifies that a receipt points back to the exact request and device it claims to report on.

This is **not** a finished policy engine and it does not yet control a real device.

## Next evidence step

Run ARTEMIS on one real Android test device with minimal changes, capture before/after observations and traces, then write the smallest `artemis-android` adapter that can translate those observed facts into this contract without inventing missing state.

See [`FOUNDATION.md`](./FOUNDATION.md) for boundaries and [`tests/`](./tests/) for executable contract checks.
