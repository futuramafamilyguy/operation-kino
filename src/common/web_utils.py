import asyncio
from typing import Optional
import aiohttp


RETRY_COUNT = 2
DELAY_DURATION = 0.5

async def fetch_html(
    session: aiohttp.ClientSession, url: str, headers: dict = None, timeout=10
) -> Optional[str]:
    for attempt in range(RETRY_COUNT + 1):
        try:
            async with session.get(
                url, headers=headers or {}, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response.raise_for_status()
                return await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            if attempt < RETRY_COUNT:
                print(f'failed to fetch at {url}. retrying...')
                await asyncio.sleep(DELAY_DURATION)
            else:
                return None
