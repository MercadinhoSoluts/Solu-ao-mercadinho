import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from bipsystem.auth_client import SupabaseApiError
from bipsystem.bipsystem import AuthState, cashier_welcome_page_content


class CashierWelcomeAccessTests(unittest.IsolatedAsyncioTestCase):
    async def test_operator_is_allowed_on_welcome_page(self) -> None:
        state = SimpleNamespace(
            user_role="operator",
            cashier_navigation_started=True,
            require_auth=AsyncMock(return_value=None),
        )

        result = await AuthState.require_cashier_welcome.fn(state)

        self.assertIsNone(result)
        self.assertFalse(state.cashier_navigation_started)
        state.require_auth.assert_awaited_once()

    async def test_manager_is_redirected_to_existing_home_page(self) -> None:
        state = SimpleNamespace(
            user_role="manager",
            cashier_navigation_started=False,
            require_auth=AsyncMock(return_value=None),
            get_post_login_redirect=AuthState.get_post_login_redirect,
        )

        result = await AuthState.require_cashier_welcome.fn(state)

        self.assertEqual(result.args[0][1]._var_value, "/")

    async def test_unauthenticated_user_keeps_auth_redirect(self) -> None:
        auth_redirect = object()
        state = SimpleNamespace(
            user_role="",
            cashier_navigation_started=False,
            require_auth=AsyncMock(return_value=auth_redirect),
        )

        result = await AuthState.require_cashier_welcome.fn(state)

        self.assertIs(result, auth_redirect)

    async def test_purchase_action_redirects_operator_to_existing_cashier(self) -> None:
        state = SimpleNamespace(
            user_role="operator",
            cashier_navigation_started=False,
            cashier_open_request_id="opening-request",
            cashier_feedback="",
            _auth_token="access-token",
            require_auth=AsyncMock(return_value=None),
            _set_cashier_purchase=Mock(),
        )

        with patch(
            "bipsystem.bipsystem.open_cashier_purchase",
            new_callable=AsyncMock,
            return_value={"id": "purchase-id", "status": "open", "items": []},
        ) as open_purchase:
            result = await AuthState.start_cashier_sale.fn(state)

        self.assertEqual(result.args[0][1]._var_value, "/caixa")
        self.assertTrue(state.cashier_navigation_started)
        state.require_auth.assert_awaited_once()
        open_purchase.assert_awaited_once_with("access-token", "opening-request")
        state._set_cashier_purchase.assert_called_once()

    async def test_purchase_action_ignores_duplicate_activation(self) -> None:
        state = SimpleNamespace(
            user_role="operator",
            cashier_navigation_started=True,
            require_auth=AsyncMock(return_value=None),
        )

        result = await AuthState.start_cashier_sale.fn(state)

        self.assertIsNone(result)
        state.require_auth.assert_not_awaited()

    async def test_purchase_action_stays_on_welcome_when_supabase_rejects_rpc(self) -> None:
        state = SimpleNamespace(
            user_role="operator",
            cashier_navigation_started=False,
            cashier_open_request_id="opening-request",
            cashier_feedback="",
            _auth_token="access-token",
            require_auth=AsyncMock(return_value=None),
            _set_cashier_purchase=Mock(),
            _handle_cashier_error=Mock(
                side_effect=lambda error, action: setattr(
                    state, "cashier_feedback", error.message
                )
            ),
        )

        with patch(
            "bipsystem.bipsystem.open_cashier_purchase",
            new_callable=AsyncMock,
            side_effect=SupabaseApiError(
                503,
                "PGRST202",
                "A função de abertura não está disponível.",
            ),
        ) as open_purchase:
            result = await AuthState.start_cashier_sale.fn(state)

        self.assertIsNone(result)
        self.assertFalse(state.cashier_navigation_started)
        self.assertEqual(state.cashier_feedback, "A função de abertura não está disponível.")
        state._set_cashier_purchase.assert_not_called()
        open_purchase.assert_awaited_once_with("access-token", "opening-request")


class CashierWelcomeRenderingTests(unittest.TestCase):
    def test_welcome_content_uses_dynamic_portuguese_clock_and_autofocused_action(self) -> None:
        rendered = cashier_welcome_page_content().render()
        serialized = json.dumps(rendered)
        self.assertIn("Bem-vindo!", serialized)
        self.assertIn("Sistema de Automa", serialized)
        self.assertIn("Iniciar Compra", serialized)
        self.assertIn("BIPSYSTEM", serialized)
        self.assertIn("Segoe Script", serialized)
        self.assertIn("/logo_bipsystem_branca.png", serialized)
        self.assertNotIn("calculator", serialized)
        self.assertIn("Sair", serialized)
        self.assertIn("clamp(3rem, 3vw, 3.375rem)", serialized)
        self.assertIn("clamp(1.125rem, 1.1vw, 1.25rem)", serialized)
        self.assertIn("Caixa registradora", serialized)
        self.assertNotIn("clock-3", serialized)
        self.assertIn("cashier-welcome-brand", serialized)
        self.assertIn("cashier-welcome-register", serialized)
        self.assertIn("cashier-welcome-greeting", serialized)
        self.assertIn("70px", serialized)
        self.assertIn("-55px", serialized)
        self.assertIn("1.375rem", serialized)
        self.assertIn("1rem", serialized)

        nodes: list[tuple[str, str]] = []

        def collect(node: object) -> None:
            if isinstance(node, dict):
                nodes.append(
                    (
                        str(node.get("name", "")),
                        " ".join(str(prop) for prop in node.get("props", [])),
                    )
                )
                for child in node.get("children", []):
                    collect(child)
            elif isinstance(node, list):
                for child in node:
                    collect(child)

        collect(rendered)
        self.assertTrue(
            any(
                name == "RadixThemesFlex"
                and 'className:"rx-Stack cashier-welcome-header"' in props
                and 'direction:"row"' in props
                for name, props in nodes
            )
        )
        self.assertTrue(
            any(
                name == "Moment"
                and 'interval:60000' in props
                and 'locale:"pt-br"' in props
                for name, props in nodes
            )
        )
        self.assertTrue(
            any(
                name == "RadixThemesFlex"
                and 'className:"rx-Stack cashier-welcome-clock"' in props
                and 'align:"center"' in props
                for name, props in nodes
            )
        )
        self.assertTrue(
            any(
                name == "RadixThemesButton"
                and "autoFocus:true" in props
                and "start_cashier_sale" in props
                and '["minHeight"] : "6.8rem"' in props
                for name, props in nodes
            )
        )
        self.assertTrue(
            any(
                name == "RadixThemesBox"
                and 'className:"cashier-welcome-action-area"' in props
                for name, props in nodes
            )
        )
