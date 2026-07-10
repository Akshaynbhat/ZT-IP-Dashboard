import time
import httpx
from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from app.config import settings

# JWKS Cache
jwks_cache = {
    "keys": [],
    "timestamp": 0.0
}
JWKS_TTL = 300.0

async def get_jwks() -> list:
    """
    Fetches the JWKS keys from Keycloak certs endpoint. Caches the keys for JWKS_TTL seconds.
    """
    current_time = time.time()
    if jwks_cache["keys"] and (current_time - jwks_cache["timestamp"] < JWKS_TTL):
        return jwks_cache["keys"]

    url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            jwks = response.json()
            jwks_cache["keys"] = jwks.get("keys", [])
            jwks_cache["timestamp"] = current_time
            return jwks_cache["keys"]
    except Exception as e:
        # Fallback to expired cache if it exists, otherwise raise 500 error
        if jwks_cache["keys"]:
            return jwks_cache["keys"]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve JWKS certificates from Keycloak: {str(e)}"
        )

async def validate_token(token: str) -> dict:
    """
    Decodes the JWT token header, retrieves the matching Key from Keycloak JWKS, 
    and validates signature, expiration, and audience.
    """
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token header missing 'kid'"
            )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token header structure: {str(e)}"
        )

    keys = await get_jwks()
    matching_key = None
    for key in keys:
        if key.get("kid") == kid:
            matching_key = key
            break

    if not matching_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Matching public certificate key not found in JWKS"
        )

    try:
        payload = jwt.decode(
            token,
            matching_key,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_CLIENT_ID
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token signature or claim verification failed: {str(e)}"
        )

def get_token_roles(payload: dict) -> list[str]:
    """
    Extracts the list of realm roles from the decoded token payload.
    """
    realm_access = payload.get("realm_access", {})
    return realm_access.get("roles", [])

def get_token_sub(payload: dict) -> str:
    """
    Extracts the keycloak_sub identifier from the decoded token payload.
    """
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing the 'sub' claim"
        )
    return sub
