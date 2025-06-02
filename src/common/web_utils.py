import asyncio
from typing import Optional
import aiohttp


async def fetch_html(
    session: aiohttp.ClientSession, url: str, headers: dict = None, timeout=10
) -> Optional[str]:
    try:
        async with session.get(
            url, headers=headers or {}, timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            response.raise_for_status()
            return await response.text()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None
