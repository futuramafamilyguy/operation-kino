from boto3.dynamodb.conditions import Key

from models import Cinema


def get_cinemas_by_region(table, region: str) -> list[Cinema]:
    items = _query_cinema_items_by_region(table, region)
    return [Cinema(**item) for item in items]

def batch_insert_cinemas(table, cinemas: list[Cinema]) -> None:
    with table.batch_writer() as batch:
        for cinema in cinemas:
            item = cinema.model_dump()
            if item.get("homepage_url") is not None:
                item["homepage_url"] = str(item["homepage_url"])
            batch.put_item(Item=item)

def delete_cinemas_by_region(table, region: str) -> None:
    items = _query_cinema_items_by_region(table, region)
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={'region': item['region'], 'id': item['id']})

def _query_cinema_items_by_region(table, region: str) -> list[dict]:
    response = table.query(
        KeyConditionExpression=Key('region').eq(region)
    )
    return response.get('Items', [])
