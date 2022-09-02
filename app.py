from urllib import response
from chalice import Chalice, Response
import boto3
from boto3.dynamodb.conditions import Key

app = Chalice(app_name='school-admission')


def get_app_db():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table('school-admission')
    return table

@app.route('/student', methods=['POST'])
def add_student():
    data = app.current_request.json_body
    try:
        get_app_db().put_item(Item={
            'email': data['email'],
        })
        response = Response(
            {
            'email': data['email']
            }
        )
        response.status_code = 201
        return response
    except Exception as e:
        print("Reached Exception")
        return {'message': str(e)}