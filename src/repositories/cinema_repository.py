import logging
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, BotoCoreError

from models.cinema import Cinema

logger = logging.getLogger(__name__)


def get_cinemas_by_region(table, region_code: str) -> list[Cinema]:
    items = _query_cinema_items_by_region(table, region_code)
    return [Cinema(**item) for item in items]


def batch_insert_cinemas(table, cinemas: list[Cinema]) -> int:
    insert_count = 0
    try:
        with table.batch_writer() as batch:
            for cinema in cinemas:
                item = cinema.model_dump()
                if item.get('homepage_url') is not None:
                    item['homepage_url'] = str(item['homepage_url'])
                batch.put_item(Item=item)
                insert_count += 1
        return insert_count
    except (ClientError, BotoCoreError) as e:
        logger.error(f'dynamodb error encountered while inserting cinemas: {e}')
        raise


def delete_cinemas_by_region(table, region_code: str) -> int:
    items = _query_cinema_items_by_region(table, region_code)
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
        logger.error(f'dynamodb error encountered while deleting cinemas: {e}')
        raise


def _query_cinema_items_by_region(table, region_code: str) -> list[dict]:
    try:
        response = table.query(
            KeyConditionExpression=Key('region_code').eq(region_code)
        )
        return response.get('Items', [])
    except (ClientError, BotoCoreError) as e:
        logger.error(f'dynamodb error encountered while fetching cinemas: {e}')
        raise
