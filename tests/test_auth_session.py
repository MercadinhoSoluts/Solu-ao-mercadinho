import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bipsystem.auth_client import AuthSession, AuthenticatedUser, SupabaseApiError
from bipsystem.bipsystem import AuthState


def session_state(**values: object) -> SimpleNamespace:
    defaults: dict[str, object] = {
        "authenticated": False,
        "user_name": "(nome)",
        "user_role": "",
        "login_feedback": "",
        "registration_feedback": "",
        "is_busy": False,
        "_auth_token": "",
        "_refresh_token": "",
        "_token_expires_at": 0.0,
    }
    defaults.update(values)
    state = SimpleNamespace(**defaults)
    state._clear_session = lambda: AuthState._clear_session(state)
    state._set_session = lambda session: AuthState._set_session(state, session)
    state._set_user = lambda user: AuthState._set_user(state, user)
    state.get_post_login_redirect = AuthState.get_post_login_redirect
    state._error_message = lambda error, action, authentication=False: (
        AuthState._error_message(error, action, authentication)
    )
    return state


class AuthStateSessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_login_stores_supabase_session_and_redirects_by_database_role(self) -> None:
        state = session_state()
        session = AuthSession("access-token", "refresh-token", 1_900_000_000)
        user = AuthenticatedUser(
            "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0",
            "Ana",
            "ana@example.com",
            "operator",
            True,
        )
        with (
            patch("bipsystem.bipsystem.login", new=AsyncMock(return_value=session)),
            patch(
                "bipsystem.bipsystem.get_current_user",
                new=AsyncMock(return_value=user),
            ),
        ):
            await AuthState.submit.fn(
                state,
                {"user": "ANA@example.com", "senha": "SenhaSegura123!"},
            )

        self.assertTrue(state.authenticated)
        self.assertEqual(state._auth_token, "access-token")
        self.assertEqual(state._refresh_token, "refresh-token")
        self.assertEqual(state.user_role, "operator")

    async def test_login_rejects_inactive_profile_and_revokes_received_session(self) -> None:
        state = session_state()
        session = AuthSession("access-token", "refresh-token", 1_900_000_000)
        inactive = AuthenticatedUser(
            "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0",
            "Ana",
            "ana@example.com",
            "operator",
            False,
        )
        with (
            patch("bipsystem.bipsystem.login", new=AsyncMock(return_value=session)),
            patch(
                "bipsystem.bipsystem.get_current_user",
                new=AsyncMock(return_value=inactive),
            ),
            patch("bipsystem.bipsystem.logout", new=AsyncMock()) as logout_mock,
        ):
            await AuthState.submit.fn(
                state,
                {"user": "ana@example.com", "senha": "SenhaSegura123!"},
            )

        logout_mock.assert_awaited_once_with("access-token")
        self.assertFalse(state.authenticated)
        self.assertFalse(state._auth_token)
        self.assertEqual(state.login_feedback, "Este usuário está inativo.")

    async def test_require_auth_refreshes_expiring_session_and_reloads_profile(self) -> None:
        state = session_state(
            _auth_token="expired-access",
            _refresh_token="refresh",
            _token_expires_at=1.0,
        )
        refreshed = AuthSession("new-access", "new-refresh", 1_900_000_000)
        user = AuthenticatedUser(
            "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0",
            "Ana",
            "ana@example.com",
            "owner",
            True,
        )
        with (
            patch(
                "bipsystem.bipsystem.refresh_session",
                new=AsyncMock(return_value=refreshed),
            ) as refresh_mock,
            patch(
                "bipsystem.bipsystem.get_current_user",
                new=AsyncMock(return_value=user),
            ) as user_mock,
        ):
            result = await AuthState.require_auth.fn(state)

        self.assertIsNone(result)
        refresh_mock.assert_awaited_once_with("refresh")
        user_mock.assert_awaited_once_with("new-access")
        self.assertEqual(state._auth_token, "new-access")
        self.assertEqual(state._refresh_token, "new-refresh")
        self.assertEqual(state.user_role, "owner")

    async def test_expired_invalid_session_redirects_without_granting_access(self) -> None:
        state = session_state(
            _auth_token="expired-access",
            _refresh_token="refresh",
            _token_expires_at=1.0,
        )
        with patch(
            "bipsystem.bipsystem.refresh_session",
            new=AsyncMock(side_effect=SupabaseApiError(401)),
        ):
            result = await AuthState.require_auth.fn(state)

        self.assertIsNotNone(result)
        self.assertFalse(state.authenticated)
        self.assertFalse(state._auth_token)
        self.assertEqual(state.login_feedback, "Sua sessão expirou. Entre novamente.")
