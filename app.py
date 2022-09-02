from email.header import Header
import json
from urllib import response
from chalice import Chalice, Response 
import boto3
import botocore
import requests
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

app = Chalice(app_name='school-admission')
client = boto3.client('dynamodb')
secretsclient = boto3.client('secretsmanager')

def get_secret():
    secret_name = "StudentAdmission"
    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = secretsclient.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS key.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return secret
        else:
            print("binary")
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return decoded_binary_secret
            

def generate_token(publickey,privatekey):
    url = "https://api.helloworks.com/v3/token/"+publickey
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer "+privatekey
    }
    response = requests.get(url, headers=headers)
    return response.text

def create_workflow_instance(token,workflowid,email,name):
    url = "https://api.helloworks.com/v3/workflow_instances"
    payload = "workflow_id="+workflowid+"&participants[participant1_SD1hLS][type]=email&participants[participant1_SD1hLS][value]="+email+"&participants[participant1_SD1hLS][full_name]="+name 
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Bearer "+token
    }
    response = requests.post(url, data=payload, headers=headers)
    return response.text

@app.route('/student', methods=['POST'])
def add_student():
    data = app.current_request.json_body
    try:
        secret_string =json.loads(get_secret())
        publickey = secret_string["publickey"]
        privatekey = secret_string["privatekey"]
        workflowid = secret_string["workflowid"]
        token = json.loads(generate_token(publickey,privatekey))["data"]["token"]
        workflow_instance_id = json.loads(create_workflow_instance(token,workflowid,data["email"],data["fullname"]))["data"]["id"]
        client.put_item(
            TableName='school-admission',
            Item={
            'email': {
                'S': data['email'],
            },
            'fullname': {
                'S': data['fullname'],
            },
            'workflow_instance_id': {
                'S': workflow_instance_id,
            },
            },
            ConditionExpression='attribute_not_exists(email)'
        )
        response = Response(
            {
            'email': data['email'],
            'fullname': data['fullname'],
            'workflow_instance_id': workflow_instance_id
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