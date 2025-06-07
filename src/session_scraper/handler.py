import asyncio
import logging
import os
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from models.region import Region
from repositories.cinema_repository import get_cinemas_by_region
from repositories.movie_repository import batch_insert_movies, delete_movies_by_region
from session_scraper.scraper import scrape_sessions

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    region_name = event.get('region_name')
    region_slug = event.get('region_slug')
    host = event.get('host')

    logger.info(f'operation kino phase 2: session scraper begin <{region_name}>')

    if not region_name or not region_slug or not host:
        return {'statusCode': 400, 'body': 'missing region or host'}

    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

        movies_table = dynamodb.Table('operationkino_movies')
        cinemas_table = dynamodb.Table('operationkino_cinemas')
        cinemas = get_cinemas_by_region(cinemas_table, region_name)
        if not cinemas:
            return {
                'statusCode': 500,
                'body': 'skip scraping movies cos no existing cinemas in database',
            }

        region = Region(name=region_name, slug=region_slug)
        movies = asyncio.run(scrape_sessions(region, host, cinemas))
        if not movies:
            return {
                'statusCode': 500,
                'body': 'failed to scrape movies',
            }

        delete_count = delete_movies_by_region(movies_table, region_name)
        logger.info(f'deleted {delete_count} movies <{region_name}>')
        insert_count = batch_insert_movies(movies_table, movies)
        logger.info(f'inserted {insert_count} movies <{region_name}>')

        logger.info(f'operation kino phase 2: session scraper complete <{region_name}>')
        return {'statusCode': 200}
    except (ClientError, BotoCoreError) as e:
        return {
            'statusCode': 500,
            'body': f'session scraping successful but encountered dynamodb error: {e}',
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'session scraper lambda encountered unexpected error: {e}',
        }
