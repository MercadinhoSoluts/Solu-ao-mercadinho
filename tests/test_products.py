import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from bipsystem.auth_client import (
    SupabaseApiError,
    create_inventory_lot,
    is_valid_product_text,
    list_inventory,
    list_products,
    parse_inventory_date,
    parse_inventory_units,
    parse_product_weight,
)
from bipsystem.bipsystem import AuthState


class ProductValidationTests(unittest.TestCase):
    def test_accepts_letters_spaces_and_portuguese_accents(self) -> None:
        for value in ("Margarina", "Leite Integral", "Coca Cola", "São Braz", "Nestlé"):
            with self.subTest(value=value):
                self.assertTrue(is_valid_product_text(value))

    def test_rejects_numbers_symbols_and_blank_product_text(self) -> None:
        for value in ("123", "Leite 2", "Leite2", "Marca@", "", "   "):
            with self.subTest(value=value):
                self.assertFalse(is_valid_product_text(value))

    def test_parses_valid_product_weight(self) -> None:
        self.assertEqual(parse_product_weight("100"), 100)
        self.assertEqual(parse_product_weight("1.25"), 1.25)
        self.assertIsNone(parse_product_weight(""))
        self.assertIsNone(parse_product_weight("NaN"))

    def test_parses_inventory_quantity_and_expiry(self) -> None:
        self.assertEqual(parse_inventory_units("15"), 15)
        self.assertIsNone(parse_inventory_units("0"))
        self.assertEqual(parse_inventory_date("2027-12-20"), "2027-12-20")
        self.assertIsNone(parse_inventory_date("20/12/2027"))

    def test_inventory_product_name_uses_catalog_weight(self) -> None:
        self.assertEqual(
            AuthState._inventory_product_name(
                {"tipo": "Leite", "marca": "Marca", "peso": 500}
            ),
            "Leite Marca 500 g",
        )


class ProductStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_text_does_not_call_supabase(self) -> None:
        state = SimpleNamespace(
            user_role="owner",
            _auth_token="token",
            product_tipo="Leite2",
            product_marca="Qualy",
            product_peso="100",
            product_codigo_de_barra="000123",
            is_busy=False,
        )
        with patch(
            "bipsystem.bipsystem.create_product",
            new_callable=AsyncMock,
        ) as create_product_mock:
            await AuthState.register_product.fn(state)
        create_product_mock.assert_not_awaited()

    async def test_operator_can_register_a_product(self) -> None:
        state = SimpleNamespace(
            user_role="operator",
            _auth_token="token",
            product_tipo="Leite",
            product_marca="Marca",
            product_peso="500",
            product_codigo_de_barra="000123",
            is_busy=False,
            _clear_product_form=MagicMock(),
        )
        with patch(
            "bipsystem.bipsystem.create_product",
            new_callable=AsyncMock,
            return_value={"id": "product-id"},
        ) as create_mock:
            await AuthState.register_product.fn(state)
        create_mock.assert_awaited_once_with("token", "Leite", "Marca", 500, "000123")

    async def test_receiving_uses_atomic_supabase_rpc_for_existing_product_barcode(self) -> None:
        state = SimpleNamespace(
            user_role="operator",
            _auth_token="token",
            conference_codigo="000123",
            conference_lote="L-2",
            conference_unidades="15",
            conference_validade="2027-12-20",
            is_busy=False,
            load_inventory=AsyncMock(),
        )
        with (
            patch(
                "bipsystem.bipsystem.find_product_by_barcode",
                new=AsyncMock(
                    return_value={
                        "id": "product-id",
                        "codigo_de_barra": "000123",
                    }
                ),
            ) as find_mock,
            patch(
                "bipsystem.bipsystem.create_inventory_lot",
                new=AsyncMock(),
            ) as create_mock,
        ):
            await AuthState.add_inventory.fn(state)

        find_mock.assert_awaited_once_with("token", "000123")
        create_mock.assert_awaited_once_with(
            "token",
            "product-id",
            15,
            "2027-12-20",
            "L-2",
        )
        state.load_inventory.assert_awaited_once()

    async def test_unknown_barcode_does_not_create_stock(self) -> None:
        state = SimpleNamespace(
            user_role="operator",
            _auth_token="token",
            conference_codigo="000123",
            conference_lote="L-2",
            conference_unidades="15",
            conference_validade="2027-12-20",
            is_busy=False,
        )
        with (
            patch(
                "bipsystem.bipsystem.find_product_by_barcode",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "bipsystem.bipsystem.create_inventory_lot",
                new=AsyncMock(),
            ) as create_mock,
        ):
            await AuthState.add_inventory.fn(state)
        create_mock.assert_not_awaited()


class SupabaseInventoryApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_inventory_records_map_supabase_fields_to_ui_contract(self) -> None:
        response = SimpleNamespace(
            data=[
                {
                    "id": "lot-id",
                    "product_id": "product-id",
                    "batch_label": "L1",
                    "units": 7,
                    "expires_on": "2027-01-02",
                }
            ]
        )
        query = MagicMock()
        query.select.return_value.order.return_value.execute = AsyncMock(
            return_value=response
        )
        client = SimpleNamespace(table=MagicMock(return_value=query))

        @asynccontextmanager
        async def fake_client(token):
            self.assertEqual(token, "user-token")
            yield client

        with patch(
            "bipsystem.auth_client.request_supabase_client",
            side_effect=fake_client,
        ):
            records = await list_inventory("user-token")
        self.assertEqual(
            records,
            [
                {
                    "id": "lot-id",
                    "produtos_id": "product-id",
                    "lote": "L1",
                    "unidades": 7,
                    "validade": "2027-01-02",
                }
            ],
        )

    async def test_product_query_maps_fields_for_existing_reflex_workflows(self) -> None:
        query = MagicMock()
        query.select.return_value.eq.return_value.order.return_value.execute = (
            AsyncMock(
                return_value=SimpleNamespace(
                    data=[
                        {
                            "id": "product-id",
                            "product_type": "Arroz",
                            "brand": "Marca",
                            "weight_grams": 5000,
                            "barcode": "000123",
                        }
                    ]
                )
            )
        )
        client = SimpleNamespace(table=MagicMock(return_value=query))

        @asynccontextmanager
        async def fake_client(token):
            yield client

        with patch(
            "bipsystem.auth_client.request_supabase_client",
            side_effect=fake_client,
        ):
            records = await list_products("user-token")

        self.assertEqual(
            records,
            [
                {
                    "id": "product-id",
                    "tipo": "Arroz",
                    "marca": "Marca",
                    "peso": 5000.0,
                    "codigo_de_barra": "000123",
                }
            ],
        )

    async def test_stock_receive_calls_atomic_database_function(self) -> None:
        row = {
            "id": "lot-id",
            "product_id": "product-id",
            "batch_label": "L1",
            "units": 10,
            "expires_on": "2027-01-02",
        }
        rpc = MagicMock()
        rpc.execute = AsyncMock(return_value=SimpleNamespace(data=row))
        client = SimpleNamespace(rpc=MagicMock(return_value=rpc))

        @asynccontextmanager
        async def fake_client(token):
            yield client

        with patch(
            "bipsystem.auth_client.request_supabase_client",
            side_effect=fake_client,
        ):
            result = await create_inventory_lot(
                "user-token",
                "product-id",
                10,
                "2027-01-02",
                "L1",
            )

        client.rpc.assert_called_once_with(
            "receive_stock",
            {
                "p_product_id": "product-id",
                "p_batch_label": "L1",
                "p_units": 10,
                "p_expires_on": "2027-01-02",
            },
        )
        self.assertEqual(result["unidades"], 10)
