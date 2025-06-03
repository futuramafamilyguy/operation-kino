import asyncio
import logging
from typing import Optional
import aiohttp


RETRY_COUNT = 2
DELAY_DURATION = 0.5

logger = logging.getLogger(__name__)


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
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt < RETRY_COUNT:
                logger.warning(f'[attempt {attempt}] failed to fetch at {url}: {e}')
                await asyncio.sleep(DELAY_DURATION)
            else:
                logger.error(f'all attempts failed at {url}: {e}')
                return None
