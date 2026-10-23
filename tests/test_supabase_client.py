import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from bipsystem.supabase_client import (
    SupabaseConfigurationError,
    SupabaseSessionError,
    request_supabase_client,
)


class SupabaseClientConfigurationTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_public_configuration_is_explicit(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                SupabaseConfigurationError,
                "SUPABASE_URL and SUPABASE_ANON_KEY",
            ):
                async with request_supabase_client():
                    self.fail("A client should not be created without configuration.")

    async def test_invalid_url_is_rejected(self) -> None:
        with patch.dict(
            os.environ,
            {"SUPABASE_URL": "not-a-url", "SUPABASE_ANON_KEY": "public-key"},
            clear=True,
        ):
            with self.assertRaisesRegex(
                SupabaseConfigurationError,
                "SUPABASE_URL must be a valid HTTP or HTTPS URL",
            ):
                async with request_supabase_client():
                    self.fail("A client should not be created with an invalid URL.")

    async def test_empty_access_token_is_rejected(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_ANON_KEY": "public-key",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(
                SupabaseSessionError,
                "non-empty Supabase access token",
            ):
                async with request_supabase_client(" "):
                    self.fail("An empty user token must not create a client.")

    async def test_authenticated_client_uses_request_scoped_bearer_header(self) -> None:
        fake_client = object()
        fake_httpx_client = object()
        httpx_context = MagicMock()
        httpx_context.__aenter__ = AsyncMock(return_value=fake_httpx_client)
        httpx_context.__aexit__ = AsyncMock(return_value=None)
        with (
            patch.dict(
                os.environ,
                {
                    "SUPABASE_URL": "https://example.supabase.co/",
                    "SUPABASE_ANON_KEY": "public-key",
                },
                clear=True,
            ),
            patch(
                "bipsystem.supabase_client.create_async_client",
                new_callable=AsyncMock,
                return_value=fake_client,
            ) as create_client,
            patch(
                "bipsystem.supabase_client.httpx.AsyncClient",
                return_value=httpx_context,
            ) as httpx_client_factory,
        ):
            async with request_supabase_client("user-access-token") as client:
                self.assertIs(client, fake_client)

        httpx_client_factory.assert_called_once_with(timeout=10.0)
        httpx_context.__aexit__.assert_awaited_once()
        create_client.assert_awaited_once()
        args, kwargs = create_client.await_args
        self.assertEqual(args[:2], ("https://example.supabase.co", "public-key"))
        options = kwargs["options"]
        self.assertEqual(options.headers["Authorization"], "Bearer user-access-token")
        self.assertFalse(options.persist_session)
        self.assertFalse(options.auto_refresh_token)
        self.assertIs(options.httpx_client, fake_httpx_client)

    async def test_request_client_observes_response_only_when_requested(self) -> None:
        fake_httpx_client = object()
        httpx_context = MagicMock()
        httpx_context.__aenter__ = AsyncMock(return_value=fake_httpx_client)
        httpx_context.__aexit__ = AsyncMock(return_value=None)
        observed_statuses: list[int] = []
        with (
            patch.dict(
                os.environ,
                {
                    "SUPABASE_URL": "https://example.supabase.co",
                    "SUPABASE_ANON_KEY": "public-key",
                },
                clear=True,
            ),
            patch(
                "bipsystem.supabase_client.create_async_client",
                new_callable=AsyncMock,
                return_value=object(),
            ),
            patch(
                "bipsystem.supabase_client.httpx.AsyncClient",
                return_value=httpx_context,
            ) as httpx_client_factory,
        ):
            async with request_supabase_client(
                "user-access-token",
                response_observer=lambda response: observed_statuses.append(
                    response.status_code
                ),
            ):
                pass

        kwargs = httpx_client_factory.call_args.kwargs
        self.assertEqual(kwargs["timeout"], 10.0)
        response_hook = kwargs["event_hooks"]["response"][0]
        await response_hook(httpx.Response(403))
        self.assertEqual(observed_statuses, [403])

    async def test_public_client_does_not_set_a_user_authorization_header(self) -> None:
        fake_httpx_client = object()
        httpx_context = MagicMock()
        httpx_context.__aenter__ = AsyncMock(return_value=fake_httpx_client)
        httpx_context.__aexit__ = AsyncMock(return_value=None)
        with (
            patch.dict(
                os.environ,
                {
                    "SUPABASE_URL": "https://example.supabase.co",
                    "SUPABASE_ANON_KEY": "public-key",
                },
                clear=True,
            ),
            patch(
                "bipsystem.supabase_client.create_async_client",
                new_callable=AsyncMock,
                return_value=object(),
            ) as create_client,
            patch(
                "bipsystem.supabase_client.httpx.AsyncClient",
                return_value=httpx_context,
            ),
        ):
            async with request_supabase_client():
                pass

        options = create_client.await_args.kwargs["options"]
        self.assertNotIn("Authorization", options.headers)
        self.assertFalse(options.persist_session)
