# AXM Device Fabric Foundation

Status: **pre-alpha research contract**

## Purpose

Provide one small, inspectable contract for representing devices as capability-bearing nodes so different authorized intelligences can observe and act through them without each intelligence needing a device-specific architecture.

The first implementation target is Android through ARTEMIS, but Android must not become an accidental hard-coded definition of the fabric.

## What belongs in the core

Only concepts that can plausibly survive across device types:

- stable device identity;
- adapter identity;
- current connection state;
- point-in-time observations;
- advertised capabilities;
- explicit authority state and grant reference;
- bounded action requests;
- before-state linkage;
- outcome receipts;
- evidence references;
- explicit unknown / failure states.

## What belongs in adapters

Platform-specific mechanics stay outside the core. Examples:

- Android ADB and accessibility/UI hierarchy;
- Windows UI Automation;
- Linux desktop/session tooling;
- browser DOM / browser-control details;
- VM transport and lifecycle controls;
- robot/sensor protocols.

An adapter translates between its native mechanics and the neutral contract. It must not fabricate neutral facts that the native system did not actually provide.

## Contract direction v0.1

### DeviceState

A point-in-time view produced by an adapter. It includes identity, device kind, connection state, capabilities, observations, evidence references, and an observation timestamp.

The state has a deterministic digest. An action can be tied to that digest so stale or substituted state is detectable.

### Capability

A named operation family advertised by an adapter. v0.1 keeps three authority states:

- `granted`
- `denied`
- `unknown`

`unknown` is deliberately not equivalent to granted. A granted capability requires a grant reference so authority can be traced instead of silently inferred.

The exact grant system is intentionally outside this first contract; different AXM products may obtain legitimate grants differently.

### ActionRequest

One bounded operation addressed to one device, one capability, and one observed state. It records who/what requested the action, the state digest used when deciding, operation arguments, and the grant reference used.

### ActionReceipt

One outcome record tied to the exact request digest. v0.1 allows:

- `succeeded`
- `failed`
- `blocked`
- `unknown`

A receipt is evidence about what the adapter reports happened. It is not magical proof that every external consequence was observed.

## Root mapping

### Truth

- unknown stays unknown;
- stale-state mismatch is explicit;
- unavailable capabilities cannot silently become available;
- receipts distinguish success, failure, blocked, and unknown;
- device-specific observations remain attributable to their adapter/evidence.

### Agency / non-domination

- authority is explicit per capability;
- `unknown` and `denied` do not execute through the structural gate;
- granted authority must carry a traceable grant reference;
- a request cannot substitute another grant reference.

### Continuity

- device IDs, request IDs, state digests, request digests, and evidence references give later workers stable anchors;
- platform-specific provenance is preserved rather than rewritten into generic claims.

### Wisdom before speed

- a disconnected device, stale state, absent capability, or missing authority blocks the small structural gate instead of being hidden by optimistic fallback;
- richer recovery behavior can be added later when evidence shows what is actually needed.

## Non-goals for v0.1

This first contract does not claim to provide:

- complete device security;
- a universal permissions system;
- autonomous privilege escalation;
- semantic understanding of every screen;
- replay of arbitrary physical consequences;
- a production-ready networking protocol;
- Android control by itself.

Those would be false claims at this stage.

## First adapter experiment: ARTEMIS Android

The ARTEMIS fork already exposes evidence surfaces that look promising: live screenshot/hierarchy observation, task execution/lifecycle, traces, and diagnostics.

The first real-device experiment should answer only what we can measure:

1. What stable device identity can the adapter expose?
2. Which observations are reliable enough to reference as evidence?
3. Which action families can be advertised without exaggeration?
4. What happens when state changes between observe and act?
5. What evidence exists for success, failure, block, disconnect, and reconnect?
6. How much of this mapping remains meaningful when Android terms are removed?

Only after that baseline should the Android adapter grow.

## Merge discipline

Growth is welcome. Canonical claims must remain grounded.

A proposed core field should answer: **Which non-Android device class could also make meaningful use of this concept?** If there is no good answer yet, keep it in the adapter until evidence justifies promotion.
