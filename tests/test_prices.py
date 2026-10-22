import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bipsystem.auth_client import SupabaseApiError
from bipsystem.bipsystem import PricesState, filter_prices


class PriceDisplayTests(unittest.TestCase):
    def test_formats_price_cents_and_timestamp_for_existing_table(self) -> None:
        row = PricesState._format_price_row(
            {
                "price_cents": 2590,
                "price_created_at": "2026-10-22T12:30:00+00:00",
                "product_name": "Arroz Marca 5000 g",
                "barcode": "000123",
                "brand": "Marca",
            }
        )
        self.assertEqual(row["price"], "R$ 25,90")
        self.assertEqual(row["date"], "22/10/2026")
        self.assertEqual(row["barcode"], "000123")
        self.assertIn("marca", row["search"])

    def test_invalid_price_timestamp_is_a_safe_backend_error(self) -> None:
        with self.assertRaises(SupabaseApiError):
            PricesState._format_price_row(
                {
                    "price_cents": 2590,
                    "price_created_at": "invalid",
                    "product_name": "Produto",
                    "barcode": "1",
                    "brand": "Marca",
                }
            )

    def test_price_search_matches_product_name_brand_and_barcode(self) -> None:
        prices = [
            {"product": "Arroz Marca", "search": "arroz marca 000123 marca"},
            {"product": "Leite", "search": "leite outra 000987 outra"},
        ]
        result = filter_prices(prices, "marca")
        self.assertEqual([price["product"] for price in result], ["Arroz Marca"])


class PriceStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_save_price_persists_exact_cents_for_selected_product(self) -> None:
        state = SimpleNamespace(
            has_selected_product=True,
            selected_product={"id": "product-id"},
            price_input="25,90",
            feedback_is_error=False,
            feedback="",
            _authorized_token=AsyncMock(return_value=("user-token", None)),
            load_prices=AsyncMock(),
        )
        with patch(
            "bipsystem.bipsystem.create_product_price",
            new=AsyncMock(),
        ) as create_mock:
            await PricesState.save_price.fn(state)

        create_mock.assert_awaited_once_with("user-token", "product-id", 2590)
        state.load_prices.assert_awaited_once()
        self.assertEqual(state.feedback, "Preço vinculado com sucesso.")
        self.assertEqual(state.price_input, "")

    async def test_invalid_price_does_not_write_to_supabase(self) -> None:
        state = SimpleNamespace(
            has_selected_product=True,
            selected_product={"id": "product-id"},
            price_input="1.999",
            feedback_is_error=False,
            feedback="",
        )
        with patch(
            "bipsystem.bipsystem.create_product_price",
            new=AsyncMock(),
        ) as create_mock:
            await PricesState.save_price.fn(state)

        create_mock.assert_not_awaited()
        self.assertTrue(state.feedback_is_error)
