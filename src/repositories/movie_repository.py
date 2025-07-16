from datetime import datetime
import logging
from typing import Optional
from zoneinfo import ZoneInfo
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, BotoCoreError

from models.movie import Movie

logger = logging.getLogger(__name__)


def get_movies_by_region(table, region_code: str, timezone: str) -> list[Movie]:
    items = _query_movie_items_by_region(
        table, region_code, apply_date_filter=True, timezone=timezone
    )
    return [Movie(**item) for item in items]


def batch_insert_movies(table, movies: list[Movie]) -> None:
    insert_count = 0
    try:
        with table.batch_writer() as batch:
            for movie in movies:
                item = movie.model_dump()
                if item.get('image_url') is not None:
                    item['image_url'] = str(item['image_url'])
                batch.put_item(Item=item)
                insert_count += 1
        return insert_count
    except (ClientError, BotoCoreError) as e:
        logger.error(f'dynamodb error encountered while inserting movies: {e}')
        raise


def delete_movies_by_region(table, region_code: str) -> int:
    items = _query_movie_items_by_region(table, region_code)
    delete_count = 0
    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={'region_code': item['region_code'], 'id': item['id']}
                )
                delete_count += 1
        return delete_count
    except (ClientError, BotoCoreError) as e:
        logger.error(f'dynamodb error encountered while deleting movies: {e}')
        raise


def _query_movie_items_by_region(
    table,
    region_code: str,
    apply_date_filter: bool = False,
    timezone: Optional[str] = None,
) -> list[dict]:
    try:
        key_condition = Key('region_code').eq(region_code)
        if apply_date_filter:
            key_condition &= Key('last_showtime').gte(
                datetime.now(ZoneInfo(timezone)).date().isoformat()
            )
            response = table.query(
                IndexName='region_by_last_showtime',
                KeyConditionExpression=key_condition,
            )
        else:
            response = table.query(
                KeyConditionExpression=key_condition,
            )
        return response.get('Items', [])
    except (ClientError, BotoCoreError) as e:
        logger.error(f'dynamodb error encountered while fetching movies: {e}')
        raise
