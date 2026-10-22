from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from math import isfinite
from time import time
from typing import Any
from urllib.parse import urlsplit

import httpx
from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError

from bipsystem.supabase_client import (
    SupabaseConfigurationError,
    request_supabase_client,
)


SUPPORTED_ROLES = {"owner", "manager", "operator"}
ROLE_ALIASES = {
    "admin": "manager",
    "administrador": "manager",
    "administradora": "manager",
    "gerente": "manager",
    "gestor": "manager",
    "manager": "manager",
    "proprietario": "owner",
    "proprietário": "owner",
    "proprietaria": "owner",
    "dono": "owner",
    "owner": "owner",
    "caixa": "operator",
    "cashier": "operator",
    "operador": "operator",
    "operadora": "operator",
    "funcionario": "operator",
    "funcionário": "operator",
    "operator": "operator",
}
ROLE_LABELS = {
    "Proprietário": "owner",
    "Operador": "operator",
    "Caixa": "operator",
    "Admin": "manager",
    "Administrador": "manager",
}


class SupabaseApiError(Exception):
    def __init__(self, status_code: int, code: str = "", message: str = "") -> None:
        super().__init__(message or "Supabase request failed.")
        self.status_code = status_code
        self.code = code
        self.message = message or "Supabase request failed."


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    name: str
    email: str
    role: str
    is_active: bool


@dataclass(frozen=True)
class AuthSession:
    access_token: str
    refresh_token: str
    expires_at: int


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
    normalized = ROLE_ALIASES.get(role.casefold())
    if normalized is not None:
        return normalized
    return role if role in SUPPORTED_ROLES else None


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


def _translate_error(error: APIError | AuthApiError) -> SupabaseApiError:
    error_code = str(getattr(error, "code", "") or "")
    status = getattr(error, "status", None)
    if status is None:
        status = getattr(error, "status_code", None)
    if status is None:
        status = 400 if isinstance(error, AuthApiError) else 500

    if error_code in {"23505", "email_exists"}:
        status = 409
    elif error_code == "42501":
        status = 403
    elif error_code.startswith(("22", "23")):
        status = 400

    safe_messages = {
        400: "Verifique os dados informados e tente novamente.",
        401: "Sessão inválida ou expirada.",
        403: "Você não tem autorização para realizar esta ação.",
        409: "Já existe um registro com esses dados.",
    }
    return SupabaseApiError(
        int(status),
        error_code,
        safe_messages.get(int(status), "O Supabase não conseguiu concluir a operação."),
    )


def _session_from_response(response: Any) -> AuthSession:
    session = getattr(response, "session", None)
    access_token = getattr(session, "access_token", None)
    refresh_token = getattr(session, "refresh_token", None)
    expires_at = getattr(session, "expires_at", None)
    if not isinstance(expires_at, int):
        expires_in = getattr(session, "expires_in", None)
        if isinstance(expires_in, int) and expires_in > 0:
            expires_at = int(time()) + expires_in
    if (
        not isinstance(access_token, str)
        or not access_token
        or not isinstance(refresh_token, str)
        or not refresh_token
        or not isinstance(expires_at, int)
    ):
        raise SupabaseApiError(
            502,
            "invalid_session",
            "O Supabase retornou uma sessão incompatível.",
        )
    return AuthSession(access_token, refresh_token, expires_at)


def _parse_profile(profile: Any) -> AuthenticatedUser:
    if not isinstance(profile, dict):
        raise SupabaseApiError(
            403,
            "profile_missing",
            "Não foi encontrado um perfil válido para esta conta.",
        )
    try:
        user_id = str(profile["id"])
        name = str(profile["name"])
        email = str(profile["email"])
        raw_role = str(profile["role"])
        is_active = profile["is_active"]
    except (KeyError, TypeError, ValueError) as error:
        raise SupabaseApiError(
            502,
            "invalid_profile",
            "O perfil retornado pelo Supabase é inválido.",
        ) from error

    role = normalize_role(raw_role)
    if (
        not user_id
        or not name.strip()
        or not email.strip()
        or role is None
        or not isinstance(is_active, bool)
    ):
        raise SupabaseApiError(
            403,
            "invalid_profile",
            "A conta não possui um perfil ativo e válido.",
        )
    return AuthenticatedUser(user_id, name, email, role, is_active)


async def login(email: str, password: str) -> AuthSession:
    normalized_email = email.strip().lower()
    if not normalized_email or not password:
        raise SupabaseApiError(400, "invalid_credentials", "Credenciais inválidas.")
    try:
        async with request_supabase_client() as client:
            response = await client.auth.sign_in_with_password(
                {"email": normalized_email, "password": password}
            )
        return _session_from_response(response)
    except (AuthApiError, APIError) as error:
        raise _translate_error(error) from error
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível conectar ao Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


async def refresh_session(refresh_token: str) -> AuthSession:
    try:
        async with request_supabase_client() as client:
            response = await client.auth.refresh_session(refresh_token)
        return _session_from_response(response)
    except (AuthApiError, APIError) as error:
        raise _translate_error(error) from error
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível renovar a sessão do Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


async def get_current_user(token: str) -> AuthenticatedUser:
    try:
        async with request_supabase_client(token) as client:
            auth_response = await client.auth.get_user(token)
            auth_user = getattr(auth_response, "user", None)
            user_id = getattr(auth_user, "id", None)
            if not isinstance(user_id, str) or not user_id:
                raise SupabaseApiError(
                    401,
                    "invalid_session",
                    "Sessão inválida ou expirada.",
                )
            profile_response = await (
                client.table("profiles")
                .select("id, name, email, role, is_active")
                .eq("id", user_id)
                .maybe_single()
                .execute()
            )
        profile = _parse_profile(profile_response.data)
        if profile.user_id != user_id:
            raise SupabaseApiError(
                403,
                "invalid_profile",
                "O perfil não corresponde à identidade autenticada.",
            )
        return profile
    except SupabaseApiError:
        raise
    except (AuthApiError, APIError) as error:
        raise _translate_error(error) from error
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível consultar o Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


async def logout(token: str) -> None:
    try:
        url, anon_key = _supabase_configuration()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{url}/auth/v1/logout",
                headers={
                    "apikey": anon_key,
                    "Authorization": f"Bearer {token}",
                },
            )
        if not response.is_success:
            raise SupabaseApiError(
                response.status_code,
                "logout_failed",
                "O Supabase não confirmou o encerramento da sessão.",
            )
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível encerrar a sessão do Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


def _supabase_configuration() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if not url or not anon_key:
        raise SupabaseApiError(
            500,
            "configuration_error",
            "Configure SUPABASE_URL e SUPABASE_ANON_KEY para usar o Supabase.",
        )
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SupabaseApiError(
            500,
            "configuration_error",
            "SUPABASE_URL deve ser uma URL HTTP ou HTTPS válida.",
        )
    return url, anon_key


async def _employee_action(token: str, payload: dict[str, Any]) -> dict[str, Any]:
    url, anon_key = _supabase_configuration()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{url}/functions/v1/employee-management",
                headers={
                    "apikey": anon_key,
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível conectar ao serviço de funcionários.",
        ) from error

    try:
        result = response.json()
    except ValueError as error:
        raise SupabaseApiError(
            502,
            "invalid_response",
            "O serviço de funcionários retornou uma resposta inválida.",
        ) from error
    if not isinstance(result, dict):
        raise SupabaseApiError(
            502,
            "invalid_response",
            "O serviço de funcionários retornou uma resposta incompatível.",
        )
    if not response.is_success:
        message = str(result.get("error", ""))
        code = str(result.get("code", ""))
        if response.status_code == 409 or "já está cadastrado" in message.lower():
            raise SupabaseApiError(409, code or "duplicate_email", message)
        raise SupabaseApiError(response.status_code, code, message)
    return result


async def create_employee(
    token: str,
    name: str,
    email: str,
    password: str,
    role: str,
) -> dict[str, Any]:
    normalized_role = normalize_role(role)
    if normalized_role is None:
        raise SupabaseApiError(400, "invalid_role", "O cargo informado é inválido.")
    result = await _employee_action(
        token,
        {
            "action": "create",
            "name": name,
            "email": email,
            "password": password,
            "role": normalized_role,
        },
    )
    employee = result.get("employee")
    if not isinstance(employee, dict) or not isinstance(employee.get("id"), str):
        raise SupabaseApiError(
            502,
            "invalid_response",
            "O Supabase não confirmou o cadastro do funcionário.",
        )
    return employee


async def list_employees(token: str) -> list[dict[str, Any]]:
    result = await _employee_action(token, {"action": "list"})
    employees = result.get("employees")
    if not isinstance(employees, list) or not all(
        isinstance(employee, dict) for employee in employees
    ):
        raise SupabaseApiError(
            502,
            "invalid_response",
            "O Supabase retornou uma lista de funcionários inválida.",
        )
    return employees


async def update_employee(
    token: str,
    employee_id: str,
    name: str,
    email: str,
    role: str,
    password: str = "",
) -> dict[str, Any]:
    normalized_role = normalize_role(role)
    if normalized_role is None:
        raise SupabaseApiError(400, "invalid_role", "O cargo informado é inválido.")
    payload: dict[str, Any] = {
        "action": "update",
        "userId": employee_id,
        "name": name,
        "email": email,
        "role": normalized_role,
    }
    if password:
        payload["password"] = password
    result = await _employee_action(token, payload)
    employee = result.get("employee")
    if not isinstance(employee, dict) or employee.get("id") != employee_id:
        raise SupabaseApiError(
            502,
            "invalid_response",
            "O Supabase não confirmou a atualização do funcionário.",
        )
    return employee


async def delete_employee(token: str, employee_id: str) -> None:
    result = await _employee_action(
        token,
        {"action": "delete", "userId": employee_id},
    )
    if result.get("deleted") is not True or result.get("userId") != employee_id:
        raise SupabaseApiError(
            502,
            "invalid_response",
            "O Supabase não confirmou a exclusão do funcionário.",
        )


def _product_from_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise SupabaseApiError(502, "invalid_response", "Produto inválido no Supabase.")
    try:
        return {
            "id": str(row["id"]),
            "tipo": str(row["product_type"]),
            "marca": str(row["brand"]),
            "peso": float(row["weight_grams"]),
            "codigo_de_barra": str(row["barcode"]),
        }
    except (KeyError, TypeError, ValueError) as error:
        raise SupabaseApiError(
            502,
            "invalid_response",
            "O Supabase retornou dados de produto incompletos.",
        ) from error


async def create_product(
    token: str,
    tipo: str,
    marca: str,
    peso: int | float,
    codigo_de_barra: str,
) -> dict[str, Any]:
    try:
        async with request_supabase_client(token) as client:
            auth_response = await client.auth.get_user(token)
            user = getattr(auth_response, "user", None)
            user_id = getattr(user, "id", None)
            if not isinstance(user_id, str) or not user_id:
                raise SupabaseApiError(401, "invalid_session", "Sessão inválida.")
            response = await (
                client.table("products")
                .insert(
                    {
                        "product_type": tipo.strip(),
                        "brand": marca.strip(),
                        "weight_grams": peso,
                        "barcode": codigo_de_barra.strip(),
                        "created_by": user_id,
                    }
                )
                .select("id, product_type, brand, weight_grams, barcode")
                .single()
                .execute()
            )
        product = _product_from_row(response.data)
        if (
            product["tipo"] != tipo.strip()
            or product["marca"] != marca.strip()
            or product["codigo_de_barra"] != codigo_de_barra.strip()
            or Decimal(str(product["peso"])) != Decimal(str(peso))
        ):
            raise SupabaseApiError(
                502,
                "invalid_response",
                "O Supabase retornou um produto diferente dos dados enviados.",
            )
        return product
    except SupabaseApiError:
        raise
    except (AuthApiError, APIError) as error:
        raise _translate_error(error) from error
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível conectar ao Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


async def list_products(token: str) -> list[dict[str, Any]]:
    try:
        async with request_supabase_client(token) as client:
            response = await (
                client.table("products")
                .select("id, product_type, brand, weight_grams, barcode")
                .eq("is_active", True)
                .order("product_type")
                .execute()
            )
        rows = response.data
        if not isinstance(rows, list):
            raise SupabaseApiError(
                502,
                "invalid_response",
                "O Supabase retornou uma lista de produtos inválida.",
            )
        return [_product_from_row(row) for row in rows]
    except SupabaseApiError:
        raise
    except (AuthApiError, APIError) as error:
        raise _translate_error(error) from error
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível consultar os produtos no Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


async def list_inventory(token: str) -> list[dict[str, Any]]:
    try:
        async with request_supabase_client(token) as client:
            response = await (
                client.table("stock_lots")
                .select("id, product_id, batch_label, units, expires_on")
                .order("expires_on")
                .execute()
            )
        rows = response.data
        if not isinstance(rows, list):
            raise SupabaseApiError(
                502,
                "invalid_response",
                "O Supabase retornou uma lista de estoque inválida.",
            )
        return [
            {
                "id": str(row["id"]),
                "produtos_id": str(row["product_id"]),
                "lote": str(row["batch_label"]),
                "unidades": int(row["units"]),
                "validade": str(row["expires_on"]),
            }
            for row in rows
        ]
    except SupabaseApiError:
        raise
    except (AuthApiError, APIError) as error:
        raise _translate_error(error) from error
    except (KeyError, TypeError, ValueError) as error:
        raise SupabaseApiError(
            502,
            "invalid_response",
            "O Supabase retornou dados de estoque inválidos.",
        ) from error
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível consultar o estoque no Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


async def create_inventory_lot(
    token: str,
    produtos_id: str,
    unidades: int,
    validade: str,
    lote: str,
) -> dict[str, Any]:
    try:
        async with request_supabase_client(token) as client:
            response = await client.rpc(
                "receive_stock",
                {
                    "p_product_id": produtos_id,
                    "p_batch_label": lote,
                    "p_units": unidades,
                    "p_expires_on": validade,
                },
            ).execute()
        row = response.data
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise SupabaseApiError(
                502,
                "invalid_response",
                "O Supabase não confirmou a atualização do estoque.",
            )
        return {
            "id": row["id"],
            "produtos_id": str(row["product_id"]),
            "lote": str(row["batch_label"]),
            "unidades": int(row["units"]),
            "validade": str(row["expires_on"]),
        }
    except SupabaseApiError:
        raise
    except (AuthApiError, APIError) as error:
        raise _translate_error(error) from error
    except (KeyError, TypeError, ValueError) as error:
        raise SupabaseApiError(
            502,
            "invalid_response",
            "O Supabase retornou dados de estoque inválidos.",
        ) from error
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível atualizar o estoque no Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


async def find_product_by_barcode(
    token: str,
    barcode: str,
) -> dict[str, Any] | None:
    try:
        async with request_supabase_client(token) as client:
            response = await (
                client.table("products")
                .select("id, product_type, brand, weight_grams, barcode")
                .eq("barcode", barcode.strip())
                .eq("is_active", True)
                .maybe_single()
                .execute()
            )
        return _product_from_row(response.data) if response.data is not None else None
    except SupabaseApiError:
        raise
    except (AuthApiError, APIError) as error:
        raise _translate_error(error) from error
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível consultar o produto no Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


async def create_product_price(
    token: str,
    product_id: str,
    price_cents: int,
) -> dict[str, Any]:
    try:
        async with request_supabase_client(token) as client:
            auth_response = await client.auth.get_user(token)
            user = getattr(auth_response, "user", None)
            user_id = getattr(user, "id", None)
            if not isinstance(user_id, str) or not user_id:
                raise SupabaseApiError(401, "invalid_session", "Sessão inválida.")
            response = await (
                client.table("product_price_history")
                .insert(
                    {
                        "product_id": product_id,
                        "price_cents": price_cents,
                        "created_by": user_id,
                    }
                )
                .select("id, product_id, price_cents, created_at")
                .single()
                .execute()
            )
        if not isinstance(response.data, dict):
            raise SupabaseApiError(
                502,
                "invalid_response",
                "O Supabase não confirmou o cadastro do preço.",
            )
        return response.data
    except SupabaseApiError:
        raise
    except (AuthApiError, APIError) as error:
        raise _translate_error(error) from error
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível registrar o preço no Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


async def list_current_prices(token: str) -> list[dict[str, Any]]:
    try:
        async with request_supabase_client(token) as client:
            response = await (
                client.table("current_product_prices")
                .select(
                    "product_id, product_name, barcode, product_type, brand, "
                    "weight_grams, price_cents, price_created_at"
                )
                .order("product_name")
                .execute()
            )
        rows = response.data
        if not isinstance(rows, list):
            raise SupabaseApiError(
                502,
                "invalid_response",
                "O Supabase retornou uma lista de preços inválida.",
            )
        return rows
    except SupabaseApiError:
        raise
    except (AuthApiError, APIError) as error:
        raise _translate_error(error) from error
    except httpx.RequestError as error:
        raise SupabaseApiError(
            0,
            "service_unavailable",
            "Não foi possível consultar os preços no Supabase.",
        ) from error
    except SupabaseConfigurationError as error:
        raise SupabaseApiError(500, "configuration_error", str(error)) from error


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


def validate_price_cents(value: str) -> int | None:
    try:
        price = Decimal(value.strip().replace(",", "."))
    except (InvalidOperation, AttributeError):
        return None
    if not price.is_finite() or price <= 0:
        return None
    cents = price * 100
    if cents != cents.to_integral_value():
        return None
    return int(cents)
