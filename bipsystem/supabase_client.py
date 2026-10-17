from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
from urllib.parse import urlsplit

import httpx
from supabase import AsyncClient, AsyncClientOptions, create_async_client


class SupabaseConfigurationError(RuntimeError):
    pass


class SupabaseSessionError(RuntimeError):
    pass


def _get_public_configuration() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "").strip()
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if not url or not anon_key:
        raise SupabaseConfigurationError(
            "Configure SUPABASE_URL and SUPABASE_ANON_KEY to use Supabase."
        )

    parsed_url = urlsplit(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise SupabaseConfigurationError(
            "SUPABASE_URL must be a valid HTTP or HTTPS URL."
        )

    return url.rstrip("/"), anon_key


@asynccontextmanager
async def request_supabase_client(
    access_token: str | None = None,
) -> AsyncIterator[AsyncClient]:
    url, anon_key = _get_public_configuration()
    headers: dict[str, str] = {}
    if access_token is not None:
        if not access_token.strip():
            raise SupabaseSessionError("A non-empty Supabase access token is required.")
        headers["Authorization"] = f"Bearer {access_token}"

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        options = AsyncClientOptions(
            headers=headers,
            auto_refresh_token=False,
            persist_session=False,
            httpx_client=http_client,
        )
        client = await create_async_client(url, anon_key, options=options)
        yield client
