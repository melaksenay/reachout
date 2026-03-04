# app/core/auth.py
import jwt
from jwt.api_jwk import PyJWK
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache

bearer_scheme = HTTPBearer()

# Public key from Supabase project JWKS endpoint (not a secret)
_SUPABASE_JWK = {
    "alg": "ES256",
    "crv": "P-256",
    "ext": True,
    "key_ops": ["verify"],
    "kid": "ff3964d2-ef75-443a-8e84-88a62a7e5c95",
    "kty": "EC",
    "use": "sig",
    "x": "kt5wUzjHkEQK9XCbUDvsI-H_O3Qt3d2RCJPv-q6TtfE",
    "y": "Tmn7u2I23Jes7gF43L2u7t57DDEQFHjqHqioMp1eZls",
}


@lru_cache()
def _get_signing_key():
    return PyJWK.from_dict(_SUPABASE_JWK).key


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Decode Supabase JWT and return the user's UUID (sub claim)."""
    token = credentials.credentials
    try:
        signing_key = _get_signing_key()
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["ES256"],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError as e:
        print(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub claim",
        )
    return user_id
