import asyncio
import logging
import os
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from repositories.cinema_repository import (
    batch_insert_cinemas,
    delete_cinemas_by_region,
)
from cinema_scraper.scraper import scrape_cinemas
from models.region import Region

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    region_name = event.get('region_name')
    region_slug = event.get('region_slug')
    host = event.get('host')

    if not region_name or not region_slug or not host:
        return {'statusCode': 400, 'body': 'missing region or host'}

    logger.info(
        f'operation kino phase 1: cinema scraper begin <{region_name}>. for king and country'
    )

    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
        cinemas_table = dynamodb.Table('Cinemas')

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
                'body': f'cinema scraping successful but encountered dynamodb error: {e}',
            }

        logger.info(f'operation kino phase 1: cinema scraper complete ({region_name})')

        return {'statusCode': 200}
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'cinema scraper lambda encountered unexpected error: {e}',
        }
