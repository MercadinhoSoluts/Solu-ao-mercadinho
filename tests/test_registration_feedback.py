import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bipsystem.auth_client import XanoApiError
from bipsystem.bipsystem import AuthState


def registration_state(previous_feedback: str) -> SimpleNamespace:
    state = SimpleNamespace(
        registration_feedback=previous_feedback,
        _auth_token="token",
        employees=[],
    )
    state._clear_session = lambda: AuthState._clear_session(state)
    state._error_message = lambda error, action: AuthState._error_message(error, action)
    state.require_admin = AsyncMock(
        side_effect=lambda: (
            None
            if state.registration_feedback == ""
            else AssertionError("Feedback was not cleared before authorization.")
        )
    )
    state.load_employees = lambda: AuthState.load_employees.fn(state)
    return state


class RegistrationFeedbackLoadTests(unittest.IsolatedAsyncioTestCase):
    async def test_page_load_clears_stale_feedback_before_loading_employee_list(self) -> None:
        state = registration_state("Funcionário excluído com sucesso.")

        with patch(
            "bipsystem.bipsystem.list_employees",
            new=AsyncMock(return_value=[{"id": 1, "name": "Ana"}]),
        ) as list_mock:
            await AuthState.require_admin_and_load_employees.fn(state)

        state.require_admin.assert_awaited_once()
        list_mock.assert_awaited_once_with("token")
        self.assertEqual(state.employees, [{"id": 1, "name": "Ana"}])
        self.assertEqual(state.registration_feedback, "")

    async def test_empty_employee_list_does_not_show_feedback(self) -> None:
        state = registration_state("Verifique os dados informados e tente novamente.")

        with patch(
            "bipsystem.bipsystem.list_employees",
            new=AsyncMock(return_value=[]),
        ):
            await AuthState.require_admin_and_load_employees.fn(state)

        self.assertEqual(state.employees, [])
        self.assertEqual(state.registration_feedback, "")

    async def test_real_list_failure_shows_query_error_after_clearing_old_feedback(self) -> None:
        state = registration_state("Funcionário excluído com sucesso.")

        with patch(
            "bipsystem.bipsystem.list_employees",
            new=AsyncMock(side_effect=XanoApiError(500)),
        ):
            await AuthState.require_admin_and_load_employees.fn(state)

        self.assertEqual(
            state.registration_feedback,
            "Não foi possível consultar os funcionários. Tente novamente.",
        )
