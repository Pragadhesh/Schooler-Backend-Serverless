from email.header import Header
import json
from logging import exception
from logging.handlers import TimedRotatingFileHandler
import re
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
    return response

def get_workflow_instance(token,workflow_instance_id):
    url = "https://api.helloworks.com/v3/workflow_instances/"+workflow_instance_id
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Bearer "+token
    }
    response = requests.get(url, headers=headers)
    return response.text   

def send_applicant_reminder(token,workflow_instance_id):
    url = "https://api.helloworks.com/v3/workflow_instances/"+workflow_instance_id+"/remind"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer "+token
    }
    response = requests.put(url, headers=headers)
    return response


def delete_student_application(token,workflow_instance_id):
    cancel_url ="https://api.helloworks.com/v3/workflow_instances/"+workflow_instance_id+"/cancel"
    url = "https://api.helloworks.com/v3/workflow_instances/"+workflow_instance_id
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer "+token
    }
    cancel_response = requests.put(cancel_url,headers=headers)
    if cancel_response.status_code == 200:
        response = requests.delete(url, headers=headers)
        return response
    else:
        return cancel_response

def get_document_link(token,workflow_instance_id):
    url = "https://api.helloworks.com/v3/workflow_instances/"+workflow_instance_id+"/document_link"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer "+token
    }
    response = requests.get(url, headers=headers)
    return response

def find_student_sex(student_sex):
    if student_sex == "choice_7XwZpL":
        return "Male"
    else:
        return "Female"

def find_student_race(student_race):
    if student_race == "choice_BbFybf":
        return "Asian"
    elif student_race == "choice_zyWylc":
        return "White"
    elif student_race == "choice_UhAVoy":
        return "African"
    elif student_race == "choice_vsTLl7":
        return "Hispanic"
    else:
        return "Pacific Islander"
 
def find_current_grade(grade):
    if grade == "choice_9SohQh":
        return "Kinder Garden"
    elif grade == "choice_csi2Af":
        return "1st Grade"
    elif grade == "choice_NQssJW":
        return "2nd Grade"
    elif grade == "choice_60JoKY":
        return "3rd Grade"
    elif grade == "choice_V8n3DM":
        return "4th Grade"
    elif grade == "choice_kJYpaB":
        return "5th Grade"
    elif grade == "choice_8cR7Mw":
        return "6th Grade"
    elif grade == "choice_DKoVwm":
        return "7th Grade"
    elif grade == "choice_I3tsLk":
        return "8th Grade"
    elif grade == "choice_gRsFHX":
        return "9th Grade"
    elif grade == "choice_EEmLEr":
        return "10th Grade"
    elif grade == "choice_2HnXTY":
        return "11th Grade"
    else:
        return "12th Grade"

def find_applied_grade(grade):
    if grade == "choice_6vcvRO":
        return "Kinder Garden"
    elif grade == "choice_eDsAak":
        return "1st Grade"
    elif grade == "choice_4QswBb":
        return "2nd Grade"  
    elif grade == "choice_Fhnfky":
        return "3rd Grade"
    elif grade == "choice_iP362l":
        return "4th Grade"
    elif grade == "choice_TXSHwR":
        return "5th Grade"
    elif grade == "choice_1NqUtB":
        return "6th Grade"
    elif grade == "choice_DB9jV5":
        return "7th Grade"
    elif grade == "choice_aaIm5N":
        return "8th Grade"
    elif grade == "choice_tc52RZ":
        return "9th Grade"
    elif grade == "choice_gGwTQM":
        return "10th Grade"
    elif grade == "choice_mhzyCA":
        return "11th Grade"
    else:
        return "12th Grade"
    
def find_parent1_relationship(parent1_relationship):
    if parent1_relationship == "choice_0A5cqt":
        return "Father"
    elif parent1_relationship == "choice_n5OM2W":
        return "Mother"
    else:
        return "Guardian"
    
def find_parent2_relationship(parent2_relationship):
    if parent2_relationship == "choice_GI2xoc":
        return "Father"
    elif parent2_relationship == "choice_dCPoOD":
        return "Mother"
    else:
        return "Guardian"


@app.route('/student', methods=['POST'],cors=True)
def add_student():
    data = app.current_request.json_body
    try:
        secret_string =json.loads(get_secret())
        publickey = secret_string["publickey"]
        privatekey = secret_string["privatekey"]
        workflowid = secret_string["workflowid"]
        token = json.loads(generate_token(publickey,privatekey))["data"]["token"]
        result = create_workflow_instance(token,workflowid,data["email"],data["fullname"])
        if result.status_code == 200:
            workflow_instance_id = json.loads(result.text)["data"]["id"]
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
        else:
            raise Exception("Error in creating workflow instance")
    except:
            response = Response(
                {
                   'message': "Error in creating workflow instance" 
                }
            )
            response.status_code = 400
            return response

@app.route('/student', methods=['GET'],cors=True)
def get_students():
    try:
        response = client.scan(
            TableName='school-admission',
            AttributesToGet=[
                    'email',
                    'fullname',
                    'workflow_instance_id'
                        ]
                    )
        workflow_instances = response['Items']
        secret_string =json.loads(get_secret())
        publickey = secret_string["publickey"]
        privatekey = secret_string["privatekey"]
        workflowid = secret_string["workflowid"]
        token = json.loads(generate_token(publickey,privatekey))["data"]["token"]
        active = []
        completed = {}
        for instance in workflow_instances:
            workflow_instance_id = instance['workflow_instance_id']['S']
            data = get_workflow_instance(token,workflow_instance_id)
            result = json.loads(data)
            if result['data']['status'] == "active":
                active.append(
                    {
                       "workflow_instance_id": workflow_instance_id,
                        "status": "active",
                        "fullname": instance['fullname']['S'],
                        "email": instance['email']['S'],
                    }
                )
            elif result['data']['status'] == "completed":
                    grade = find_applied_grade(result['data']['data']['form_r9GXB5']['field_GQtdyP'][0])
                    email =  instance['email']['S'] 
                    if grade in completed:
                        student_info = completed.get(grade)               
                        student_info.append(
                            { email:
                                    {
                            "workflow_instance_id": workflow_instance_id,
                            "status": "completed",
                            "fullname": instance['fullname']['S'],
                            "email": instance['email']['S'],
                            "student_firstname": result['data']['data']['form_r9GXB5']['field_0K01Wy'],
                            "student_lastname": result['data']['data']['form_r9GXB5']['field_7368pV'],
                            "student_dob": result['data']['data']['form_r9GXB5']['field_emZSLZ'],
                            "student_phone": result['data']['data']['form_r9GXB5']['field_p2ukp6'],
                            "student_address": result['data']['data']['form_r9GXB5']['field_zHBA5s'].replace('\n',' '),
                            "student_sex": find_student_sex(result['data']['data']['form_r9GXB5']['field_UVdZWk'][0]),
                            "student_race": find_student_race(result['data']['data']['form_r9GXB5']['field_EsVhlD'][0]),
                            "student_nationality": result['data']['data']['form_r9GXB5']['field_j3e3QU'],
                            "student_religion": result['data']['data']['form_r9GXB5']['field_FAdfd2'],
                            "student_current_grade_level": find_current_grade(result['data']['data']['form_r9GXB5']['field_wrpwlS'][0]),
                            "student_grade_level_applied": find_applied_grade(result['data']['data']['form_r9GXB5']['field_GQtdyP'][0]),
                            "parent1_firstname": result['data']['data']['form_r9GXB5']['field_arLmAU'],
                            "parent1_lastname": result['data']['data']['form_r9GXB5']['field_m2hchx'],
                            "parent1_relationship": find_parent1_relationship(result['data']['data']['form_r9GXB5']['field_rtu4JU'][0]),
                            "parent1_phone": result['data']['data']['form_r9GXB5']['field_EMvAFf'],
                            "parent1_email": result['data']['data']['form_r9GXB5']['field_5oIoGP'],
                            "parent1_address": result['data']['data']['form_r9GXB5']['field_8eYtwV'].replace('\n',' '),
                            "parent2_firstname": result['data']['data']['form_r9GXB5']['field_0Mb1X8'],
                            "parent2_lastname": result['data']['data']['form_r9GXB5']['field_KyKJLx'],
                            "parent2_relationship": find_parent2_relationship(result['data']['data']['form_r9GXB5']['field_acDFTL'][0]),
                            "parent2_phone": result['data']['data']['form_r9GXB5']['field_HDvxMm'],
                            "parent2_email": result['data']['data']['form_r9GXB5']['field_LR4vlx'],
                            "parent2_address": result['data']['data']['form_r9GXB5']['field_bcWQpe'].replace('\n',' ') 
                        } 
                        }  
                        )      
                    else:
                        student_info = [
                            { email:
                                    {
                            "workflow_instance_id": workflow_instance_id,
                            "status": "completed",
                            "fullname": instance['fullname']['S'],
                            "email": instance['email']['S'],
                            "student_firstname": result['data']['data']['form_r9GXB5']['field_0K01Wy'],
                            "student_lastname": result['data']['data']['form_r9GXB5']['field_7368pV'],
                            "student_dob": result['data']['data']['form_r9GXB5']['field_emZSLZ'],
                            "student_phone": result['data']['data']['form_r9GXB5']['field_p2ukp6'],
                            "student_address": result['data']['data']['form_r9GXB5']['field_zHBA5s'].replace('\n',' '),
                            "student_sex": find_student_sex(result['data']['data']['form_r9GXB5']['field_UVdZWk'][0]),
                            "student_race": find_student_race(result['data']['data']['form_r9GXB5']['field_EsVhlD'][0]),
                            "student_nationality": result['data']['data']['form_r9GXB5']['field_j3e3QU'],
                            "student_religion": result['data']['data']['form_r9GXB5']['field_FAdfd2'],
                            "student_current_grade_level": find_current_grade(result['data']['data']['form_r9GXB5']['field_wrpwlS'][0]),
                            "student_grade_level_applied": find_applied_grade(result['data']['data']['form_r9GXB5']['field_GQtdyP'][0]),
                            "parent1_firstname": result['data']['data']['form_r9GXB5']['field_arLmAU'],
                            "parent1_lastname": result['data']['data']['form_r9GXB5']['field_m2hchx'],
                            "parent1_relationship": find_parent1_relationship(result['data']['data']['form_r9GXB5']['field_rtu4JU'][0]),
                            "parent1_phone": result['data']['data']['form_r9GXB5']['field_EMvAFf'],
                            "parent1_email": result['data']['data']['form_r9GXB5']['field_5oIoGP'],
                            "parent1_address": result['data']['data']['form_r9GXB5']['field_8eYtwV'].replace('\n',' '),
                            "parent2_firstname": result['data']['data']['form_r9GXB5']['field_0Mb1X8'],
                            "parent2_lastname": result['data']['data']['form_r9GXB5']['field_KyKJLx'],
                            "parent2_relationship": find_parent2_relationship(result['data']['data']['form_r9GXB5']['field_acDFTL'][0]),
                            "parent2_phone": result['data']['data']['form_r9GXB5']['field_HDvxMm'],
                            "parent2_email": result['data']['data']['form_r9GXB5']['field_LR4vlx'],
                            "parent2_address": result['data']['data']['form_r9GXB5']['field_bcWQpe'].replace('\n',' ') 
                        } 
                        }  
                        ]
                    completed[grade] = student_info              
        student_information = {
            'active': active,
            'completed': completed
        }
        return json.dumps(student_information)
    except botocore.exceptions.ClientError as e:
            response = Response(
                {
                   'message': str(e) 
                }
            )
            response.status_code = 400
            return response


@app.route('/reminder',methods=['PUT'],cors=True)
def send_reminder():
    data = app.current_request.json_body
    try:    
        secret_string =json.loads(get_secret())
        publickey = secret_string["publickey"]
        privatekey = secret_string["privatekey"]
        workflow_instance_id = data["workflow_instance_id"]
        token = json.loads(generate_token(publickey,privatekey))["data"]["token"]
        result = send_applicant_reminder(token,workflow_instance_id)
        if result.status_code == 200:
            response = Response(
                {
                   'message': result.text
                }
            )
            response.status_code = 200
            return response
        elif json.loads(result.text)["error"] == "Not enough time has gone by":
            response = Response(
                {
                   'message': "Application sent recently.Please try again later."
                }
            )
            response.status_code = 200
            return response
        else:
            raise Exception("Reminder not sent")
    except:
            response = Response(
                {
                   'message': "Issue in sending the reminder"
                }
            )
            response.status_code = 400
            return response
        
@app.route('/student', methods=['PUT'],cors=True)
def delete_workflow_instance():
    data = app.current_request.json_body
    print(data)
    try:    
        secret_string =json.loads(get_secret())
        publickey = secret_string["publickey"]
        privatekey = secret_string["privatekey"]
        workflow_instance_id = data["workflow_instance_id"]
        token = json.loads(generate_token(publickey,privatekey))["data"]["token"]
        result = delete_student_application(token,workflow_instance_id)
        if result.status_code == 200:
            client.delete_item(
                TableName='school-admission',
                Key={
                'email': {
                    'S': data["email"],
                }
                }
            )
            response = Response(
                {
                   'message': "Application deleted successfully"
                }
            )
            response.status_code = 200
            return response
        else:
            raise Exception("Issue in deleting the application")
    except:
            response = Response(
                {
                   'message': "Issue in deleting the application"
                }
            )
            response.status_code = 400
            return response
 
        
@app.route('/documents', methods=['GET'],cors=True)
def get_documents():
    data = app.current_request.json_body
    try:    
        secret_string =json.loads(get_secret())
        publickey = secret_string["publickey"]
        privatekey = secret_string["privatekey"]
        token = json.loads(generate_token(publickey,privatekey))["data"]["token"]
        document_link = get_document_link(token,data["workflow_instance_id"])
        if document_link.status_code == 200:
            return json.loads(document_link.text)['data']
        else:
            raise Exception("Error in fetching the documents")
    except:
            response = Response(
                {
                   'message': "Error in fetching the documents"
                }
            )
            response.status_code = 400
            return response
        
@app.route('/test',methods=['GET'])
def get_workflow_instance_details():
    data = app.current_request.json_body
    secret_string =json.loads(get_secret())
    publickey = secret_string["publickey"]
    privatekey = secret_string["privatekey"]
    token = json.loads(generate_token(publickey,privatekey))["data"]["token"]
    resp = get_workflow_instance(token,data["workflow_instance_id"])
    result = json.loads(resp)
    return resp