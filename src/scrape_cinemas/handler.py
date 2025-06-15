import asyncio
import logging
import os
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from repositories.cinema_repository import (
    batch_insert_cinemas,
    delete_cinemas_by_region,
)
from scrape_cinemas.scraper import scrape_cinemas
from models.region import Region

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

    logger.info(
        f'operation kino phase 1: scrape cinemas begin <{region_name}>. for king and country'
    )

    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
        cinemas_table = dynamodb.Table('operation-kino_cinemas')

        region = Region(name=region_name, slug=region_slug)
        cinemas = asyncio.run(scrape_cinemas(region, host))
        if not cinemas:
            return {
                'statusCode': 500,
                'body': 'failed to scrape cinemas',
            }

        try:
            delete_count = delete_cinemas_by_region(cinemas_table, region_name)
            logger.info(f'deleted {delete_count} cinemas <{region_name}>')
            insert_count = batch_insert_cinemas(cinemas_table, cinemas)
            logger.info(f'inserted {insert_count} cinemas <{region_name}>')
        except (ClientError, BotoCoreError) as e:
            return {
                'statusCode': 500,
                'body': f'scrape cinemas successful but encountered dynamodb error: {e}',
            }

        logger.info(f'operation kino phase 1: scrape cinemas complete <{region_name}>')

        return {'statusCode': 200}
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'scrape cinemas lambda encountered unexpected error: {e}',
        }
