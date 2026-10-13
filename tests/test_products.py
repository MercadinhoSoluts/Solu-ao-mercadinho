import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from bipsystem.auth_client import (
    XanoApiError,
    create_product,
    create_inventory_lot,
    is_valid_product_text,
    list_inventory,
    list_products,
    parse_product_weight,
    update_inventory_lot,
)
from bipsystem.bipsystem import AuthState, find_inventory_record


class ProductValidationTests(unittest.TestCase):
    def test_accepts_letters_spaces_and_portuguese_accents(self) -> None:
        for value in ("Margarina", "Leite Integral", "Coca Cola", "São Braz", "Nestlé"):
            with self.subTest(value=value):
                self.assertTrue(is_valid_product_text(value))

    def test_rejects_numbers_symbols_and_blank_product_text(self) -> None:
        for value in ("123", "Leite 2", "Leite2", "Marca@", "", "   "):
            with self.subTest(value=value):
                self.assertFalse(is_valid_product_text(value))

    def test_parses_integer_and_fractional_weights(self) -> None:
        self.assertEqual(parse_product_weight("100"), 100)
        self.assertEqual(parse_product_weight("1.25"), 1.25)

    def test_rejects_invalid_weights(self) -> None:
        self.assertIsNone(parse_product_weight(""))
        self.assertIsNone(parse_product_weight("abc"))
        self.assertIsNone(parse_product_weight("NaN"))


class ProductStateValidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_text_does_not_call_xano(self) -> None:
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


class ProductApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_product_sends_barcode_as_text_and_validates_response(self) -> None:
        response = httpx.Response(
            200,
            json={
                "id": 42,
                "created_at": 1791586257965,
                "tipo": "MARGARINA",
                "marca": "qualy",
                "peso": 100,
                "codigo_de_barra": "000123",
            },
        )
        client = AsyncMock()
        client.post.return_value = response

        with patch("bipsystem.auth_client.httpx.AsyncClient") as client_factory:
            client_factory.return_value.__aenter__.return_value = client
            result = await create_product(
                "token",
                "MARGARINA",
                "qualy",
                100,
                "000123",
            )

        self.assertEqual(result["id"], 42)
        client.post.assert_awaited_once_with(
            "https://x8ki-letl-twmt.n7.xano.io/api:_832jVAW/produtos",
            headers={"Authorization": "Bearer token"},
            json={
                "tipo": "MARGARINA",
                "marca": "qualy",
                "peso": 100,
                "codigo_de_barra": "000123",
            },
        )

    async def test_create_product_preserves_api_errors(self) -> None:
        response = httpx.Response(
            409,
            json={"code": "ERROR_CODE_UNIQUE", "message": "barcode must be unique"},
        )
        client = AsyncMock()
        client.post.return_value = response

        with patch("bipsystem.auth_client.httpx.AsyncClient") as client_factory:
            client_factory.return_value.__aenter__.return_value = client
            with self.assertRaises(XanoApiError) as error:
                await create_product("token", "MARGARINA", "qualy", 100, "000123")

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(error.exception.code, "ERROR_CODE_UNIQUE")


class InventoryApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_inventory_endpoints_use_product_and_lot_contract(self) -> None:
        client = AsyncMock()
        client.get.side_effect = [
            httpx.Response(200, json=[{"id": 1, "codigo_de_barra": "000123"}]),
            httpx.Response(200, json=[{"id": 8, "produtos_id": 1, "unidades": 2}]),
        ]
        client.post.return_value = httpx.Response(
            200,
            json={"id": 9, "produtos_id": 1, "unidades": 5},
        )
        client.patch.return_value = httpx.Response(
            200,
            json={"id": 8, "produtos_id": 1, "unidades": 7},
        )

        with patch("bipsystem.auth_client.httpx.AsyncClient") as client_factory:
            client_factory.return_value.__aenter__.return_value = client
            self.assertEqual((await list_products("token"))[0]["id"], 1)
            self.assertEqual((await list_inventory("token"))[0]["id"], 8)
            await create_inventory_lot("token", 1, 5, "2027-01-02", "L1")
            await update_inventory_lot("token", 8, 7)

        client.post.assert_awaited_once_with(
            "https://x8ki-letl-twmt.n7.xano.io/api:_832jVAW/estoque",
            headers={"Authorization": "Bearer token"},
            json={
                "produtos_id": 1,
                "unidades": 5,
                "validade": "2027-01-02",
                "lote": "L1",
            },
        )
        client.patch.assert_awaited_once_with(
            "https://x8ki-letl-twmt.n7.xano.io/api:_832jVAW/estoque/8",
            headers={"Authorization": "Bearer token"},
            json={"unidades": 7},
        )


class InventoryBusinessRuleTests(unittest.TestCase):
    INVENTORY = [
        {
            "id": 15,
            "produtos_id": 1,
            "lote": "1",
            "validade": "2027-12-20",
            "unidades": 30,
        },
        {
            "id": 20,
            "produtos_id": 2,
            "lote": "9",
            "validade": "2027-12-20",
            "unidades": 12,
        },
    ]

    def test_same_product_and_validity_match_even_when_lot_differs(self) -> None:
        record = find_inventory_record(self.INVENTORY, 1, "2027-12-20")
        self.assertEqual(record["id"], 15)
        self.assertEqual(record["lote"], "1")

    def test_same_product_and_validity_match_with_same_lot(self) -> None:
        self.assertEqual(
            find_inventory_record(self.INVENTORY, 1, "2027-12-20")["id"],
            15,
        )

    def test_different_validity_creates_a_new_candidate(self) -> None:
        self.assertIsNone(find_inventory_record(self.INVENTORY, 1, "2028-01-20"))

    def test_different_product_with_same_validity_is_independent(self) -> None:
        record = find_inventory_record(self.INVENTORY, 2, "2027-12-20")
        self.assertEqual(record["id"], 20)


class InventoryStateIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_different_lot_updates_existing_record_without_creating_one(self) -> None:
        state = SimpleNamespace(
            user_role="owner",
            _auth_token="token",
            conference_codigo="000123",
            conference_lote="2",
            conference_unidades="15",
            conference_validade="2027-12-20",
            is_busy=False,
            load_inventory=AsyncMock(),
        )
        existing = {
            "id": 15,
            "produtos_id": 1,
            "lote": "1",
            "validade": "2027-12-20",
            "unidades": 30,
        }

        with (
            patch(
                "bipsystem.bipsystem.list_products",
                new=AsyncMock(return_value=[{"id": 1, "codigo_de_barra": "000123"}]),
            ),
            patch(
                "bipsystem.bipsystem.list_inventory",
                new=AsyncMock(return_value=[existing]),
            ),
            patch(
                "bipsystem.bipsystem.update_inventory_lot",
                new=AsyncMock(return_value={**existing, "unidades": 45}),
            ) as update_mock,
            patch(
                "bipsystem.bipsystem.create_inventory_lot",
                new=AsyncMock(),
            ) as create_mock,
        ):
            await AuthState.add_inventory.fn(state)

        update_mock.assert_awaited_once_with("token", 15, 45)
        create_mock.assert_not_awaited()
