import boto3
from repositories.cinema_repository import batch_insert_cinemas, delete_cinemas_by_region
from cinema_scraper.scraper import scrape_cinemas
from models.region import Region


def lambda_handler(event, context):
    region_name = event.get('region_name')
    region_slug = event.get('region_slug')
    host = event.get('host')

    if not region_name or not region_slug or not host:
        return {'statusCode': 400, 'body': 'missing region or host'}
    
    dynamodb = boto3.resource("dynamodb", region_name='ap-southeast-2')
    cinemas_table = dynamodb.Table("Cinemas")

    region = Region(name=region_name, slug=region_slug)
    cinemas = scrape_cinemas(region, host)
    delete_cinemas_by_region(cinemas_table, region_name)
    batch_insert_cinemas(cinemas_table, cinemas)

    return {'statusCode': 200}
