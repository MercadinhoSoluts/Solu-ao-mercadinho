from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import date
from math import isfinite
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


def parse_product_weight(value: str) -> int | float | None:
    try:
        weight = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        return None
    if not weight.is_finite():
        return None
    if weight == weight.to_integral_value():
        return int(weight)
    parsed = float(weight)
    return parsed if isfinite(parsed) else None


def is_valid_product_text(value: str) -> bool:
    normalized = value.strip()
    return bool(normalized) and all(
        character.isalpha() or character == " "
        for character in normalized
    )


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


async def create_product(
    token: str,
    tipo: str,
    marca: str,
    peso: int | float,
    codigo_de_barra: str,
) -> dict[str, Any]:
    payload = {
        "tipo": tipo,
        "marca": marca,
        "peso": peso,
        "codigo_de_barra": codigo_de_barra,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{XANO_API_BASE_URL}/produtos",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
    except httpx.RequestError as error:
        raise XanoApiError(0, message="Não foi possível conectar ao Xano.") from error

    _raise_for_api_error(response)
    result = _decode_response(response)
    if not isinstance(result.get("id"), int):
        raise XanoApiError(
            502,
            message="O Xano não confirmou o cadastro do produto.",
        )
    if (
        result.get("tipo") != tipo
        or result.get("marca") != marca
        or result.get("codigo_de_barra") != codigo_de_barra
    ):
        raise XanoApiError(
            502,
            message="O Xano retornou um produto diferente dos dados enviados.",
        )
    try:
        returned_weight = Decimal(str(result["peso"]))
    except (KeyError, InvalidOperation, TypeError, ValueError) as error:
        raise XanoApiError(
            502,
            message="O Xano retornou um peso inválido para o produto.",
        ) from error
    if returned_weight != Decimal(str(peso)):
        raise XanoApiError(
            502,
            message="O Xano retornou um peso diferente do informado.",
        )
    return result


def parse_inventory_units(value: str) -> int | None:
    try:
        units = int(value.strip())
    except (AttributeError, TypeError, ValueError):
        return None
    return units if units > 0 else None


def parse_inventory_date(value: str) -> str | None:
    try:
        return date.fromisoformat(value.strip()).isoformat()
    except (AttributeError, TypeError, ValueError):
        return None


async def list_products(token: str) -> list[dict[str, Any]]:
    return await _list_xano_records(token, "/produtos")


async def list_inventory(token: str) -> list[dict[str, Any]]:
    return await _list_xano_records(token, "/estoque")


async def _list_xano_records(token: str, path: str) -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{XANO_API_BASE_URL}{path}",
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.RequestError as error:
        raise XanoApiError(0, message="Não foi possível conectar ao Xano.") from error

    _raise_for_api_error(response)
    payload = response.json()
    if not isinstance(payload, list) or not all(
        isinstance(record, dict) for record in payload
    ):
        raise XanoApiError(
            502,
            message="O Xano retornou uma lista inválida.",
        )
    return payload


async def create_inventory_lot(
    token: str,
    produtos_id: int,
    unidades: int,
    validade: str,
    lote: str,
) -> dict[str, Any]:
    return await _mutate_inventory(
        token,
        "post",
        "/estoque",
        {
            "produtos_id": produtos_id,
            "unidades": unidades,
            "validade": validade,
            "lote": lote,
        },
    )


async def update_inventory_lot(
    token: str,
    estoque_id: int,
    unidades: int,
) -> dict[str, Any]:
    return await _mutate_inventory(
        token,
        "patch",
        f"/estoque/{estoque_id}",
        {"unidades": unidades},
    )


async def _mutate_inventory(
    token: str,
    method: str,
    path: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            request = getattr(client, method)
            response = await request(
                f"{XANO_API_BASE_URL}{path}",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
    except httpx.RequestError as error:
        raise XanoApiError(0, message="Não foi possível conectar ao Xano.") from error

    _raise_for_api_error(response)
    result = _decode_response(response)
    if not isinstance(result.get("id"), int):
        raise XanoApiError(
            502,
            message="O Xano não confirmou a atualização do estoque.",
        )
    return result
