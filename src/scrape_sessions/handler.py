import asyncio
import logging
import os
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from models.region import Region
from repositories.cinema_repository import get_cinemas_by_region
from repositories.movie_repository import batch_insert_movies, delete_movies_by_region
from scrape_sessions.scraper import scrape_sessions

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    region_name = event.get('region_name')
    region_slug = event.get('region_slug')
    country_code = event.get('country_code')
    if not region_name or not region_slug or not country_code:
        return {'statusCode': 400, 'body': 'missing region info'}

    host = os.getenv(f'SCRAPE_HOST_{country_code}').upper()
    if not host:
        return {
            'statusCode': 400,
            'body': f'country code not supported: <{country_code}>',
        }

    logger.info(f'operation kino phase 2: scrape sessions begin <{region_slug}>')

    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

        movies_table = dynamodb.Table('operation-kino_movies')
        cinemas_table = dynamodb.Table('operation-kino_cinemas')
        cinemas = get_cinemas_by_region(cinemas_table, region_slug)
        if not cinemas:
            return {
                'statusCode': 500,
                'body': 'skip scrape sessions cos no existing cinemas in database',
            }

        region = Region(name=region_name, slug=region_slug)
        movies = asyncio.run(scrape_sessions(region, host, cinemas))
        if not movies:
            return {
                'statusCode': 500,
                'body': 'failed to scrape sessions',
            }

        delete_count = delete_movies_by_region(movies_table, region_slug)
        logger.info(f'deleted {delete_count} movies <{region_slug}>')
        insert_count = batch_insert_movies(movies_table, movies)
        logger.info(f'inserted {insert_count} movies <{region_slug}>')

        logger.info(f'operation kino phase 2: scrape sessions complete <{region_slug}>')
        return {'statusCode': 200}
    except (ClientError, BotoCoreError) as e:
        return {
            'statusCode': 500,
            'body': f'scrape sessions successful but encountered dynamodb error: {e}',
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'scrape sessions lambda encountered unexpected error: {e}',
        }
