import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bipsystem.auth_client import SupabaseApiError
from bipsystem.bipsystem import AuthState


def deletion_state(**overrides: object) -> SimpleNamespace:
    employee_one = "2d8973c0-2c38-4db5-95c8-a3cf8df4621f"
    employee_two = "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0"
    employee_three = "dfcc9c1a-1ff0-4351-ae6b-b28aeedc246b"
    values: dict[str, object] = {
        "employee_delete_busy": False,
        "employee_delete_open": True,
        "employee_delete_id": employee_two,
        "employee_delete_name": "Ana",
        "user_role": "owner",
        "_auth_token": "token",
        "employees": [
            {"id": employee_one, "name": "Bruno"},
            {"id": employee_two, "name": "Ana"},
            {"id": employee_three, "name": "Caio"},
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

        delete_mock.assert_awaited_once_with(
            "token",
            "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0",
        )
        self.assertEqual(
            [employee["id"] for employee in state.employees],
            [
                "2d8973c0-2c38-4db5-95c8-a3cf8df4621f",
                "dfcc9c1a-1ff0-4351-ae6b-b28aeedc246b",
            ],
        )
        self.assertEqual(
            state.registration_feedback,
            "Funcionário excluído com sucesso.",
        )
        self.assertFalse(state.employee_delete_open)
        self.assertFalse(state.employee_delete_busy)

    async def test_failed_delete_keeps_employee_and_reports_error(self) -> None:
        state = deletion_state(
            employees=[
                {
                    "id": "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0",
                    "name": "Ana",
                }
            ]
        )

        with patch(
            "bipsystem.bipsystem.delete_employee",
            new=AsyncMock(side_effect=SupabaseApiError(500)),
        ) as delete_mock:
            await AuthState.confirm_employee_delete.fn(state)

        delete_mock.assert_awaited_once_with(
            "token",
            "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0",
        )
        self.assertEqual(
            state.employees,
            [
                {
                    "id": "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0",
                    "name": "Ana",
                }
            ],
        )
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
        self.assertEqual(state.employee_delete_id, "")
        self.assertEqual(state.employee_delete_name, "")
        self.assertFalse(state.employee_delete_open)

    async def test_busy_state_blocks_duplicate_delete_requests(self) -> None:
        state = deletion_state(employee_delete_busy=True)

        with patch("bipsystem.bipsystem.delete_employee", new=AsyncMock()) as delete_mock:
            await AuthState.confirm_employee_delete.fn(state)

        delete_mock.assert_not_awaited()
        self.assertEqual(
            [employee["id"] for employee in state.employees],
            [
                "2d8973c0-2c38-4db5-95c8-a3cf8df4621f",
                "d1e35c87-9f35-4b23-9e36-a6b2f7f45ef0",
                "dfcc9c1a-1ff0-4351-ae6b-b28aeedc246b",
            ],
        )
