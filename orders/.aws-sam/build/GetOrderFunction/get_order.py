# Get Order with layer
# In this step, your Lambda function will retrieve an order with the get_order() method from the pyutils Lambda layer you 
# created in the previous step.
#
# The Lambda handler extracts values from the event:
#
# user_id from the authorizer token : event['requestContext']['authorizer']['claims']['sub']
# order_id from pathParameters.
# The handler calls get_order() from pyutils to retrieve the order details from the DynamoDB table in the TABLE_NAME 
# environment variable. If the query is successful, the function returns as JSON response with the order information 
# and a success status code.
#
# The Lambda handler is a great place to do input retrieval and validation. 
# You keep business logic isolated, testable, and reusable in the layer.

import simplejson as json
from utils import get_order

def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['claims']['sub']
    order_id = event['pathParameters']['orderId']

    try:
        orders = get_order(user_id, order_id)
        response = {
            "statusCode": 200,
            "headers": {},
            "body": json.dumps(orders)
        }

        return response
    except Exception as err:
        raise