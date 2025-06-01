from boto3.dynamodb.conditions import Key

from models.movie import Movie


def get_movies_by_region(table, region: str) -> list[Movie]:
    items = _query_movie_items_by_region(table, region)
    return [Movie(**item) for item in items]


def batch_insert_movies(table, movies: list[Movie]) -> None:
    with table.batch_writer() as batch:
        for movie in movies:
            item = movie.model_dump()
            if item.get('image_url') is not None:
                item['image_url'] = str(item['image_url'])
            batch.put_item(Item=item)


def delete_movies_by_region(table, region: str) -> None:
    items = _query_movie_items_by_region(table, region)
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={'region': item['region'], 'id': item['id']})


def _query_movie_items_by_region(table, region: str) -> list[dict]:
    response = table.query(KeyConditionExpression=Key('region').eq(region))
    return response.get('Items', [])
