# Create Orders service
# Before you can explore idempotency to reliably send orders to restaurants, you need an Orders microservice, with the following components:
# - Orders database table
# - Function(s) to create, read, update, and delete Orders
# - API to connect requests to your Orders function(s)
#
# This trio of resources may sound familiar from the Users module. 
# To get started faster, we've provided database, API, and function resources for the AWS SAM template.
#
# After importing standard libraries, the code uses the os module to load the orders_table environment variable, 
# initializes a DynamoDB resource object with boto3, uses decimal to parse numeric values from the input, 
# and gets the current timestamp in UTC format with datetime. Note the uuid generates unique identifiers used later.
#
# When adding an order to the database, the userId from the authentication token identifies the record, 
# and the function adds a timestamp to record the order placement time.
#
# Lambda function with two functions?
# You may notice this Python Lambda function actually contains two functions: add_order and lambda_handler. 
# When we talk about a Lambda function, that means the code has a lambda_handler() entry point, but you may create 
# as many internal functions, or methods, as necessary to process your workloads.
#
# lambda_handler function is the entry point for the Lambda function. 
# It invokes the add_order function with the input event as a parameter, and constructs an HTTP response object 
# containing the returned order_detail. If an error occurs, it raises the exception.
#
# add_order function takes event and context input parameters. 
# It loads the event body as a JSON object and extracts various attributes from it, 
# including: restaurantId, totalAmount, orderItems, userId, orderTime, and orderId. 
# The function constructs an item with these attributes, then stores the item in the table specified by the orders_table
# environment variable, and finally returns a detail object with the new orderId and status code.

import os
import boto3
from decimal import Decimal
import json
import uuid
from datetime import datetime
# Idempotency
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig, DynamoDBPersistenceLayer, idempotent_function
)
# Logging
from aws_lambda_powertools import Logger, Metrics
# Metrics
from aws_lambda_powertools.metrics import MetricUnit

# Globals
logger = Logger() # Logger
metrics = Metrics() # Metrics
orders_table = os.getenv('TABLE_NAME') # Gotten from template.yaml -> Resources:AddOrderFunction:Properties:Environment:Variables:
idempotency_table = os.getenv('IDEMPOTENCY_TABLE_NAME') # Idempotency
dynamodb = boto3.resource('dynamodb')
# Idempotency
persistence_layer = DynamoDBPersistenceLayer(table_name=idempotency_table)
idempotency_config = IdempotencyConfig(event_key_jmespath="powertools_json(body).orderId")

@idempotent_function(data_keyword_argument="event", config=idempotency_config, persistence_store=persistence_layer)
def add_order(event: dict):
    # Logger
    logger.info("Adding a new order")
    detail = json.loads(event['body'])
    logger.info({"operation": "add_order", "order_details": detail})
    restaurant_id = detail['restaurantId']
    total_amount = detail['totalAmount']
    order_items = detail['orderItems']
    user_id = event['requestContext']['authorizer']['claims']['sub']
    order_time = datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ')
    order_id = detail['orderId']

    ddb_item = {
        'orderId': order_id,
        'userId': user_id,
        'data': {
            'orderId': order_id,
            'userId': user_id,
            'restaurantId': restaurant_id,
            'totalAmount': total_amount,
            'orderItems': order_items,
            'status': 'PLACED',
            'orderTime': order_time
        }
    }

    ddb_item = json.loads(json.dumps(ddb_item), parse_float=Decimal)

    table = dynamodb.Table(orders_table)
    # We must use conditional expression, otherwise put_item will allways replace the original order and will never fail
    table.put_item(Item = ddb_item, ConditionExpression='attribute_not_exists(orderId) AND attribute_not_exists(userId)')

    detail['orderId'] = order_id
    detail['orderTime'] = order_time
    detail['status'] = 'PLACED'

    logger.info(f"new Order with ID {order_id} saved")
    metrics.add_metric(name="SuccessfulOrder", unit=MetricUnit.Count, value=1)
    metrics.add_metric(name="OrderTotal", unit=MetricUnit.Count, value=total_amount)

    return detail

@metrics.log_metrics
@logger.inject_lambda_context
def lambda_handler(event, context:LambdaContext):
    # Idempotency
    idempotency_config.register_lambda_context(context)

    try:
        order_detail = add_order(event=event)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps(order_detail)
        }

        return response
    except Exception as err:
        raise
