import logging
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, BotoCoreError

from models.movie import Movie

logger = logging.getLogger(__name__)


def get_movies_by_region(table, region: str) -> list[Movie]:
    items = _query_movie_items_by_region(table, region)
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


def delete_movies_by_region(table, region: str) -> int:
    items = _query_movie_items_by_region(table, region)
    delete_count = 0
    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={'region': item['region'], 'id': item['id']})
                delete_count += 1
        return delete_count
    except (ClientError, BotoCoreError) as e:
        logger.error(f'dynamodb error encountered while deleting movies: {e}')
        raise


def _query_movie_items_by_region(table, region: str) -> list[dict]:
    try:
        response = table.query(KeyConditionExpression=Key('region').eq(region))
        return response.get('Items', [])
    except (ClientError, BotoCoreError) as e:
        logger.error(f'dynamodb error encountered while fetching movies: {e}')
        raise
