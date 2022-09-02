import re
from urllib import response
from chalice import Chalice, Response
import boto3
import botocore
from boto3.dynamodb.conditions import Key

app = Chalice(app_name='school-admission')

client = boto3.client('dynamodb')

@app.route('/student', methods=['POST'])
def add_student():
    data = app.current_request.json_body
    try:
        client.put_item(
            TableName='school-admission',
            Item={
            'email': {
                'S': data['email'],
            }
            },
            ConditionExpression='attribute_not_exists(email)'
        )
        response = Response(
            {
            'email': data['email']
            }
        )
        response.status_code = 201
        return response
    except botocore.exceptions.ClientError as e:
            response = Response(
                {
                   'message': str(e) 
                }
            )
            response.status_code = 400
            return response