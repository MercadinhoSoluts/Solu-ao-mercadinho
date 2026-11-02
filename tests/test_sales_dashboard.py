import unittest
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from bipsystem.auth_client import SupabaseApiError, list_completed_sales
from bipsystem.bipsystem import (
    REPORT_CARDS,
    EstoqueState,
    SalesDashboardState,
    ValidadeState,
    reports_cards,
    sales_dashboard_page,
)


LOCAL_TZ = timezone(timedelta(hours=-3))


class SalesChartTests(unittest.TestCase):
    def test_daily_sales_are_grouped_by_local_hour(self) -> None:
        now = datetime(2026, 11, 2, 12, 0, tzinfo=LOCAL_TZ)
        labels, values = SalesDashboardState._chart_values(
            [
                {"created_at": "2026-11-02T03:30:00Z", "total_cents": 1250},
                {"created_at": "2026-11-02T04:10:00Z", "total_cents": 300},
                {"created_at": "2026-11-01T04:10:00Z", "total_cents": 999},
            ],
            "daily",
            now,
        )

        self.assertEqual(len(labels), 24)
        self.assertEqual(values[0], 12.5)
        self.assertEqual(values[1], 3.0)
        self.assertEqual(sum(values), 15.5)

    def test_weekly_sales_cover_today_and_the_previous_six_days(self) -> None:
        now = datetime(2026, 11, 2, 12, 0, tzinfo=LOCAL_TZ)
        labels, values = SalesDashboardState._chart_values(
            [
                {"created_at": "2026-10-27T03:00:00Z", "total_cents": 2500},
                {"created_at": "2026-11-01T15:00:00Z", "total_cents": 1750},
                {"created_at": "2026-10-26T23:59:00Z", "total_cents": 999},
            ],
            "weekly",
            now,
        )

        self.assertEqual(len(labels), 7)
        self.assertEqual(labels[0], "27/10")
        self.assertEqual(labels[-1], "02/11")
        self.assertEqual(values[0], 25.0)
        self.assertEqual(values[5], 17.5)
        self.assertEqual(sum(values), 42.5)

    def test_chart_rejects_invalid_sale_amounts(self) -> None:
        with self.assertRaises(SupabaseApiError):
            SalesDashboardState._chart_values(
                [{"created_at": "2026-11-02T03:30:00Z", "total_cents": -1}],
                "daily",
                datetime(2026, 11, 2, 12, 0, tzinfo=LOCAL_TZ),
            )


class SalesQueryTests(unittest.IsolatedAsyncioTestCase):
    async def test_query_filters_completed_purchases_by_created_at(self) -> None:
        rows = [{"created_at": "2026-11-02T03:30:00Z", "total_cents": 1250}]
        query = Mock()
        query.select.return_value = query
        query.eq.return_value = query
        query.gte.return_value = query
        query.lt.return_value = query
        query.order.return_value = query
        query.execute = AsyncMock(return_value=SimpleNamespace(data=rows))
        client = Mock()
        client.table.return_value = query

        @asynccontextmanager
        async def fake_client(token: str):
            self.assertEqual(token, "manager-token")
            yield client

        with patch("bipsystem.auth_client.request_supabase_client", fake_client):
            result = await list_completed_sales(
                "manager-token",
                "2026-11-02T03:00:00+00:00",
                "2026-11-03T03:00:00+00:00",
            )

        self.assertEqual(result, rows)
        client.table.assert_called_once_with("purchases")
        query.select.assert_called_once_with("created_at, total_cents")
        query.eq.assert_called_once_with("status", "completed")
        query.gte.assert_called_once_with("created_at", "2026-11-02T03:00:00+00:00")
        query.lt.assert_called_once_with("created_at", "2026-11-03T03:00:00+00:00")
        query.order.assert_called_once_with("created_at")


class SalesCardNavigationTests(unittest.TestCase):
    def test_sales_cards_use_internal_navigation_in_the_current_tab(self) -> None:
        component = reports_cards()
        card_links = component.children

        self.assertEqual(len(card_links), len(REPORT_CARDS))
        for link, card in zip(card_links, REPORT_CARDS, strict=True):
            router_link = link.children[0]
            self.assertEqual(router_link.to._var_value, card["href"])
            self.assertIsNone(link.is_external)
            self.assertIsNone(link.target)

    def test_inventory_cards_link_to_their_dedicated_dashboards(self) -> None:
        self.assertEqual(REPORT_CARDS[0]["href"], "/data-proxima")
        self.assertEqual(REPORT_CARDS[1]["href"], "/estoque-baixo")

    def test_daily_and_weekly_sales_dashboards_have_home_button(self) -> None:
        for title in ("Vendas diárias", "Vendas semanais"):
            with self.subTest(title=title):
                page = sales_dashboard_page(title)
                home_link = page.children[0]
                router_link = home_link.children[0]
                button = router_link.children[0]

                self.assertEqual(router_link.to._var_value, "/")
                self.assertEqual(
                    button.children[1].contents._var_value,
                    "Voltar para o início",
                )


class InventoryDashboardFigureTests(unittest.TestCase):
    today = datetime(2026, 11, 2).date()
    products = [
        {
            "id": "p1",
            "tipo": "Arroz",
            "marca": "Marca A",
            "peso": 1000,
        },
        {
            "id": "p2",
            "tipo": "Leite",
            "marca": "Marca B",
            "peso": 1000,
        },
    ]

    def test_low_stock_sums_non_expired_lots_and_includes_zero_stock(self) -> None:
        figure = EstoqueState._build_figure(
            [
                {
                    "produtos_id": "p1",
                    "unidades": 4,
                    "validade": "2026-11-02",
                },
                {
                    "produtos_id": "p1",
                    "unidades": 7,
                    "validade": "2026-11-01",
                },
            ],
            self.products,
            self.today,
        )

        self.assertEqual(figure["data"][0]["marker"]["color"], "#EF4444")
        self.assertEqual(
            figure["data"][0]["x"],
            ["Leite Marca B 1000 g", "Arroz Marca A 1000 g"],
        )
        self.assertEqual(figure["data"][0]["y"], [0, 4])

    def test_expiry_report_sorts_valid_lots_in_the_next_fifteen_days(self) -> None:
        figure = ValidadeState._build_figure(
            [
                {
                    "produtos_id": "p1",
                    "lote": "Tarde",
                    "unidades": 3,
                    "validade": "2026-11-17",
                },
                {
                    "produtos_id": "p2",
                    "lote": "Hoje",
                    "unidades": 5,
                    "validade": "2026-11-02",
                },
                {
                    "produtos_id": "p1",
                    "lote": "Expirado",
                    "unidades": 6,
                    "validade": "2026-11-01",
                },
                {
                    "produtos_id": "p2",
                    "lote": "Depois",
                    "unidades": 2,
                    "validade": "2026-11-18",
                },
                {
                    "produtos_id": "p1",
                    "lote": "Vazio",
                    "unidades": 0,
                    "validade": "2026-11-03",
                },
            ],
            self.products,
            self.today,
        )

        trace = figure["data"][0]
        self.assertEqual(trace["orientation"], "h")
        self.assertEqual(
            trace["y"],
            [
                "Leite Marca B 1000 g — lote Hoje",
                "Arroz Marca A 1000 g — lote Tarde",
            ],
        )
        self.assertEqual(trace["x"], [0, 15])
        self.assertEqual(trace["customdata"], [5, 3])
