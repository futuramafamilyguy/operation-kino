import boto3


dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

cinema_table = dynamodb.create_table(
    TableName='Cinemas',
    KeySchema=[
        {'AttributeName': 'region', 'KeyType': 'HASH'},
        {'AttributeName': 'id', 'KeyType': 'RANGE'},
    ],
    AttributeDefinitions=[
        {'AttributeName': 'region', 'AttributeType': 'S'},
        {'AttributeName': 'id', 'AttributeType': 'S'},
    ],
    BillingMode='PAY_PER_REQUEST',
)

movie_table = dynamodb.create_table(
    TableName='Movies',
    KeySchema=[
        {'AttributeName': 'region', 'KeyType': 'HASH'},
        {'AttributeName': 'id', 'KeyType': 'RANGE'},
    ],
    AttributeDefinitions=[
        {'AttributeName': 'region', 'AttributeType': 'S'},
        {'AttributeName': 'id', 'AttributeType': 'S'},
    ],
    BillingMode='PAY_PER_REQUEST',
)
