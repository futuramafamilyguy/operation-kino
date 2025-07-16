from datetime import datetime
import json
import logging
import os
from zoneinfo import ZoneInfo

import boto3

from models.movie import Movie
from repositories.movie_repository import get_movies_by_region


LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

REGION_TIMEZONES = {
    'auckland': 'Pacific/Auckland',
    'canterbury': 'Pacific/Auckland',
    'brisbane-central': 'Australia/Brisbane',
}


def lambda_handler(event, context):
    region_code = event['pathParameters']['region_code']

    if not region_code:
        return {'statusCode': 400, 'body': 'missing region'}

    timezone = REGION_TIMEZONES.get(region_code.lower())

    try:
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

        movies_table = dynamodb.Table('operation-kino_movies')
        sessions = get_movies_by_region(movies_table, region_code, timezone)
        if not sessions:
            logger.warning(f'no sessions found for <{region_code}>')

        sessions_filtered = _filter_past_showtimes(sessions, timezone)

        sessions_json = [
            json.loads(session.model_dump_json(exclude={'id', 'region'}, by_alias=True))
            for session in sessions_filtered
        ]

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'sessions': sessions_json}),
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'get sessions lambda encountered unexpected error: {e}',
        }


def _filter_past_showtimes(sessions: list[Movie], timezone: str):
    now = datetime.now(ZoneInfo(timezone)).date()

    def filter_showtimes(session: Movie):
        session.showtimes = [
            st for st in session.showtimes if datetime.fromisoformat(st).date() >= now
        ]
        return session

    return list(map(filter_showtimes, sessions))
