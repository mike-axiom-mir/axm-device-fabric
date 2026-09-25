import unittest

from axm_device_fabric.contracts import (
    ActionReceipt,
    ActionRequest,
    Capability,
    DeviceState,
    digest,
    validate_receipt_against_request,
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
                    operations=("open_settings",),
                    evidence_refs=("evidence:hierarchy:001",),
                ),
            ),
            observations={"surface": "home"},
            evidence_refs=("evidence:screenshot:001",),
            current_surface="home",
        )

    def make_request(self, state=None):
        state = state or self.make_state()
        return ActionRequest(
            request_id="action-001",
            device_id=state.device_id,
            capability="ui.navigate",
            operation="open_settings",
            requested_by="axm:test",
            state_digest=digest(state),
            grant_ref="grant:test-session",
        )

    def test_digest_is_stable(self):
        state = self.make_state()
        self.assertEqual(digest(state), digest(state))

    def test_availability_requires_an_explicit_boolean(self):
        for value in ("false", "true", 0, 1, None, [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Capability(name="ui.navigate", available=value, authority="granted",
                           grant_ref="grant:test", operations=("open",))

    def test_unavailable_capability_stays_blocked(self):
        from dataclasses import replace
        state = self.make_state()
        state = replace(state, capabilities=(replace(state.capabilities[0], available=False),))
        self.assertIn("capability_unavailable", validate_request_against_state(state, self.make_request(state)))

    def test_nonfinite_observations_cannot_acquire_a_state_digest(self):
        from dataclasses import replace
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                digest(replace(self.make_state(), observations={"reading": [value]}))

    def test_matching_request_passes(self):
        state = self.make_state()
        request = self.make_request(state)
        self.assertEqual(validate_request_against_state(state, request), ())

    def test_unknown_authority_does_not_pass(self):
        state = DeviceState(
            device_id="device-01",
            adapter_id="adapter-01",
            device_kind="other",
            connection="connected",
            observed_at="2026-09-14T06:00:00+02:00",
            capabilities=(
                Capability(
                    name="ui.navigate",
                    available=True,
                    authority="unknown",
                    operations=("open",),
                ),
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

    def test_granted_capability_requires_explicit_operations(self):
        with self.assertRaises(ValueError):
            Capability(
                name="ui.navigate",
                available=True,
                authority="granted",
                grant_ref="grant:test-session",
            )

    def test_operation_outside_grant_is_blocked(self):
        state = self.make_state()
        request = ActionRequest(
            request_id="action-unsafe",
            device_id=state.device_id,
            capability="ui.navigate",
            operation="factory_reset",
            requested_by="axm:test",
            state_digest=digest(state),
            grant_ref="grant:test-session",
        )
        self.assertIn(
            "operation_not_granted",
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

    def test_matching_receipt_links_to_exact_request(self):
        state = self.make_state()
        request = self.make_request(state)
        receipt = ActionReceipt(
            request_id=request.request_id,
            device_id=request.device_id,
            status="succeeded",
            request_digest=digest(request),
            completed_at="2026-09-14T06:01:00+02:00",
            evidence_refs=("evidence:screenshot:002",),
        )
        self.assertEqual(validate_receipt_against_request(request, receipt), ())

    def test_receipt_request_digest_mismatch_is_detected(self):
        state = self.make_state()
        request = self.make_request(state)
        receipt = ActionReceipt(
            request_id=request.request_id,
            device_id=request.device_id,
            status="succeeded",
            request_digest="sha256:not-the-request",
            completed_at="2026-09-14T06:01:00+02:00",
        )
        self.assertIn(
            "request_digest_mismatch",
            validate_receipt_against_request(request, receipt),
        )


if __name__ == "__main__":
    unittest.main()
