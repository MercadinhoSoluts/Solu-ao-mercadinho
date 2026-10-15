import unittest
from unittest.mock import AsyncMock, patch

import httpx
from bipsystem.auth_client import (
    XanoApiError,
    delete_employee,
    list_employees,
    normalize_role,
    update_employee,
    validate_password,
)
from bipsystem.bipsystem import AuthState


class AuthClientValidationTests(unittest.TestCase):
    def test_normalizes_supported_role_labels(self) -> None:
        self.assertEqual(normalize_role("Proprietário"), "owner")
        self.assertEqual(normalize_role("Operador"), "operator")
        self.assertEqual(normalize_role("Admin"), "manager")
        self.assertEqual(normalize_role("manager"), "manager")
        self.assertEqual(normalize_role("admin"), "manager")
        self.assertEqual(normalize_role("Administrador"), "manager")
        self.assertEqual(normalize_role("proprietario"), "owner")

    def test_accepts_password_with_all_required_classes(self) -> None:
        self.assertIsNone(validate_password("SenhaSegura123!"))

    def test_rejects_password_without_special_character(self) -> None:
        self.assertEqual(
            validate_password("SenhaSegura123"),
            "A senha deve conter um caractere especial.",
        )

    def test_login_authentication_failure_is_not_reported_as_authorization(self) -> None:
        message = AuthState._error_message(
            XanoApiError(403, code="ERROR_CODE_ACCESS_DENIED"),
            "realizar o login",
            authentication=True,
        )
        self.assertEqual(
            message,
            "Senha incorreta. Verifique sua senha e tente novamente.",
        )

    def test_protected_action_failure_remains_authorization_error(self) -> None:
        message = AuthState._error_message(
            XanoApiError(403, code="ERROR_CODE_ACCESS_DENIED"),
            "cadastrar o funcionário",
        )
        self.assertEqual(
            message,
            "Você não tem autorização para realizar esta ação.",
        )

    def test_login_connection_failure_is_not_reported_as_authentication_failure(self) -> None:
        message = AuthState._error_message(
            XanoApiError(0),
            "realizar o login",
            authentication=True,
        )
        self.assertEqual(message, "Não foi possível conectar ao Xano.")

    def test_post_login_redirect_uses_operator_route_only_for_operator_role(self) -> None:
        self.assertEqual(AuthState.get_post_login_redirect("operator"), "/caixa")
        self.assertEqual(AuthState.get_post_login_redirect("owner"), "/")
        self.assertEqual(AuthState.get_post_login_redirect("manager"), "/")
        self.assertIsNone(AuthState.get_post_login_redirect("unknown"))
        self.assertIsNone(AuthState.get_post_login_redirect(None))


class EmployeeApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_employees_returns_public_fields(self) -> None:
        client = AsyncMock()
        client.get.return_value = httpx.Response(
            200,
            json=[{"id": 2, "name": "Ana", "email": "ana@example.com", "role": "operator"}],
        )

        with patch("bipsystem.auth_client.httpx.AsyncClient") as client_factory:
            client_factory.return_value.__aenter__.return_value = client
            result = await list_employees("token")

        self.assertEqual(result[0]["id"], 2)
        client.get.assert_awaited_once_with(
            "https://x8ki-letl-twmt.n7.xano.io/api:_832jVAW/users",
            headers={"Authorization": "Bearer token"},
        )

    async def test_update_employee_omits_empty_password(self) -> None:
        client = AsyncMock()
        client.patch.return_value = httpx.Response(
            200,
            json={"id": 2, "name": "Ana Silva", "email": "ana@example.com", "role": "manager"},
        )

        with patch("bipsystem.auth_client.httpx.AsyncClient") as client_factory:
            client_factory.return_value.__aenter__.return_value = client
            await update_employee("token", 2, "Ana Silva", "ana@example.com", "manager")

        client.patch.assert_awaited_once_with(
            "https://x8ki-letl-twmt.n7.xano.io/api:_832jVAW/users/2",
            headers={"Authorization": "Bearer token"},
            json={"name": "Ana Silva", "email": "ana@example.com", "role": "manager"},
        )

    async def test_delete_employee_uses_delete_endpoint(self) -> None:
        client = AsyncMock()
        client.delete.return_value = httpx.Response(200, json=None)

        with patch("bipsystem.auth_client.httpx.AsyncClient") as client_factory:
            client_factory.return_value.__aenter__.return_value = client
            await delete_employee("token", 2)

        client.delete.assert_awaited_once_with(
            "https://x8ki-letl-twmt.n7.xano.io/api:_832jVAW/users/2",
            headers={"Authorization": "Bearer token"},
        )
