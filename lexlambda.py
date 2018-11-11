import json
import boto3

lex_client = boto3.client('lex-runtime')


def lambda_handler(event, context):
    #for message in event["messages"]:
    #   text = message["unstructured"]["text"]
    #  text = text.lower()
    print(event)
    print(event['key1'])
    print(event['userid'])
    userid = event['userid']
    inputText = event['key1']
    print('Testing for input {}'.format(inputText))

    # sessionAttributes = event['sessionAttributes']

    response = lex_client.post_text(
        botAlias="$LATEST",
        botName="dining_bot",
        userId=userid,
        # sessionAttributes=sessionAttributes,
        inputText=inputText
    )

    print("HERE is the response : " + str(response['message']));
    
    return response
