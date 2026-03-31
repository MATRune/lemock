import typing
import jwt
from fastapi import Request
from pwdlib import PasswordHash
from datetime import timedelta, datetime, timezone
from app.config import get_settings


password_hash = PasswordHash.recommended()
def flash(request: Request, message: str) -> None:
    if "_messages" not in request.session:
        request.session["_messages"] = []
    request.session["_messages"].append(message)


def get_flashed_messages(request: Request):
   return request.session.pop("_messages") if "_messages" in request.session else []

def encrypt_password(password: str):
    return PasswordHash.recommended().hash(password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=get_settings().jwt_access_token_expires)):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_settings().secret_key, algorithm=get_settings().jwt_algorithm)
    return encoded_jwt
