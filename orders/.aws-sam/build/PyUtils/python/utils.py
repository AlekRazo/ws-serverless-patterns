# The shared layer code imports the Key class and boto3 module to connect and query the database table. 
# The get_order function uses the two parameters: user_id and order_id to create a KeyConditionExpression 
# for finding the order in the database. Although that should find a singular result, the code loops 
# through all returned Items in the database response and returns the first item.
#
# Several of the single-purpose API functions use this code, 
# so the next step is to build a layer that contains it instead of duplicating it.
from boto3.dynamodb.conditions import Key
import boto3
import os

orders_table = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')

def get_order(user_id, order_id):
    table = dynamodb.Table(orders_table)
    response = table.query(KeyConditionExpression=(Key('userId').eq(user_id) & Key('orderId').eq(order_id)))
    user_orders = []

    for item in response['Items']:
        user_orders.append(item['data'])

    return user_orders[0]