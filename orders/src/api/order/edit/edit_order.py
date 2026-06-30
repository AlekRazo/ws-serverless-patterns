# Edit an Order
# Customers can modify an Order before the restaurant has set the status to ACKNOWLEDGED.
# 
# The code defines two functions lambda_handler and edit_order. 
# The lambda_handler() is the entry point for the Lambda function. 
# It calls edit_order() which creates an updated order to store in the database. 
# The function returns the updated order information the customer.
#
# Remember the Lambda layer you created to get orders? You will include that layer again to reuse the get_order() function.
#
# Using DynamoDB’s ConditionExpression for safe and cost-effective operations
#
# With ConditionExpression in DynamoDB, you can specify certain conditions exist before updating, inserting, or deleting an item. 
# The ConditionExpression in our example ensures the PutItem operation runs only when the existing record values for orderId and 
# userId match the order_id and user_id parameters and the status is PLACED.
#
# You use ConditionExpressions to avoid read operations before a write operation (ex. GetItem then PutItem). 
# Use this approach when you need to update a record only under certain conditions, such as order_id exists. 
# In this example, ConditionExpression combines the conditional check and write operation into one atomic operation, 
# reducing read operations and potentially reducing cost.
#
# Additionally, atomic operations can reduce the chances of race conditions 
# — multiple clients trying to update the same item simultaneously - which further improves your application reliability!
import simplejson as json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from decimal import Decimal
from utils import get_order

#globals
order_table = os.getenv('TABLE_NAME')
dynamodb = boto3.resource('dynamodb')

def edit_order(event):
    user_id = event['requestContext']['authorizer']['claims']['sub']
    order_id = event['pathParameters']['orderId']
    new_data = json.loads(event['body'], parse_float=Decimal)
    new_data['userId'] = user_id
    new_data['orderId'] = order_id

    ddb_item = {
                'orderId': order_id,
                'userId': user_id,
                'data': new_data
            }
    
    ddb_item = json.loads(json.dumps(ddb_item), parse_float=Decimal)
    table = dynamodb.Table(order_table)

    try:
        table.put_item(
            Item=ddb_item, 
            ConditionExpression="attribute_exists(orderId) AND attribute_exists(userId) AND #data.#status = :status", 
            ExpressionAttributeNames={
                "#data": "data",
                "#status": "status"
            },
            ExpressionAttributeValues={
                ":status": "PLACED"
            },
            ReturnValuesOnConditionCheckFailure="ALL_OLD"
        )
    except ClientError as exc:
        if exc.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise Exception(f"Cannot edit Order {order_id}. Please check if the order exists and the status is PLACED.")
        else:
            raise Exception(f"Error occurred: {exc.response['Error']['Code']}: {exc.response['Error']['Message']}")
    except Exception as e:
        raise Exception(f"An unexpected error ocurred: {e}")

    return get_order(user_id, order_id)

def lambda_handler(event, context):
    try:
        updated = edit_order(event)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps(updated)
        }

        return response
    except Exception as err:
        raise Exception(str(err))
