from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


DEFAULT_XANO_API_BASE_URL = "https://x8ki-letl-twmt.n7.xano.io/api:_832jVAW"
XANO_API_BASE_URL = os.environ.get(
    "XANO_API_BASE_URL",
    DEFAULT_XANO_API_BASE_URL,
).rstrip("/")
SUPPORTED_ROLES = {"owner", "manager", "operator"}
ROLE_LABELS = {
    "Proprietário": "owner",
    "Operador": "operator",
    "Admin": "manager",
}


class XanoApiError(Exception):
    def __init__(self, status_code: int, code: str = "", message: str = "") -> None:
        super().__init__(message or "Xano API request failed.")
        self.status_code = status_code
        self.code = code
        self.message = message or "Xano API request failed."


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int
    name: str
    email: str
    role: str
    is_active: bool | None = None


def normalize_role(value: str) -> str | None:
    role = value.strip()
    if role in ROLE_LABELS:
        return ROLE_LABELS[role]
    if role in SUPPORTED_ROLES:
        return role
    return None


def validate_password(password: str) -> str | None:
    if len(password) < 12:
        return "A senha deve ter pelo menos 12 caracteres."
    if not any(character.isupper() for character in password):
        return "A senha deve conter uma letra maiúscula."
    if not any(character.islower() for character in password):
        return "A senha deve conter uma letra minúscula."
    if not any(character.isdigit() for character in password):
        return "A senha deve conter um número."
    if not any(not character.isalnum() for character in password):
        return "A senha deve conter um caractere especial."
    return None


def _decode_response(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as error:
        raise XanoApiError(
            response.status_code,
            message="O Xano retornou uma resposta inválida.",
        ) from error

    if not isinstance(payload, dict):
        raise XanoApiError(
            response.status_code,
            message="O Xano retornou uma resposta incompatível.",
        )
    return payload


def _raise_for_api_error(response: httpx.Response) -> None:
    if response.is_success:
        return
    payload = _decode_response(response)
    raise XanoApiError(
        response.status_code,
        code=str(payload.get("code", "")),
        message=str(payload.get("message", "")),
    )


def _parse_user(payload: dict[str, Any]) -> AuthenticatedUser:
    try:
        user_id = int(payload["id"])
        name = str(payload["name"])
        email = str(payload["email"])
        role = str(payload["role"])
    except (KeyError, TypeError, ValueError) as error:
        raise XanoApiError(
            502,
            message="O Xano retornou dados de usuário incompletos.",
        ) from error

    if role not in SUPPORTED_ROLES:
        raise XanoApiError(
            502,
            message="O Xano retornou uma função de usuário não reconhecida.",
        )

    is_active = payload.get("is_active")
    if is_active is not None and not isinstance(is_active, bool):
        raise XanoApiError(
            502,
            message="O Xano retornou um estado de usuário inválido.",
        )

    return AuthenticatedUser(user_id, name, email, role, is_active)


async def login(email: str, password: str) -> tuple[str, int]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{XANO_API_BASE_URL}/auth/login",
                json={"email": email, "password": password},
            )
    except httpx.RequestError as error:
        raise XanoApiError(0, message="Não foi possível conectar ao Xano.") from error

    _raise_for_api_error(response)
    payload = _decode_response(response)
    token = payload.get("authToken")
    user_id = payload.get("user_id")
    if not isinstance(token, str) or not token or not isinstance(user_id, int):
        raise XanoApiError(
            502,
            message="O Xano retornou uma resposta de login incompatível.",
        )
    return token, user_id


async def get_current_user(token: str) -> AuthenticatedUser:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{XANO_API_BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.RequestError as error:
        raise XanoApiError(0, message="Não foi possível consultar o Xano.") from error

    _raise_for_api_error(response)
    return _parse_user(_decode_response(response))


async def create_employee(
    token: str,
    name: str,
    email: str,
    password: str,
    role: str,
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{XANO_API_BASE_URL}/users",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": name,
                    "email": email,
                    "password": password,
                    "role": role,
                },
            )
    except httpx.RequestError as error:
        raise XanoApiError(0, message="Não foi possível cadastrar no Xano.") from error

    _raise_for_api_error(response)
    payload = _decode_response(response)
    if not isinstance(payload.get("id"), int):
        raise XanoApiError(
            502,
            message="O Xano retornou uma resposta de cadastro incompatível.",
        )
    return payload
