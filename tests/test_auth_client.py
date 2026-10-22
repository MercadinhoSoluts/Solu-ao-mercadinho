import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from bipsystem.auth_client import (
    AuthSession,
    SupabaseApiError,
    _employee_action,
    get_current_user,
    login,
    normalize_role,
    parse_inventory_date,
    parse_inventory_units,
    validate_password,
    validate_price_cents,
)
from bipsystem.bipsystem import AuthState


class RoleAndValidationTests(unittest.TestCase):
    def test_maps_business_roles_to_existing_enum_values(self) -> None:
        self.assertEqual(normalize_role("proprietario"), "owner")
        self.assertEqual(normalize_role("Admin"), "manager")
        self.assertEqual(normalize_role("caixa"), "operator")
        self.assertEqual(normalize_role("owner"), "owner")
        self.assertEqual(normalize_role("manager"), "manager")
        self.assertEqual(normalize_role("operator"), "operator")
        self.assertIsNone(normalize_role("unknown"))

    def test_validates_password_policy(self) -> None:
        self.assertIsNone(validate_password("SenhaSegura123!"))
        self.assertEqual(
            validate_password("SenhaSegura123"),
            "A senha deve conter um caractere especial.",
        )

    def test_parses_positive_inventory_units_and_iso_dates(self) -> None:
        self.assertEqual(parse_inventory_units("12"), 12)
        self.assertIsNone(parse_inventory_units("0"))
        self.assertEqual(parse_inventory_date("2027-01-02"), "2027-01-02")
        self.assertIsNone(parse_inventory_date("02/01/2027"))

    def test_converts_prices_to_exact_integer_cents(self) -> None:
        self.assertEqual(validate_price_cents("25,90"), 2590)
        self.assertEqual(validate_price_cents("0.01"), 1)
        self.assertIsNone(validate_price_cents("0"))
        self.assertIsNone(validate_price_cents("1.999"))
        self.assertIsNone(validate_price_cents("NaN"))

    def test_post_login_redirect_uses_business_role_mapping(self) -> None:
        self.assertEqual(AuthState.get_post_login_redirect("caixa"), "/caixa")
        self.assertEqual(AuthState.get_post_login_redirect("operator"), "/caixa")
        self.assertEqual(AuthState.get_post_login_redirect("proprietario"), "/")
        self.assertEqual(AuthState.get_post_login_redirect("admin"), "/")
        self.assertIsNone(AuthState.get_post_login_redirect("unknown"))

    def test_auth_error_messages_distinguish_connection_and_permissions(self) -> None:
        self.assertEqual(
            AuthState._error_message(
                SupabaseApiError(0),
                "realizar o login",
                authentication=True,
            ),
            "Não foi possível conectar ao Supabase.",
        )
        self.assertEqual(
            AuthState._error_message(
                SupabaseApiError(403),
                "cadastrar o funcionário",
            ),
            "Você não tem autorização para realizar esta ação.",
        )


class SupabaseAuthenticationTests(unittest.IsolatedAsyncioTestCase):
    async def test_login_normalizes_email_and_returns_access_and_refresh_tokens(self) -> None:
        session = SimpleNamespace(
            access_token="access",
            refresh_token="refresh",
            expires_at=1_800_000_000,
        )
        client = SimpleNamespace(
            auth=SimpleNamespace(
                sign_in_with_password=AsyncMock(
                    return_value=SimpleNamespace(session=session)
                )
            )
        )

        @asynccontextmanager
        async def fake_client():
            yield client

        with patch(
            "bipsystem.auth_client.request_supabase_client",
            side_effect=fake_client,
        ):
            result = await login(" User@Example.com ", "Password123!")

        self.assertEqual(
            result,
            AuthSession("access", "refresh", 1_800_000_000),
        )
        client.auth.sign_in_with_password.assert_awaited_once_with(
            {"email": "user@example.com", "password": "Password123!"}
        )

    async def test_current_user_requires_a_matching_supported_profile(self) -> None:
        user_id = "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0"
        profile = {
            "id": user_id,
            "name": "Ana",
            "email": "ana@example.com",
            "role": "manager",
            "is_active": True,
        }
        query = MagicMock()
        query.select.return_value.eq.return_value.maybe_single.return_value.execute = (
            AsyncMock(return_value=SimpleNamespace(data=profile))
        )
        client = SimpleNamespace(
            auth=SimpleNamespace(
                get_user=AsyncMock(
                    return_value=SimpleNamespace(
                        user=SimpleNamespace(id=user_id)
                    )
                )
            ),
            table=MagicMock(return_value=query),
        )

        @asynccontextmanager
        async def fake_client(token):
            self.assertEqual(token, "access")
            yield client

        with patch(
            "bipsystem.auth_client.request_supabase_client",
            side_effect=fake_client,
        ):
            current_user = await get_current_user("access")

        self.assertEqual(current_user.user_id, user_id)
        self.assertEqual(current_user.role, "manager")
        self.assertTrue(current_user.is_active)

    async def test_missing_profile_fails_closed(self) -> None:
        user_id = "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0"
        query = MagicMock()
        query.select.return_value.eq.return_value.maybe_single.return_value.execute = (
            AsyncMock(return_value=SimpleNamespace(data=None))
        )
        client = SimpleNamespace(
            auth=SimpleNamespace(
                get_user=AsyncMock(
                    return_value=SimpleNamespace(
                        user=SimpleNamespace(id=user_id)
                    )
                )
            ),
            table=MagicMock(return_value=query),
        )

        @asynccontextmanager
        async def fake_client(token):
            yield client

        with patch(
            "bipsystem.auth_client.request_supabase_client",
            side_effect=fake_client,
        ):
            with self.assertRaises(SupabaseApiError) as context:
                await get_current_user("access")

        self.assertEqual(context.exception.code, "profile_missing")
        self.assertEqual(context.exception.status_code, 403)


class EmployeeFunctionTests(unittest.IsolatedAsyncioTestCase):
    async def test_employee_action_uses_edge_function_with_user_token(self) -> None:
        response = httpx.Response(
            200,
            json={"employees": [{"id": "user-id", "role": "operator"}]},
        )
        client = AsyncMock()
        client.post.return_value = response
        with (
            patch(
                "bipsystem.auth_client._supabase_configuration",
                return_value=("https://example.supabase.co", "public-key"),
            ),
            patch("bipsystem.auth_client.httpx.AsyncClient") as client_factory,
        ):
            client_factory.return_value.__aenter__.return_value = client
            result = await _employee_action("user-access", {"action": "list"})

        self.assertEqual(result["employees"][0]["id"], "user-id")
        client.post.assert_awaited_once_with(
            "https://example.supabase.co/functions/v1/employee-management",
            headers={
                "apikey": "public-key",
                "Authorization": "Bearer user-access",
                "Content-Type": "application/json",
            },
            json={"action": "list"},
        )

    async def test_employee_action_preserves_duplicate_email_conflict(self) -> None:
        response = httpx.Response(
            409,
            json={"error": "Este e-mail já está cadastrado."},
        )
        client = AsyncMock()
        client.post.return_value = response
        with (
            patch(
                "bipsystem.auth_client._supabase_configuration",
                return_value=("https://example.supabase.co", "public-key"),
            ),
            patch("bipsystem.auth_client.httpx.AsyncClient") as client_factory,
        ):
            client_factory.return_value.__aenter__.return_value = client
            with self.assertRaises(SupabaseApiError) as context:
                await _employee_action(
                    "user-access",
                    {"action": "create", "email": "ana@example.com"},
                )

        self.assertEqual(context.exception.status_code, 409)
