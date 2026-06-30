# Cancel an Order
# The business rules allow a Customer to cancel an Order when it is in the PLACED status and is less than 10 minutes old.
#
# The following Python code defines a Lambda function that cancels an order. 
# It first checks the status and age of the order and raises a custom OrderStatusError exception 
# if the order's status is not PLACED or if the customer placed the order more than 10 minutes ago.
# 
# If the order meets the cancellation criteria, the function updates the order status to CANCELED. 
# The function returns the updated order information in it's response. 
# In case of an exception, the function returns an error response with the appropriate status code and error message.
#
# DynamoDB's ConditionExpression guarantee data integrity
#
# The ConditionExpression verifies the cancellation request meets the business requirements before cancelling an order.
# The order status must be PLACED and the orderTime within 10 minutes of the request.
#
# With ReturnValues="ALL_NEW", DynamoDB will also return the updated item. 
# By combining ConditionExpression and ReturnValues, you can choose specific conditions to atomically update both the 
# data store and current item in a single network request.

import simplejson as json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
from utils import get_order
from botocore.exceptions import ClientError
import time

# Custom Exception
class OrderStatusError(Exception):
    status_code = 400

    def __init__(self, message):
        super().__init__(message)

# Globals
orders_table = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')

def cancel_order(event):
    user_id = event ['requestContext']['authorizer']['claims']['sub']
    order_id = event['pathParameters']['orderId']
    current_time = time.time()

    try:
        table = dynamodb.Table(orders_table)
        response = table.update_item(
            Key={'userId': user_id, 'orderId': order_id},
            UpdateExpression = "set #data.#status = :new_status",
            ConditionExpression = "(#data.#status = :current_status) AND (#data.orderTime > :minOrderTime)",
            ExpressionAttributeNames = {
                "#data": "data",
                "#status": "status"
            },
            ExpressionAttributeValues = {
                ":current_status": "PLACED",
                ":minOrderTime": str(current_time - 600),
                ":new_status": "CANCELED"
            },
            ReturnValues = "ALL_NEW"
        )
    except ClientError as exc:
        if exc.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise OrderStatusError(f"Order {order_id} cannot be cancelled. Make sure the status of this order is PLACED and it was created less than 10 minutes ago.")
        else:
            raise OrderStatusError(f"Error Ocurred: {exc.response['Error']['Code']}: {exc.response['Error']['Message']}")
    except Exception as e:
        raise OrderStatusError(f"An unexpected error occurred: {e}")

    return response['Attributes']['data']

def lambda_handler(event, context):
    try:
        updated = cancel_order(event)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps(updated)
        }

        return response
    except OrderStatusError as oe:
        return {
            "statusCode": oe.status_code,
            "body": str(oe)
        }
    except Exception as err:
        raise