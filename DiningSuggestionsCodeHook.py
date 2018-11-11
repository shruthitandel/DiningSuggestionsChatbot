"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages suggestions for restaurants.
"""
import math
import json
import dateutil.parser
import datetime
import time
import os
import boto3
import logging
import re
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create SQS client
sqs = boto3.client('sqs', region_name="us-east-1",
            aws_access_key_id='AKIAJHG5MZOWVWJRJSJQ',
            aws_secret_access_key='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'
        )

queue_url = 'https://sqs.us-east-1.amazonaws.com/402812318651/diningqueue'

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, intent_request, fulfillment_state, message):

    #sqs = boto3.client('sqs')
    
    location = get_slots(intent_request)["Location"]
    cuisine = get_slots(intent_request)["Cuisine"]
    no_of_people = get_slots(intent_request)["NumberOfPeople"]
    date = get_slots(intent_request)["Day"]
    dining_time = get_slots(intent_request)["DiningTime"]
    phone_number = get_slots(intent_request)["Phone_number"]
    
    # Send message to SQS queue
    response1 = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageAttributes={
            'cuisine': {
                'DataType': 'String',
                'StringValue': cuisine
            },
            'date': {
                'DataType': 'String',
                'StringValue': date
            },
            'phone_number': {
                'DataType': 'String',
                'StringValue': phone_number
            },
            'dining_time': {
                'DataType': 'String',
                'StringValue': dining_time
            },
            'location': {
                'DataType': 'String',
                'StringValue': location
            },
            'no_of_people': {
                'DataType': 'Number',
                'StringValue': str(no_of_people)
            }
        },
        MessageBody=(
            'Hi, Message Queue from Dining bot '
        )
    )

    print(response1['MessageId'])
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_city(city):
    valid_cities = ['new york', 'los angeles', 'chicago', 'houston', 'philadelphia', 'phoenix', 'san antonio',
                    'san diego', 'dallas', 'san jose', 'austin', 'jacksonville', 'san francisco', 'indianapolis',
                    'columbus', 'fort worth', 'charlotte', 'detroit', 'el paso', 'seattle', 'denver', 'washington dc',
                    'memphis', 'boston', 'nashville', 'baltimore', 'portland']
    return city.lower() in valid_cities


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def isvalid_string(str_val):
    pattern = re.compile("[^0-9]",re.IGNORECASE)
    return pattern.match(str_val)
    

def isvalid_phoneNumber(phone_number):
    pattern = re.compile("^[\dA-Z]{3}[\dA-Z]{3}[\dA-Z]{4}$", re.IGNORECASE)
    return pattern.match(phone_number)


def validate_book_restaurant(location, cuisine, no_of_people, date, dining_time, phone_number):
    # if location and not isvalid_city(location):
    #     return build_validation_result(
    #         False,
    #         'Location',
    #         'We currently do not support {} as a valid location.  Can you try a different city?'.format(location))
    
    if location and not isvalid_string(location):
        return build_validation_result(
            False,
            'Location',
            'I do not understand that.  Can you enter a valid city?'.format(location))
    
    if cuisine and not isvalid_string(cuisine):
        return build_validation_result(
            False,
            'Cuisine',
            'I do not understand that.  Can you try a diffrent cuisine?'.format(cuisine))

    if no_of_people is not None and (int(no_of_people) < 1 or int(no_of_people) > 30):
        return build_validation_result(
            False,
            'NumberOfPeople',
            'Sorry, I can suggest restaurants only from one to thirty people. How many people are in your party?'
        )

    if date is not None:
        logger.debug(datetime.strptime(date, '%Y-%m-%d').date())
        logger.debug(datetime.now())
        if not isvalid_date(date):
            return build_validation_result(False, 'Day',
                                       'I did not understand that, Please give me a valid date?')
        elif datetime.strptime(date, '%Y-%m-%d').date() < datetime.now().date():
            return build_validation_result(False, 'Day',
                                       'Sorry, its past the current date. Can you try a different date?')
   
    if dining_time is not None:
        #logger.debug('Shruthi 124'+ len(dining_time))
        print('Shruthi 125'+dining_time)
        if len(dining_time) != 5:
        # Not a valid time; use a prompt defined on the build-time model.
            # return build_validation_result(False, 'DiningTime', None)
            return build_validation_result(False, 'DiningTime', 'Can you please specify am or pm?')
        
        dine = datetime.strptime(date+' '+dining_time, '%Y-%m-%d %H:%M')

        if dine <= datetime.now():  
            return build_validation_result(False, 'DiningTime',
                                          'Sorry, its past the current time.  Can you try a different time?')

        hour, minute = dining_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
        # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

    if phone_number and not isvalid_phoneNumber(phone_number):
        return build_validation_result(
        False,
        'Phone_number',
        'I did not understand that, could you please provide a valid phone number?'
    )

    return build_validation_result(True, None, None)

""" --- Functions that control the bot's behavior --- """


def book_restaurant(intent_request):
    """
    Performs dialog management and fulfillment for suggesting restaurants.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """

    location = get_slots(intent_request)["Location"]
    cuisine = get_slots(intent_request)["Cuisine"]
    no_of_people = get_slots(intent_request)["NumberOfPeople"]
    date = get_slots(intent_request)["Day"]
    dining_time = get_slots(intent_request)["DiningTime"]
    print("Dine:",dining_time)
    phone_number = get_slots(intent_request)["Phone_number"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
    # Perform basic validation on the supplied input slots.
    # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_book_restaurant(location, cuisine, no_of_people, date, dining_time, phone_number)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                           intent_request['currentIntent']['name'],
                           slots,
                           validation_result['violatedSlot'],
                           validation_result['message'])

        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        return delegate(output_session_attributes, get_slots(intent_request))

    return close(intent_request['sessionAttributes'],
            intent_request,
             'Fulfilled',
             {'contentType': 'PlainText',
              'content': 'Thanks, you will receive {} restaurant suggestions in {} for {} on {} at {} on your mobile number {}'.format(
                  cuisine, location, no_of_people, date, dining_time, phone_number)})
                  
def greeting(intent_request):
    return { "dialogAction": {"type": "Close", "fulfillmentState": "Fulfilled", "message": {"contentType": "PlainText", "content": "Hi there, How can i help you?"}}};
        
    
def thanks(intent_request):
     return { "dialogAction": {"type": "Close", "fulfillmentState": "Fulfilled", "message": {"contentType": "PlainText", "content": "No problem! I am happy to help you"}}};
    
    

""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug(
        'dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return book_restaurant(intent_request)
    elif intent_name == 'GreetingIntent':
        return greeting(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thanks(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    print(json.dumps(event))
    logger.debug('Shruthi')
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
