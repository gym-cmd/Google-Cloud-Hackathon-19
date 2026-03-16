import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

_bearer_scheme = HTTPBearer()
_firebase_app = None


def init_firebase():
    """Initialize Firebase Admin SDK. Call once at app startup."""
    global _firebase_app
    if _firebase_app is not None:
        return

    cred_path = settings.firebase_credentials_path
    if cred_path:
        cred = credentials.Certificate(cred_path)
    else:
        # Falls back to GOOGLE_APPLICATION_CREDENTIALS env var or default credentials
        cred = credentials.ApplicationDefault()

    _firebase_app = firebase_admin.initialize_app(cred)


async def get_current_user(
    credential: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """Verify Firebase ID token from Authorization header.

    Returns the decoded token dict with at least 'uid', 'email', etc.
    """
    token = credential.credentials
    try:
        decoded = auth.verify_id_token(token)
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return decoded
