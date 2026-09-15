"""
Tenant middleware for FastAPI.

Extracts tenant_id from the JWT access token (Bearer auth header),
decodes it using decode_token from app.services.auth_service,
and stores the tenant_id in request.state.tenant_id.

If no token is present or the token is invalid, tenant_id is set
to an empty string so the request can continue (auth endpoints or
route-level dependencies can handle enforcement).

When a token is present but expired (valid structure, past expiry),
request.state.auth_status is set to "expired" so the router layer
can return an HTTP 401 instead of a misleading 403, which lets the
frontend's refresh flow kick in properly.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.auth_service import decode_token, _load_public_key
from jose import jwt
from app.config import settings


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts tenant context from the JWT access token.

    Steps:
    1. Extract Bearer token from the Authorization header.
    2. If no token is present, skip (set tenant_id to "" and continue).
    3. Decode the token via decode_token to get tenant_id + user_id.
    4. Store tenant_id in request.state.tenant_id.
    5. If the token is invalid, set tenant_id to "" (no tenant context,
       request continues without failure).
    6. If the token is expired (valid signature but past exp), set
       request.state.auth_status = "expired" so routers return 401.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Default: no tenant context
        request.state.tenant_id = ""
        request.state.user_id = ""
        request.state.auth_status = ""  # "expired" if token is valid but expired

        # Admin console（2026-09-09）：require_superadmin 自己 decode + guard —
        # 唔好喺 middleware 對無 tenant 嘅 admin call 403（nexus_admin 唔靠 tenant RLS）
        if request.url.path.startswith("/api/v1/admin"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()

            if token:
                payload = decode_token(token)

                if payload is not None:
                    # Valid token — extract tenant_id and user_id
                    tenant_id = payload.get("tenant_id", "")
                    user_id = payload.get("sub", "")

                    request.state.tenant_id = tenant_id or ""
                    request.state.user_id = user_id or ""
                else:
                    # decode_token returned None — could be expired or invalid
                    # Try decoding without expiry check to distinguish
                    try:
                        pub_key = _load_public_key()
                        expired_payload = jwt.decode(
                            token,
                            pub_key,
                            algorithms=[settings.jwt_algorithm],
                            options={"verify_exp": False},
                        )
                        # Payload is structurally valid but expired → flag it
                        request.state.auth_status = "expired"
                        # Still set tenant_id/user_id from the expired payload
                        # so that specialized handling can use them if needed
                        request.state.tenant_id = expired_payload.get("tenant_id", "") or ""
                        request.state.user_id = expired_payload.get("sub", "") or ""
                    except Exception:
                        # Truly invalid token — leave everything as default
                        pass

        # Proceed with the request regardless of tenant state
        response = await call_next(request)
        return response
