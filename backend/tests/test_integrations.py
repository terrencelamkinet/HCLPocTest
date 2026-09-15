"""
Integration API Tests — tenant-isolated, async.

Run against running backend:
  source venv/bin/activate && pytest tests/test_integrations.py -v --capture=no

Requires: backend running on http://localhost:8001
"""
import pytest
import httpx
import uuid
from jose import jwt
from datetime import datetime, timezone

from app.config import settings
from app.services.auth_service import _load_private_key

BACKEND_URL = "http://localhost:8001"
KINETIX_TENANT = "00000000-0000-0000-0000-000000000001"
ALT_TENANT = "00000000-0000-0000-0000-000000000002"
TEST_USER = "9f3e7b11-e529-4cf8-82a6-2a62e4e5b643"
ALT_USER = "aaaaaaaa-e529-4cf8-82a6-2a62e4e5bbbb"

TEST_PROVIDER = "google_calendar"
TEST_PROVIDER_DISPLAY = "Google Calendar"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(sub: str, tenant_id: str, email: str = "test@test.com", role: str = "admin") -> str:
    """Generate a JWT for testing."""
    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "tenant_id": tenant_id,
    }
    return jwt.encode(payload, _load_private_key(), algorithm=settings.jwt_algorithm)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {_make_token(TEST_USER, KINETIX_TENANT)}"}


@pytest.fixture
def alt_auth_headers():
    """Different tenant, different user."""
    return {"Authorization": f"Bearer {_make_token(ALT_USER, ALT_TENANT, 'alt@test.com')}"}


@pytest.fixture(autouse=True)
async def cleanup_integrations():
    """Clean up all test integrations before each test so tests don't leak."""
    async with httpx.AsyncClient() as client:
        token = _make_token(TEST_USER, KINETIX_TENANT)
        headers = {"Authorization": f"Bearer {token}"}
        # List current integrations
        resp = await client.get(f"{BACKEND_URL}/api/v1/integrations", headers=headers)
        if resp.status_code == 200:
            for item in resp.json():
                await client.delete(f"{BACKEND_URL}/api/v1/integrations/{item['id']}", headers=headers)
    yield


# ===========================================================================
# Unauthenticated access
# ===========================================================================

class TestUnauthenticated:

    async def test_list_integrations_no_auth(self):
        """Without a Bearer token, the endpoint should return 403 (Tenant not identified)."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BACKEND_URL}/api/v1/integrations")
        assert resp.status_code == 403
        assert "Tenant not identified" in resp.json().get("detail", "")

    async def test_oauth_start_no_auth(self):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                json={"provider": TEST_PROVIDER},
            )
        assert resp.status_code == 403

    async def test_oauth_callback_no_auth(self):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                json={"code": "x", "state": "y"},
            )
        assert resp.status_code == 403


# ===========================================================================
# Fresh state — no integrations connected yet
# ===========================================================================

class TestFreshIntegration:

    async def test_list_integrations_empty(self, auth_headers):
        """Fresh user should have an empty list."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/integrations",
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_get_nonexistent_integration(self, auth_headers):
        fake_id = str(uuid.uuid4())
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/integrations/{fake_id}",
                headers=auth_headers,
            )
        assert resp.status_code == 404


# ===========================================================================
# OAuth start flow
# ===========================================================================

class TestOAuthStart:

    async def test_start_google_calendar(self, auth_headers):
        """Starting OAuth for Google Calendar should return state + oauth_url."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                headers=auth_headers,
                json={"provider": "google_calendar"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "state" in data
        assert len(data["state"]) > 20  # CSRF token
        assert "oauth_url" in data
        assert "google.com" in data["oauth_url"]
        assert data["provider"] == "google_calendar"
        # Verify redirect_uri points to frontend callback
        assert "/marketplace/oauth/callback" in data["oauth_url"]

    async def test_start_missing_provider(self, auth_headers):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                headers=auth_headers,
                json={},
            )
        assert resp.status_code == 400
        assert "provider" in resp.json().get("detail", "")

    async def test_start_webhook_provider(self, auth_headers):
        """Webhook-based providers (Zapier, Make) should return empty oauth_url."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                headers=auth_headers,
                json={"provider": "zapier"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["oauth_url"] == ""  # no OAuth for webhook


# ===========================================================================
# OAuth callback + complete flow
# ===========================================================================

class TestOAuthComplete:

    async def test_callback_invalid_state(self, auth_headers):
        """Random/invalid state should be rejected."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                headers=auth_headers,
                json={"code": "test_code_123", "state": "invalid_state_xyz"},
            )
        assert resp.status_code == 400
        assert "Invalid or expired" in resp.json().get("detail", "")

    async def test_callback_missing_params(self, auth_headers):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                headers=auth_headers,
                json={},
            )
        assert resp.status_code == 400

    async def test_full_oauth_flow(self, auth_headers):
        """Complete OAuth flow: start → callback → integration created."""
        async with httpx.AsyncClient() as client:
            # Step 1: Start OAuth
            start_resp = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                headers=auth_headers,
                json={"provider": TEST_PROVIDER},
            )
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        state = start_data["state"]

        # Step 2: Complete OAuth (simulate provider callback)
        async with httpx.AsyncClient() as client:
            cb_resp = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                headers=auth_headers,
                json={"code": "auth_code_abc", "state": state},
            )
        assert cb_resp.status_code == 200
        integration = cb_resp.json()
        assert integration["provider"] == TEST_PROVIDER
        assert integration["provider_display"] == TEST_PROVIDER_DISPLAY
        assert integration["status"] == "active"
        assert integration["tenant_id"] == KINETIX_TENANT
        assert integration["user_id"] == TEST_USER
        assert "config" in integration
        assert integration["config"]["access_token"].startswith("placeholder")
        assert "created_at" in integration
        assert "id" in integration

        # Step 3: Verify it shows up in the list
        async with httpx.AsyncClient() as client:
            list_resp = await client.get(
                f"{BACKEND_URL}/api/v1/integrations",
                headers=auth_headers,
            )
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) == 1
        assert items[0]["provider"] == TEST_PROVIDER

        # Store integration ID for later tests
        return integration["id"]

    async def test_full_flow_with_all_providers(self, auth_headers):
        """Test OAuth flow for each known provider type."""
        providers = [
            "google_calendar", "outlook_calendar", "gmail", "outlook_mail",
            "slack", "zoom", "whatsapp", "teams",
            "google_drive", "dropbox", "onedrive",
            "linkedin", "facebook",
            "notion", "stripe", "quickbooks", "mailchimp", "hubspot",
        ]
        created_ids = []

        async with httpx.AsyncClient() as client:
            for provider in providers:
                # Start
                start_resp = await client.post(
                    f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                    headers=auth_headers,
                    json={"provider": provider},
                )
                assert start_resp.status_code == 200, f"Failed to start {provider}"
                state = start_resp.json()["state"]

                # Callback
                cb_resp = await client.post(
                    f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                    headers=auth_headers,
                    json={"code": f"code_{provider}", "state": state},
                )
                assert cb_resp.status_code == 200, f"Failed callback for {provider}"
                integ = cb_resp.json()
                assert integ["provider"] == provider
                assert integ["status"] == "active"
                created_ids.append(integ["id"])

        # Verify all 18 providers were created
        async with httpx.AsyncClient() as client:
            list_resp = await client.get(
                f"{BACKEND_URL}/api/v1/integrations",
                headers=auth_headers,
            )
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) == len(providers)

        return created_ids


# ===========================================================================
# Integration CRUD
# ===========================================================================

class TestIntegrationCRUD:

    async def test_create_url_connection(self, auth_headers):
        """POST /integrations should create a URL-based connection directly."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/v1/integrations",
                headers=auth_headers,
                json={
                    "provider": "google_calendar",
                    "provider_display": "Google Calendar",
                    "status": "active",
                    "config": {"connection_url": "https://calendar.google.com/calendar/ical/test/basic.ics"},
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["provider"] == "google_calendar"
        assert data["config"]["connection_url"] == "https://calendar.google.com/calendar/ical/test/basic.ics"
        assert data["status"] == "active"
        assert data["tenant_id"] == KINETIX_TENANT
        return data["id"]

    async def test_update_integration_status(self, auth_headers):
        """PATCH should update status and config."""
        # First create one
        async with httpx.AsyncClient() as client:
            start = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                headers=auth_headers,
                json={"provider": "outlook_calendar"},
            )
            state = start.json()["state"]
            cb = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                headers=auth_headers,
                json={"code": "code_outlook", "state": state},
            )
        integ_id = cb.json()["id"]

        # Update
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{BACKEND_URL}/api/v1/integrations/{integ_id}",
                headers=auth_headers,
                json={"status": "error", "metadata_": {"last_error": "token_expired"}},
            )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["status"] == "error"
        assert updated["metadata_"]["last_error"] == "token_expired"

    async def test_delete_integration(self, auth_headers):
        """DELETE should remove the integration."""
        # Create one
        async with httpx.AsyncClient() as client:
            start = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                headers=auth_headers,
                json={"provider": "slack"},
            )
            state = start.json()["state"]
            cb = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                headers=auth_headers,
                json={"code": "code_slack", "state": state},
            )
        integ_id = cb.json()["id"]

        # Delete
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BACKEND_URL}/api/v1/integrations/{integ_id}",
                headers=auth_headers,
            )
        assert resp.status_code == 204

        # Verify gone
        async with httpx.AsyncClient() as client:
            get_resp = await client.get(
                f"{BACKEND_URL}/api/v1/integrations/{integ_id}",
                headers=auth_headers,
            )
        assert get_resp.status_code == 404

    async def test_get_single_integration(self, auth_headers):
        """GET by ID should return the full record."""
        # Create one
        async with httpx.AsyncClient() as client:
            start = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                headers=auth_headers,
                json={"provider": "gmail"},
            )
            state = start.json()["state"]
            cb = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                headers=auth_headers,
                json={"code": "code_gmail", "state": state},
            )
        integ_id = cb.json()["id"]

        # Get
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/integrations/{integ_id}",
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == integ_id
        assert data["provider"] == "gmail"
        assert data["status"] == "active"


# ===========================================================================
# Tenant isolation — critical security test
# ===========================================================================

class TestTenantIsolation:

    async def test_cross_tenant_invisible(self, auth_headers, alt_auth_headers):
        """User A's integrations should be invisible to User B (different tenant)."""

        # User A creates an integration
        async with httpx.AsyncClient() as client:
            start = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                headers=auth_headers,
                json={"provider": TEST_PROVIDER},
            )
            state = start.json()["state"]
            await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                headers=auth_headers,
                json={"code": "code_a", "state": state},
            )

        # User B (different tenant) should see nothing
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/integrations",
                headers=alt_auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 0, "Cross-tenant data leak detected!"

    async def test_cross_tenant_get_blocked(self, auth_headers, alt_auth_headers):
        """User B should get 404 trying to access User A's integration by ID."""
        # Create as User A
        async with httpx.AsyncClient() as client:
            start = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                headers=auth_headers,
                json={"provider": "outlook_calendar"},
            )
            state = start.json()["state"]
            cb = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                headers=auth_headers,
                json={"code": "code_outlook", "state": state},
            )
        integ_id = cb.json()["id"]

        # User B tries to access User A's integration
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/integrations/{integ_id}",
                headers=alt_auth_headers,
            )
        assert resp.status_code == 404, "Cross-tenant read leak!"

        # User B tries to delete User A's integration
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BACKEND_URL}/api/v1/integrations/{integ_id}",
                headers=alt_auth_headers,
            )
        assert resp.status_code == 404, "Cross-tenant delete leak!"


# ===========================================================================
# Error scenarios
# ===========================================================================

class TestErrorScenarios:

    async def test_duplicate_oauth_state_rejected(self, auth_headers):
        """Using the same OAuth state twice should fail."""
        async with httpx.AsyncClient() as client:
            start = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/start",
                headers=auth_headers,
                json={"provider": TEST_PROVIDER},
            )
            state = start.json()["state"]

            # First use — OK
            cb1 = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                headers=auth_headers,
                json={"code": "code_first", "state": state},
            )
            assert cb1.status_code == 200

            # Second use with same state — should fail (state was deleted)
            cb2 = await client.post(
                f"{BACKEND_URL}/api/v1/integrations/oauth/callback",
                headers=auth_headers,
                json={"code": "code_second", "state": state},
            )
            assert cb2.status_code == 400

    async def test_bad_integration_id_format(self, auth_headers):
        """Non-UUID string should be rejected gracefully."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/integrations/not-a-uuid",
                headers=auth_headers,
            )
        # FastAPI validates UUID path params — returns 422 or similar
        assert resp.status_code in (422, 404)
