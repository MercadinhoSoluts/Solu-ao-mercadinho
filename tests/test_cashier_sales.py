import json
import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from postgrest.exceptions import APIError

from bipsystem import bipsystem
from bipsystem.auth_client import (
    SupabaseApiError,
    _purchase_from_rpc,
    _translate_error,
    get_available_stock,
)
from bipsystem.auth_client import open_cashier_purchase
from bipsystem.bipsystem import (
    AuthState,
    cashier_page_content,
    format_currency_cents,
)


PURCHASE_ID = "fd736e5a-ef04-4f12-b49a-8ed6763f16cb"
ITEM_ID = "af538e50-b670-4965-a4ef-522685a0fcb5"
PURCHASE_RESPONSE = {
    "id": PURCHASE_ID,
    "status": "open",
    "total_cents": 1000,
    "payment_method": None,
    "items": [
        {
            "id": ITEM_ID,
            "product_name": "Arroz Tipo 1 500 g",
            "barcode": "0001234567890",
            "quantity": 2,
            "unit_price_cents": 500,
            "line_total_cents": 1000,
        }
    ],
}
PRODUCT_ID = "af538e50-b670-4965-a4ef-522685a0fcb5"


def cashier_add_state(items: list[dict[str, str]] | None = None) -> SimpleNamespace:
    state = SimpleNamespace(
        cashier_barcode="",
        cashier_quantity="1",
        cashier_purchase_id=PURCHASE_ID,
        cashier_purchase_status="open",
        cashier_pending_request_id="",
        cashier_pending_barcode="",
        cashier_pending_quantity=0,
        cashier_busy=False,
        cashier_feedback="",
        cashier_items=items or [],
        _auth_token="access-token",
    )
    state._set_cashier_purchase = lambda purchase: setattr(
        state, "last_purchase", purchase
    )
    state._handle_cashier_error = lambda error, action: setattr(
        state, "cashier_feedback", error.message
    )
    return state


class CashierPurchaseParsingTests(unittest.TestCase):
    def test_currency_formats_integer_cents_without_float_rounding(self) -> None:
        self.assertEqual(format_currency_cents(0), "0,00 R$")
        self.assertEqual(format_currency_cents(500), "5,00 R$")
        self.assertEqual(format_currency_cents(123456789), "1234567,89 R$")

    def test_purchase_parser_preserves_item_price_and_barcode_snapshot(self) -> None:
        purchase = _purchase_from_rpc(PURCHASE_RESPONSE)

        self.assertIsNone(purchase["payment_method"])
        self.assertEqual(purchase["items"][0]["barcode"], "0001234567890")
        self.assertEqual(purchase["items"][0]["unit_price_cents"], 500)
        self.assertEqual(purchase["items"][0]["line_total_cents"], 1000)
        self.assertEqual(purchase["total_cents"], 1000)

    def test_purchase_parser_rejects_inconsistent_line_or_purchase_totals(self) -> None:
        invalid = {
            **PURCHASE_RESPONSE,
            "items": [
                {
                    **PURCHASE_RESPONSE["items"][0],
                    "line_total_cents": 999,
                }
            ],
        }

        with self.assertRaisesRegex(SupabaseApiError, "incompletos ou inconsistentes"):
            _purchase_from_rpc(invalid)

    def test_purchase_parser_validates_payment_method(self) -> None:
        purchase = _purchase_from_rpc(
            {**PURCHASE_RESPONSE, "payment_method": "pix"}
        )
        self.assertEqual(purchase["payment_method"], "pix")

        with self.assertRaisesRegex(SupabaseApiError, "incompletos ou inconsistentes"):
            _purchase_from_rpc(
                {**PURCHASE_RESPONSE, "payment_method": "unknown"}
            )

    def test_known_rpc_errors_are_translated_to_safe_cashier_messages(self) -> None:
        error = _translate_error(SimpleNamespace(code="P1002", status=500))

        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.message, "Este produto não possui um preço vigente.")

    def test_schema_cache_errors_report_schema_availability(self) -> None:
        error = _translate_error(
            APIError(
                {
                    "code": "PGRST202",
                    "message": "Could not find the function in the schema cache",
                    "details": None,
                    "hint": None,
                }
            )
        )

        self.assertEqual(error.status_code, 503)
        self.assertEqual(error.code, "PGRST202")
        self.assertIn("migration", error.message)

    def test_auth_and_rls_errors_keep_distinct_statuses(self) -> None:
        expired = _translate_error(SimpleNamespace(code="PGRST301"))
        denied = _translate_error(SimpleNamespace(code="42501"))
        insufficient_stock = _translate_error(
            SimpleNamespace(code="P1010", status=500)
        )
        repeated_with_other_method = _translate_error(
            SimpleNamespace(code="P1011", status=500)
        )

        self.assertEqual(expired.status_code, 401)
        self.assertEqual(expired.message, "Sua sessão expirou ou não é mais válida. Entre novamente.")
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(denied.message, "Você não tem autorização para realizar esta ação.")
        self.assertEqual(insufficient_stock.status_code, 409)
        self.assertIn("Estoque insuficiente", insufficient_stock.message)
        self.assertEqual(repeated_with_other_method.status_code, 409)


class CashierPurchaseStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_stock_query_filters_lots_by_business_date(self) -> None:
        query_calls = []

        class StockQuery:
            def select(self, columns: str):
                query_calls.append(("select", columns))
                return self

            def eq(self, column: str, value: str):
                query_calls.append(("eq", column, value))
                return self

            def gte(self, column: str, value: str):
                query_calls.append(("gte", column, value))
                return self

            async def execute(self):
                return SimpleNamespace(data=[{"units": 3}, {"units": 5}])

        class StockClient:
            def table(self, name: str):
                query_calls.append(("table", name))
                return StockQuery()

        @asynccontextmanager
        async def fake_client(token: str, response_observer=None):
            yield StockClient()

        with patch(
            "bipsystem.auth_client.request_supabase_client",
            side_effect=fake_client,
        ):
            available = await get_available_stock(
                "access-token",
                PRODUCT_ID,
                "2026-10-23",
            )

        self.assertEqual(available, 8)
        self.assertIn(("gte", "expires_on", "2026-10-23"), query_calls)
        self.assertIn(("eq", "product_id", PRODUCT_ID), query_calls)

    async def test_add_cashier_item_accepts_quantities_below_and_at_stock(self) -> None:
        for quantity in (129, 130):
            with self.subTest(quantity=quantity):
                state = cashier_add_state()
                add_item = AsyncMock(return_value=PURCHASE_RESPONSE)
                with (
                    patch(
                        "bipsystem.bipsystem.find_product_by_barcode",
                        AsyncMock(return_value={"id": PRODUCT_ID}),
                    ),
                    patch(
                        "bipsystem.bipsystem.get_available_stock",
                        AsyncMock(return_value=130),
                    ),
                    patch(
                        "bipsystem.bipsystem.add_cashier_purchase_item",
                        add_item,
                    ),
                ):
                    await AuthState.add_cashier_item.fn(
                        state,
                        {"barcode": "0001234567890", "quantity": str(quantity)},
                    )

                add_item.assert_awaited_once()
                self.assertEqual(state.cashier_feedback, "Item incluído na compra.")

    async def test_add_cashier_item_rejects_quantity_above_stock_and_preserves_cart(
        self,
    ) -> None:
        state = cashier_add_state()
        add_item = AsyncMock()

        with (
            patch(
                "bipsystem.bipsystem.find_product_by_barcode",
                AsyncMock(return_value={"id": PRODUCT_ID}),
            ),
            patch(
                "bipsystem.bipsystem.get_available_stock",
                AsyncMock(return_value=130),
            ),
            patch("bipsystem.bipsystem.add_cashier_purchase_item", add_item),
        ):
            await AuthState.add_cashier_item.fn(
                state,
                {"barcode": "0001234567890", "quantity": "131"},
            )

        add_item.assert_not_awaited()
        self.assertEqual(state.cashier_items, [])
        self.assertEqual(
            state.cashier_feedback,
            "Estoque insuficiente. Disponível: 130 unidades. "
            "Quantidade solicitada: 131.",
        )

    async def test_add_cashier_item_includes_existing_quantity_in_stock_limit(self) -> None:
        existing_item = {
            "product_name": "Arroz Tipo 1 500 g",
            "quantity": "2",
            "barcode": "0001234567890",
        }
        state = cashier_add_state([existing_item])
        add_item = AsyncMock(return_value=PURCHASE_RESPONSE)

        with (
            patch(
                "bipsystem.bipsystem.find_product_by_barcode",
                AsyncMock(return_value={"id": PRODUCT_ID}),
            ),
            patch(
                "bipsystem.bipsystem.get_available_stock",
                AsyncMock(return_value=3),
            ),
            patch("bipsystem.bipsystem.add_cashier_purchase_item", add_item),
        ):
            await AuthState.add_cashier_item.fn(
                state,
                {"barcode": "0001234567890", "quantity": "2"},
            )

        add_item.assert_not_awaited()
        self.assertEqual(state.cashier_items, [existing_item])
        self.assertIn("Quantidade solicitada total: 4", state.cashier_feedback)

    async def test_add_cashier_item_allows_total_equal_to_stock(self) -> None:
        state = cashier_add_state(
            [
                {
                    "product_name": "Arroz Tipo 1 500 g",
                    "quantity": "2",
                    "barcode": "0001234567890",
                }
            ]
        )
        add_item = AsyncMock(return_value=PURCHASE_RESPONSE)

        with (
            patch(
                "bipsystem.bipsystem.find_product_by_barcode",
                AsyncMock(return_value={"id": PRODUCT_ID}),
            ),
            patch(
                "bipsystem.bipsystem.get_available_stock",
                AsyncMock(return_value=3),
            ),
            patch("bipsystem.bipsystem.add_cashier_purchase_item", add_item),
        ):
            await AuthState.add_cashier_item.fn(
                state,
                {"barcode": "0001234567890", "quantity": "1"},
            )

        add_item.assert_awaited_once()

    async def test_rpc_failure_logs_http_code_and_schema_error_without_token(self) -> None:
        api_error = APIError(
            {
                "code": "PGRST202",
                "message": "Could not find the function in the schema cache",
                "details": "Function public.open_cashier_purchase was not found",
                "hint": "Check function argument names",
            }
        )
        rpc = SimpleNamespace(execute=AsyncMock(side_effect=api_error))

        @asynccontextmanager
        async def fake_client(token: str, response_observer=None):
            response_observer(httpx.Response(404))
            yield SimpleNamespace(rpc=lambda function, parameters: rpc)

        with (
            patch(
                "bipsystem.auth_client.request_supabase_client",
                side_effect=fake_client,
            ),
            self.assertLogs("bipsystem.auth_client", level="ERROR") as logs,
        ):
            with self.assertRaises(SupabaseApiError) as raised:
                await open_cashier_purchase(
                    "sensitive-access-token",
                    "fd736e5a-ef04-4f12-b49a-8ed6763f16cb",
                )

        self.assertEqual(raised.exception.code, "PGRST202")
        self.assertEqual(raised.exception.status_code, 503)
        log_output = "\n".join(logs.output)
        self.assertIn("http_status=404", log_output)
        self.assertIn("PGRST202", log_output)
        self.assertIn("schema cache", log_output)
        self.assertNotIn("sensitive-access-token", log_output)

    async def test_payment_completion_sends_selected_method_to_rpc(self) -> None:
        rpc = SimpleNamespace(
            execute=AsyncMock(
                side_effect=lambda: SimpleNamespace(
                    data={
                        **PURCHASE_RESPONSE,
                        "status": "completed",
                        "payment_method": current_method[0],
                    }
                )
            )
        )
        current_method = [""]
        rpc_calls = []

        @asynccontextmanager
        async def fake_client(token: str, response_observer=None):
            def call_rpc(function: str, parameters: dict[str, str]):
                rpc_calls.append((function, parameters.copy()))
                return rpc

            yield SimpleNamespace(rpc=call_rpc)

        with patch(
            "bipsystem.auth_client.request_supabase_client",
            side_effect=fake_client,
        ):
            for method in ("credit_card", "debit_card", "pix", "cash"):
                current_method[0] = method
                result = await bipsystem.complete_cashier_purchase(
                    "access-token",
                    PURCHASE_ID,
                    method,
                )
                self.assertEqual(result["payment_method"], method)

        self.assertEqual(rpc.execute.await_count, 4)
        self.assertEqual(
            rpc_calls,
            [
                (
                    "complete_cashier_purchase",
                    {
                        "p_purchase_id": PURCHASE_ID,
                        "p_payment_method": method,
                    },
                )
                for method in ("credit_card", "debit_card", "pix", "cash")
            ],
        )

    async def test_payment_completion_rejects_unknown_method_without_rpc(self) -> None:
        with self.assertRaisesRegex(SupabaseApiError, "válido"):
            await bipsystem.complete_cashier_purchase(
                "access-token",
                PURCHASE_ID,
                "unknown",
            )

    async def test_item_retry_reuses_request_id_and_keeps_leading_zeroes(self) -> None:
        state = SimpleNamespace(
            cashier_barcode="",
            cashier_quantity="1",
            cashier_purchase_id=PURCHASE_ID,
            cashier_purchase_status="open",
            cashier_pending_request_id="",
            cashier_pending_barcode="",
            cashier_pending_quantity=0,
            cashier_busy=False,
            cashier_feedback="",
            cashier_items=[],
            _auth_token="access-token",
        )
        state._set_cashier_purchase = lambda purchase: setattr(
            state, "last_purchase", purchase
        )
        state._handle_cashier_error = lambda error, action: setattr(
            state, "cashier_feedback", error.message
        )
        add_item = AsyncMock(
            side_effect=[
                SupabaseApiError(0, "service_unavailable", "Conexão indisponível."),
                PURCHASE_RESPONSE,
            ]
        )

        with (
            patch(
                "bipsystem.bipsystem.find_product_by_barcode",
                AsyncMock(return_value={"id": PRODUCT_ID}),
            ),
            patch(
                "bipsystem.bipsystem.get_available_stock",
                AsyncMock(return_value=130),
            ),
            patch("bipsystem.bipsystem.add_cashier_purchase_item", add_item),
        ):
            await AuthState.add_cashier_item.fn(
                state,
                {"barcode": " 0001234567890 ", "quantity": "2"},
            )
            request_id = state.cashier_pending_request_id
            await AuthState.add_cashier_item.fn(
                state,
                {"barcode": "0001234567890", "quantity": "2"},
            )

        self.assertEqual(add_item.await_count, 2)
        first_call = add_item.await_args_list[0].args
        second_call = add_item.await_args_list[1].args
        self.assertEqual(first_call, second_call)
        self.assertEqual(first_call[2], "0001234567890")
        self.assertEqual(first_call[3], 2)
        self.assertEqual(first_call[4], request_id)
        self.assertEqual(state.cashier_pending_request_id, "")
        self.assertEqual(state.cashier_barcode, "")
        self.assertEqual(state.last_purchase, PURCHASE_RESPONSE)

    async def test_invalid_quantity_does_not_call_the_database(self) -> None:
        state = SimpleNamespace(
            cashier_barcode="123",
            cashier_quantity="0.5",
            cashier_purchase_id=PURCHASE_ID,
            cashier_purchase_status="open",
            cashier_feedback="",
            cashier_busy=False,
        )
        add_item = AsyncMock()

        with patch("bipsystem.bipsystem.add_cashier_purchase_item", add_item):
            await AuthState.add_cashier_item.fn(
                state,
                {"barcode": "123", "quantity": "0.5"},
            )

        add_item.assert_not_awaited()
        self.assertIn("inteiro maior que zero", state.cashier_feedback)

    async def test_entry_card_can_close_and_reopen_without_closing_purchase(self) -> None:
        state = SimpleNamespace(
            cashier_purchase_status="open",
            cashier_entry_open=True,
            cashier_feedback="",
        )

        AuthState.toggle_cashier_entry.fn(state)
        self.assertFalse(state.cashier_entry_open)
        self.assertEqual(state.cashier_purchase_status, "open")

        AuthState.toggle_cashier_entry.fn(state)
        self.assertTrue(state.cashier_entry_open)
        self.assertEqual(state.cashier_purchase_status, "open")

        state.cashier_purchase_status = "completed"
        AuthState.toggle_cashier_entry.fn(state)
        self.assertTrue(state.cashier_entry_open)

    async def test_cancel_confirmation_only_opens_for_an_open_purchase(self) -> None:
        state = SimpleNamespace(
            cashier_purchase_status="open",
            cashier_cancel_confirmation_open=False,
        )

        AuthState.open_cashier_cancel_confirmation.fn(state)
        self.assertTrue(state.cashier_cancel_confirmation_open)

        state.cashier_purchase_status = "cancelled"
        state.cashier_cancel_confirmation_open = False
        AuthState.open_cashier_cancel_confirmation.fn(state)
        self.assertFalse(state.cashier_cancel_confirmation_open)

    async def test_payment_selection_completes_sale_once_for_each_method(self) -> None:
        for method in ("credit_card", "debit_card", "pix", "cash"):
            state = SimpleNamespace(
                cashier_busy=False,
                cashier_purchase_id=PURCHASE_ID,
                cashier_open_request_id="request",
                cashier_purchase_status="open",
                cashier_payment_method="",
                cashier_items=[
                    {
                        "product_name": "Arroz",
                        "quantity": "2",
                        "barcode": "0001234567890",
                    }
                ],
                cashier_total_display="10,00 R$",
                cashier_entry_open=True,
                cashier_pending_request_id="",
                cashier_pending_barcode="",
                cashier_pending_quantity=0,
                cashier_payment_modal_open=False,
                cashier_selected_payment_method="",
                cashier_payment_feedback="",
                cashier_feedback="",
                _auth_token="access-token",
            )
            state._set_cashier_purchase = lambda purchase: (
                AuthState._set_cashier_purchase(state, purchase)
            )
            completed_purchase = {
                **PURCHASE_RESPONSE,
                "status": "completed",
                "payment_method": method,
            }
            complete = AsyncMock(return_value=completed_purchase)

            with (
                patch(
                    "bipsystem.bipsystem.cashier_stock_error",
                    AsyncMock(return_value=None),
                ),
                patch("bipsystem.bipsystem.complete_cashier_purchase", complete),
            ):
                AuthState.open_cashier_payment_modal.fn(state)
                self.assertTrue(state.cashier_payment_modal_open)
                await AuthState.select_cashier_payment_method.fn(state, method)

            complete.assert_awaited_once_with("access-token", PURCHASE_ID, method)
            self.assertEqual(state.cashier_purchase_status, "completed")
            self.assertEqual(state.cashier_payment_method, method)
            self.assertFalse(state.cashier_payment_modal_open)
            self.assertFalse(state.cashier_busy)
            self.assertEqual(state.cashier_items[0]["product_name"], "Arroz Tipo 1 500 g")
            self.assertEqual(state.cashier_total_display, "10,00 R$")
            self.assertIn("Venda concluída", state.cashier_feedback)

    async def test_payment_failure_keeps_sale_and_modal_open(self) -> None:
        state = SimpleNamespace(
            cashier_busy=False,
            cashier_purchase_id=PURCHASE_ID,
            cashier_purchase_status="open",
            cashier_payment_method="",
            cashier_items=[
                {
                    "product_name": "Arroz",
                    "quantity": "2",
                    "barcode": "0001234567890",
                }
            ],
            cashier_total_display="10,00 R$",
            cashier_payment_modal_open=True,
            cashier_selected_payment_method="",
            cashier_payment_feedback="",
            cashier_feedback="",
            _auth_token="access-token",
        )
        state._handle_cashier_error = lambda error, action: (
            AuthState._handle_cashier_error(state, error, action)
        )
        complete = AsyncMock(
            side_effect=SupabaseApiError(
                409,
                "P1010",
                "Estoque insuficiente para concluir a venda.",
            )
        )

        with (
            patch(
                "bipsystem.bipsystem.cashier_stock_error",
                AsyncMock(return_value=None),
            ),
            patch("bipsystem.bipsystem.complete_cashier_purchase", complete),
        ):
            await AuthState.select_cashier_payment_method.fn(state, "cash")

        complete.assert_awaited_once()
        self.assertEqual(state.cashier_purchase_status, "open")
        self.assertTrue(state.cashier_payment_modal_open)
        self.assertFalse(state.cashier_busy)
        self.assertEqual(
            state.cashier_items,
            [
                {
                    "product_name": "Arroz",
                    "quantity": "2",
                    "barcode": "0001234567890",
                }
            ],
        )
        self.assertEqual(state.cashier_total_display, "10,00 R$")
        self.assertIn("Estoque insuficiente", state.cashier_payment_feedback)

    async def test_payment_preflight_blocks_insufficient_stock(self) -> None:
        items = [
            {
                "product_name": "Arroz",
                "quantity": "131",
                "barcode": "0001234567890",
            }
        ]
        state = SimpleNamespace(
            cashier_busy=False,
            cashier_purchase_id=PURCHASE_ID,
            cashier_purchase_status="open",
            cashier_items=items,
            cashier_payment_modal_open=True,
            cashier_selected_payment_method="",
            cashier_payment_feedback="",
            cashier_feedback="",
            _auth_token="access-token",
        )
        complete = AsyncMock()

        with (
            patch(
                "bipsystem.bipsystem.cashier_stock_error",
                AsyncMock(
                    return_value=(
                        "Estoque insuficiente. Disponível: 130 unidades. "
                        "Quantidade solicitada: 131."
                    )
                ),
            ),
            patch("bipsystem.bipsystem.complete_cashier_purchase", complete),
        ):
            await AuthState.select_cashier_payment_method.fn(state, "pix")

        complete.assert_not_awaited()
        self.assertEqual(state.cashier_items, items)
        self.assertTrue(state.cashier_payment_modal_open)
        self.assertFalse(state.cashier_busy)
        self.assertIn("Disponível: 130 unidades", state.cashier_payment_feedback)

    async def test_busy_payment_cannot_be_retriggered_or_close_modal(self) -> None:
        state = SimpleNamespace(
            cashier_busy=True,
            cashier_purchase_status="open",
            cashier_items=[{"product_name": "Arroz"}],
            cashier_payment_modal_open=True,
            cashier_selected_payment_method="",
            cashier_payment_feedback="",
            _auth_token="access-token",
        )
        complete = AsyncMock()

        with patch("bipsystem.bipsystem.complete_cashier_purchase", complete):
            await AuthState.select_cashier_payment_method.fn(state, "pix")
        AuthState.close_cashier_payment_modal.fn(state)

        complete.assert_not_awaited()
        self.assertTrue(state.cashier_payment_modal_open)

    async def test_empty_purchase_and_invalid_method_do_not_finalize(self) -> None:
        state = SimpleNamespace(
            cashier_busy=False,
            cashier_purchase_id=PURCHASE_ID,
            cashier_purchase_status="open",
            cashier_items=[],
            cashier_payment_modal_open=False,
            cashier_selected_payment_method="",
            cashier_payment_feedback="",
            _auth_token="access-token",
        )
        complete = AsyncMock()

        with patch("bipsystem.bipsystem.complete_cashier_purchase", complete):
            AuthState.open_cashier_payment_modal.fn(state)
            self.assertFalse(state.cashier_payment_modal_open)
            state.cashier_items = [{"product_name": "Arroz"}]
            AuthState.open_cashier_payment_modal.fn(state)
            await AuthState.select_cashier_payment_method.fn(state, "unknown")

        complete.assert_not_awaited()
        self.assertEqual(state.cashier_selected_payment_method, "")
        self.assertTrue(state.cashier_payment_modal_open)


class CashierPageRenderingTests(unittest.TestCase):
    def test_page_binds_total_items_and_purchase_actions(self) -> None:
        serialized = json.dumps(cashier_page_content().render(), default=str)

        self.assertIn("Digite ou escaneie o c", serialized)
        self.assertIn(r"c\\u00f3digo de barra", serialized)
        self.assertIn("/caixa-inicio", serialized)
        self.assertIn("Voltar para a tela inicial", serialized)
        self.assertIn("LucideArrowLeft", serialized)
        self.assertIn(".cashier-back-link:hover", bipsystem.app.style)
        self.assertIn(".cashier-back-link:focus-visible", bipsystem.app.style)
        self.assertEqual(serialized.count("cashier-entry-input"), 2)
        self.assertGreaterEqual(serialized.count("#000000"), 12)
        self.assertIn("#F7F9FC", serialized)
        self.assertIn("3.1rem", serialized)
        self.assertIn("0.7rem", serialized)
        self.assertIn("&:hover", serialized)
        self.assertIn("&:focus-visible", serialized)
        self.assertIn("&:active", serialized)
        cashier_styles = bipsystem.app.style
        selectors = next(
            selector
            for selector in cashier_styles
            if selector.startswith(".cashier-entry-input, ")
        )
        self.assertIn(".cashier-entry-input:focus-visible", selectors)
        self.assertIn(".cashier-entry-input input:focus", selectors)
        self.assertIn(".cashier-entry-input input:active", selectors)
        self.assertEqual(
            cashier_styles[selectors]["color"],
            "#000000 !important",
        )
        self.assertEqual(
            cashier_styles[selectors]["-webkit-text-fill-color"],
            "#000000 !important",
        )
        placeholder_selectors = next(
            selector
            for selector in cashier_styles
            if selector.startswith(".cashier-entry-input::placeholder")
        )
        self.assertIn("input:focus::placeholder", placeholder_selectors)
        self.assertIn("input:focus-visible::placeholder", placeholder_selectors)
        self.assertIn("input:active::placeholder", placeholder_selectors)
        self.assertEqual(
            cashier_styles[placeholder_selectors]["color"],
            "#000000 !important",
        )
        self.assertIn("cashier_total_display", serialized)
        self.assertIn("cashier_items", serialized)
        self.assertIn("cashier-brand-name", serialized)
        self.assertIn("Segoe Script", serialized)
        self.assertIn("cashier-page-clock", serialized)
        self.assertIn("HH:mm", serialized)
        self.assertIn("D [de] MMMM [de] YYYY", serialized)
        self.assertIn("pt-br", serialized)
        self.assertIn("cashier-total-card", serialized)
        self.assertIn("cashier-products-card", serialized)
        self.assertIn("cashier-items-table", serialized)
        self.assertIn("minmax(6.5rem, 1.2fr)", serialized)
        self.assertIn("Adicionar", serialized)
        self.assertIn("Finalizar compra", serialized)
        self.assertIn("Cancelar compra", serialized)
        self.assertIn("Nova compra", serialized)
        self.assertIn("RadixThemesDialog.Root", serialized)
        self.assertIn("RadixThemesDialog.Content", serialized)
        self.assertIn("Escolha o m", serialized)
        self.assertIn(r"m\\u00e9todo de pagamento", serialized)
        self.assertIn("Selecione como o cliente deseja realizar o pagamento.", serialized)
        self.assertIn("Fechar sele", serialized)
        self.assertIn(r"sele\\u00e7\\u00e3o de pagamento", serialized)
        self.assertEqual(serialized.count("select_cashier_payment_method"), 4)
        self.assertIn(r"Parcela em at\\u00e9 12x", serialized)
        self.assertIn(r"Pagamento instant\\u00e2neo", serialized)
        self.assertIn("Finalizando venda...", serialized)
        self.assertNotIn("A seleção não processa nem confirma o pagamento.", serialized)
        self.assertNotIn("O pagamento ainda não está integrado.", serialized)
        self.assertNotIn("finalize_cashier_purchase", serialized)
        self.assertIn(".rt-DialogOverlay", bipsystem.app.style)
        self.assertIn(".rt-DialogContent.cashier-payment-dialog", bipsystem.app.style)
        self.assertEqual(
            bipsystem.app.style[
                ".rt-DialogContent.cashier-payment-dialog"
            ]["background_color"],
            "#FFFFFF !important",
        )
        self.assertIn(".cashier-payment-option:focus-visible", bipsystem.app.style)
        self.assertIn(".cashier-payment-option.is-selected", bipsystem.app.style)
        self.assertIn("@media (max-width: 560px)", bipsystem.app.style)
        self.assertNotIn("1234,00 R$", serialized)
