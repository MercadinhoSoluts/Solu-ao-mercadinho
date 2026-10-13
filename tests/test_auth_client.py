import unittest

from bipsystem.auth_client import XanoApiError, normalize_role, validate_password
from bipsystem.bipsystem import AuthState


class AuthClientValidationTests(unittest.TestCase):
    def test_normalizes_supported_role_labels(self) -> None:
        self.assertEqual(normalize_role("Proprietário"), "owner")
        self.assertEqual(normalize_role("Operador"), "operator")
        self.assertEqual(normalize_role("Admin"), "manager")
        self.assertEqual(normalize_role("manager"), "manager")
        self.assertIsNone(normalize_role("admin"))

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
