import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bipsystem.auth_client import XanoApiError
from bipsystem.bipsystem import AuthState


def deletion_state(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "employee_delete_busy": False,
        "employee_delete_open": True,
        "employee_delete_id": 2,
        "employee_delete_name": "Ana",
        "user_role": "owner",
        "_auth_token": "token",
        "employees": [
            {"id": 1, "name": "Bruno"},
            {"id": 2, "name": "Ana"},
            {"id": 3, "name": "Caio"},
        ],
        "registration_feedback": "",
    }
    values.update(overrides)
    state = SimpleNamespace(**values)
    state.close_employee_delete = lambda: AuthState.close_employee_delete.fn(state)
    state._error_message = lambda error, action: AuthState._error_message(error, action)
    return state


class EmployeeDeleteStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirm_deletes_only_selected_employee_after_success(self) -> None:
        state = deletion_state()

        with patch(
            "bipsystem.bipsystem.delete_employee",
            new=AsyncMock(),
        ) as delete_mock:
            await AuthState.confirm_employee_delete.fn(state)

        delete_mock.assert_awaited_once_with("token", 2)
        self.assertEqual([employee["id"] for employee in state.employees], [1, 3])
        self.assertEqual(
            state.registration_feedback,
            "Funcionário excluído com sucesso.",
        )
        self.assertFalse(state.employee_delete_open)
        self.assertFalse(state.employee_delete_busy)

    async def test_failed_delete_keeps_employee_and_reports_error(self) -> None:
        state = deletion_state(employees=[{"id": 2, "name": "Ana"}])

        with patch(
            "bipsystem.bipsystem.delete_employee",
            new=AsyncMock(side_effect=XanoApiError(500)),
        ) as delete_mock:
            await AuthState.confirm_employee_delete.fn(state)

        delete_mock.assert_awaited_once_with("token", 2)
        self.assertEqual(state.employees, [{"id": 2, "name": "Ana"}])
        self.assertEqual(
            state.registration_feedback,
            "Não foi possível excluir o funcionário. Tente novamente.",
        )
        self.assertFalse(state.employee_delete_open)
        self.assertFalse(state.employee_delete_busy)

    async def test_cancel_closes_confirmation_without_deleting(self) -> None:
        state = deletion_state()

        with patch("bipsystem.bipsystem.delete_employee", new=AsyncMock()) as delete_mock:
            AuthState.close_employee_delete.fn(state)

        delete_mock.assert_not_awaited()
        self.assertEqual(state.employee_delete_id, 0)
        self.assertEqual(state.employee_delete_name, "")
        self.assertFalse(state.employee_delete_open)

    async def test_busy_state_blocks_duplicate_delete_requests(self) -> None:
        state = deletion_state(employee_delete_busy=True)

        with patch("bipsystem.bipsystem.delete_employee", new=AsyncMock()) as delete_mock:
            await AuthState.confirm_employee_delete.fn(state)

        delete_mock.assert_not_awaited()
        self.assertEqual([employee["id"] for employee in state.employees], [1, 2, 3])
