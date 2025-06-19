import asyncio
import logging
from typing import Awaitable, Callable, Optional
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


async def stream_html(
    session: aiohttp.ClientSession,
    url: str,
    process_chunk: Callable[[bytes], Awaitable[bool]],
    headers: dict = None,
    timeout: int = 10,
) -> bool:
    for attempt in range(RETRY_COUNT + 1):
        try:
            async with session.get(
                url,
                headers=headers or {},
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                response.raise_for_status()
                async for chunk in response.content.iter_chunked(2048):
                    if await process_chunk(chunk):
                        break
                return True
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt < RETRY_COUNT:
                logger.warning(f'[attempt {attempt}] failed to fetch at {url}: {e}')
                await asyncio.sleep(DELAY_DURATION)
            else:
                logger.error(f'all attempts failed at {url}: {e}')
                return False


async def fetch_html_section(
    session: aiohttp.ClientSession,
    url: str,
    html_section_start: str,
    html_section_end: str,
):
    html_buffer = []
    html_extractor = _build_html_section_extractor(
        html_section_start, html_section_end, html_buffer
    )
    await stream_html(session, url, process_chunk=html_extractor)

    return b''.join(html_buffer).decode('utf-8', errors='ignore')


def _build_html_section_extractor(
    start_marker: str, end_marker: str, buffer: list[bytes]
) -> Callable[[bytes], bool]:
    inside_target = False

    async def _extract_html_section(chunk: bytes) -> bool:
        nonlocal inside_target

        text = chunk.decode('utf-8', errors='ignore')

        if not inside_target:
            start_idx = text.find(start_marker)
            if start_idx != -1:
                inside_target = True
                buffer.append(text[start_idx:].encode())
            return False

        end_idx = text.find(end_marker)
        if end_idx != -1:
            buffer.append(text[:end_idx].encode())
            return True

        buffer.append(chunk)
        return False

    return _extract_html_section
