import boto3
import time
import datetime
from datetime import datetime
import decimal
import yelpapi
from yelpapi import YelpAPI
from pprint import pprint

queue_url = 'https://sqs.us-east-1.amazonaws.com/402812318651/diningqueue'

def replace_decimals_emptystring(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = replace_decimals_emptystring(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = replace_decimals_emptystring(obj[k])
        return obj
    elif isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return int(obj)
    elif isinstance(obj, float):
        #print(obj)
        if obj % 1 == 0:
            return int(obj)
        else:
            return int(obj)
    elif isinstance(obj, str):
        
        if obj  == "":
            return 'no_val'
        else:
            return obj
    else:
        return obj

def lambda_handler(event, context):
    
    #sqs = boto3.client('sqs')
    sqs = boto3.client('sqs', region_name="us-east-1",
            aws_access_key_id='',
            aws_secret_access_key=''
        )
    sns = boto3.client('sns',
         aws_access_key_id="",
         aws_secret_access_key="",
         region_name="us-east-1"
    )
    response1 = sqs.receive_message(
    QueueUrl=queue_url,
    AttributeNames=[
        'SentTimestamp'
    ],
    MaxNumberOfMessages=1,
    MessageAttributeNames=[
        'All'
    ],
    VisibilityTimeout=0,
    WaitTimeSeconds=0
    )
    for message in response1['Messages']:
    # message = response1['Messages'][0]
        cuisine_type = message['MessageAttributes']['cuisine']['StringValue']
        location = message['MessageAttributes']['location']['StringValue']
        phone_number = message['MessageAttributes']['phone_number']['StringValue']
        dining_time = message['MessageAttributes']['dining_time']['StringValue']
        date = message['MessageAttributes']['date']['StringValue']
        no_of_people = message['MessageAttributes']['no_of_people']['StringValue']
        datetime_object = datetime.strptime(date + ' ' + dining_time, '%Y-%m-%d %H:%M')
        unixtime = time.mktime(datetime_object.timetuple())
   
        yelp_api = YelpAPI("vWTAQiV5BPys5WuKyKEZF44sNG0wXZ1hsikDqrccoupT6CWWeeRuUb2v6tGMu_qLljWiIPdCS5EjcId5p8lKf1drOQdZ1my017zx_LNthVx0_8ytvrFl6tapg-3kW3Yx")
        response = yelp_api.search_query(term= cuisine_type, location=location, open_at = int(unixtime), sort_by = 'rating', limit=10)
        #response = yelp_api.search_query(term= cuisine_type, location=location, open_now = True, sort_by='rating', limit=2)
        print(response)
        sms_msg = "Hello! Here are my "+cuisine_type+" restaurant suggestions for "+no_of_people+" people, for "+date+" at "+dining_time+": " + "\n"
        rest_msg = ""
        cnt = 0
        for x in response['businesses']:
	        print("%s at  %s" % (x['name'], x['location']['address1']))
	        cnt = cnt + 1
	        rest_msg = rest_msg + str(cnt) + ". " + x['name'] + " at "+ x['location']['address1']+". " + "\n"
        sms_msg = sms_msg + rest_msg +"Enjoy your meal!"
	    
	    # Send your sms message.
        sns.publish(
            PhoneNumber="+1"+phone_number,
            Message=sms_msg
        )     
	
        receipt_handle = message['ReceiptHandle']
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('Dinning_Suggestions_table')
        table.put_item(
            Item={
                'message_id': receipt_handle,
                'suggestions': replace_decimals_emptystring(response['businesses'])
                #'suggestions': response['businesses']
            }
        )    
        # Delete received message from queue
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )    
    return
