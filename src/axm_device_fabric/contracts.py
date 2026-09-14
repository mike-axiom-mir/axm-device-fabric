"""Small deterministic contracts for AXM Device Fabric v0.1.1.

This module intentionally contains no device-specific control code.
Adapters translate platform-specific observations/actions into these contracts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

SCHEMA_VERSION = "0.1.1"

AUTHORITY_STATES = {"granted", "denied", "unknown"}
CONNECTION_STATES = {"connected", "disconnected", "degraded", "unknown"}
RECEIPT_STATES = {"succeeded", "failed", "blocked", "unknown"}


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def canonical_json(value: Any) -> str:
    """Return a stable JSON representation suitable for hashing/evidence links."""
    return json.dumps(
        _plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def digest(value: Any) -> str:
    """Return a sha256 digest of the canonical JSON representation."""
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Capability:
    """One capability advertised by a device adapter.

    ``authority`` is deliberately explicit. Unknown is not treated as granted.
    ``grant_ref`` points to the external evidence/policy that granted authority.

    ``operations`` is the bounded set of operations this capability may execute.
    A granted capability without an explicit operation set is invalid: a family
    name alone must not silently authorize arbitrary operations.
    """

    name: str
    available: bool
    authority: str = "unknown"
    grant_ref: str | None = None
    operations: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("capability name must not be empty")
        if self.authority not in AUTHORITY_STATES:
            raise ValueError(f"invalid authority state: {self.authority}")
        if self.authority == "granted" and not self.grant_ref:
            raise ValueError("granted capability requires grant_ref")

        normalized = [operation.strip() for operation in self.operations]
        if any(not operation for operation in normalized):
            raise ValueError("capability operations must not contain empty values")
        if len(normalized) != len(set(normalized)):
            raise ValueError("capability operations must be unique")
        if self.authority == "granted" and not normalized:
            raise ValueError("granted capability requires explicit operations")


@dataclass(frozen=True)
class DeviceState:
    """A point-in-time, adapter-produced view of one device."""

    device_id: str
    adapter_id: str
    device_kind: str
    connection: str
    observed_at: str
    capabilities: tuple[Capability, ...] = ()
    observations: Mapping[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()
    current_surface: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in ("device_id", "adapter_id", "device_kind", "observed_at"):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.connection not in CONNECTION_STATES:
            raise ValueError(f"invalid connection state: {self.connection}")

        names = [cap.name for cap in self.capabilities]
        if len(names) != len(set(names)):
            raise ValueError("capability names must be unique within a device state")

    def capability(self, name: str) -> Capability | None:
        return next((cap for cap in self.capabilities if cap.name == name), None)


@dataclass(frozen=True)
class ActionRequest:
    """A bounded request against one observed device state."""

    request_id: str
    device_id: str
    capability: str
    operation: str
    requested_by: str
    state_digest: str
    arguments: Mapping[str, Any] = field(default_factory=dict)
    grant_ref: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "device_id",
            "capability",
            "operation",
            "requested_by",
            "state_digest",
        ):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True)
class ActionReceipt:
    """Evidence record for the outcome of an ActionRequest."""

    request_id: str
    device_id: str
    status: str
    request_digest: str
    completed_at: str
    evidence_refs: tuple[str, ...] = ()
    detail: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "device_id",
            "request_digest",
            "completed_at",
        ):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.status not in RECEIPT_STATES:
            raise ValueError(f"invalid receipt status: {self.status}")


def validate_request_against_state(
    state: DeviceState,
    request: ActionRequest,
) -> tuple[str, ...]:
    """Return structural blockers; an empty tuple means this small gate passes.

    This is deliberately not a complete policy engine. It checks only facts
    carried by the current state/request contract.
    """

    blockers: list[str] = []

    if state.device_id != request.device_id:
        blockers.append("device_id_mismatch")

    current_digest = digest(state)
    if request.state_digest != current_digest:
        blockers.append("state_digest_mismatch")

    if state.connection != "connected":
        blockers.append("device_not_connected")

    capability = state.capability(request.capability)
    if capability is None:
        blockers.append("capability_not_advertised")
        return tuple(blockers)

    if not capability.available:
        blockers.append("capability_unavailable")

    if capability.authority != "granted":
        blockers.append("capability_not_granted")
    elif capability.grant_ref != request.grant_ref:
        blockers.append("grant_ref_mismatch")

    if request.operation not in capability.operations:
        blockers.append("operation_not_granted")

    return tuple(blockers)


def validate_receipt_against_request(
    request: ActionRequest,
    receipt: ActionReceipt,
) -> tuple[str, ...]:
    """Return continuity blockers between an action request and its receipt.

    A structurally valid receipt is still not proof of every external effect.
    This only checks that the receipt is linked to the exact request/device it
    claims to report on.
    """

    blockers: list[str] = []

    if receipt.request_id != request.request_id:
        blockers.append("request_id_mismatch")

    if receipt.device_id != request.device_id:
        blockers.append("device_id_mismatch")

    if receipt.request_digest != digest(request):
        blockers.append("request_digest_mismatch")

    return tuple(blockers)
