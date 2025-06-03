import asyncio
import time
import boto3
from models.region import Region
from repositories.cinema_repository import get_cinemas_by_region
from repositories.movie_repository import batch_insert_movies, delete_movies_by_region
from session_scraper.scraper import scrape_sessions


def lambda_handler(event, context):
    region_name = event.get('region_name')
    region_slug = event.get('region_slug')
    host = event.get('host')

    if not region_name or not region_slug or not host:
        return {'statusCode': 400, 'body': 'missing region or host'}

    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

    movies_table = dynamodb.Table('Movies')
    delete_movies_by_region(movies_table, region_name)

    cinemas_table = dynamodb.Table('Cinemas')
    cinemas = get_cinemas_by_region(cinemas_table, region_name)

    region = Region(name=region_name, slug=region_slug)
    movies = asyncio.run(scrape_sessions(region, host, cinemas))
    batch_insert_movies(movies_table, movies)

    return {'statusCode': 200}


def main():
    region_name = 'canterbury'
    region_slug = 'canterbury'
    host = 'https://flicks.com.au'

    if not region_name or not region_slug or not host:
        return {'statusCode': 400, 'body': 'missing region or host'}

    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

    movies_table = dynamodb.Table('Movies')
    delete_movies_by_region(movies_table, region_name)

    cinemas_table = dynamodb.Table('Cinemas')
    cinemas = get_cinemas_by_region(cinemas_table, region_name)

    region = Region(name=region_name, slug=region_slug)
    movies = asyncio.run(scrape_sessions(region, host, cinemas))
    batch_insert_movies(movies_table, movies)

    return {'statusCode': 200}


if __name__ == '__main__':
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    print(f'Execution time: {end - start:.4f} seconds')
