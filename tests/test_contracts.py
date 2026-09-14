import unittest

from axm_device_fabric.contracts import (
    ActionReceipt,
    ActionRequest,
    Capability,
    DeviceState,
    digest,
    validate_request_against_state,
)


class ContractTests(unittest.TestCase):
    def make_state(self):
        return DeviceState(
            device_id="android-test-01",
            adapter_id="artemis-android",
            device_kind="android",
            connection="connected",
            observed_at="2026-09-14T06:00:00+02:00",
            capabilities=(
                Capability(
                    name="ui.navigate",
                    available=True,
                    authority="granted",
                    grant_ref="grant:test-session",
                    evidence_refs=("evidence:hierarchy:001",),
                ),
            ),
            observations={"surface": "home"},
            evidence_refs=("evidence:screenshot:001",),
            current_surface="home",
        )

    def test_digest_is_stable(self):
        state = self.make_state()
        self.assertEqual(digest(state), digest(state))

    def test_matching_request_passes(self):
        state = self.make_state()
        request = ActionRequest(
            request_id="action-001",
            device_id=state.device_id,
            capability="ui.navigate",
            operation="open_settings",
            requested_by="axm:test",
            state_digest=digest(state),
            grant_ref="grant:test-session",
        )
        self.assertEqual(validate_request_against_state(state, request), ())

    def test_unknown_authority_does_not_pass(self):
        state = DeviceState(
            device_id="device-01",
            adapter_id="adapter-01",
            device_kind="other",
            connection="connected",
            observed_at="2026-09-14T06:00:00+02:00",
            capabilities=(
                Capability(name="ui.navigate", available=True, authority="unknown"),
            ),
        )
        request = ActionRequest(
            request_id="action-002",
            device_id=state.device_id,
            capability="ui.navigate",
            operation="open",
            requested_by="axm:test",
            state_digest=digest(state),
        )
        self.assertIn(
            "capability_not_granted",
            validate_request_against_state(state, request),
        )

    def test_stale_state_is_detected(self):
        state = self.make_state()
        request = ActionRequest(
            request_id="action-003",
            device_id=state.device_id,
            capability="ui.navigate",
            operation="open_settings",
            requested_by="axm:test",
            state_digest="sha256:stale",
            grant_ref="grant:test-session",
        )
        self.assertIn(
            "state_digest_mismatch",
            validate_request_against_state(state, request),
        )

    def test_receipt_status_is_bounded(self):
        with self.assertRaises(ValueError):
            ActionReceipt(
                request_id="action-004",
                device_id="device-01",
                status="probably",
                request_digest="sha256:x",
                completed_at="2026-09-14T06:00:00+02:00",
            )


if __name__ == "__main__":
    unittest.main()
