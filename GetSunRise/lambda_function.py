import requests
import datetime
import boto3
import json
from requests_oauthlib import OAuth1Session


def get_sunrise_as_utc(lat, lng):
    response = requests.get(f'https://api.sunrisesunset.io/json?lat={lat}&lng={lng}')
    sunrise = response.json()['results']['sunrise']
    sunrise_time = datetime.datetime.strptime(sunrise, "%I:%M:%S %p")
    one_hour_before_sunrise_as_utc = sunrise_time - datetime.timedelta(hours=4)
    return f"{one_hour_before_sunrise_as_utc.minute} {one_hour_before_sunrise_as_utc.hour} * * ? *"
    
def get_Sun_Set_as_CUTC(lat,lng):
    response = requests.get(f'https://api.sunrisesunset.io/json?lat={lat}&lng={lng}')
    sunset = response.json()['results']['sunset']
    sunset_time = datetime.datetime.strptime(sunset, "%I:%M:%S %p")
    two_hour_before_sunset_as_UTC = sunset_time - datetime.timedelta(hours=5)
    return f"{two_hour_before_sunset_as_UTC.minute} {two_hour_before_sunset_as_UTC.hour} ? * * *"



def get_media_id(time, consumer_key, consumer_secret, access_token, access_token_secret):  
    # Retrieve the keys and tokens from environment variables

    
    if time == 'M':
        image_path = "images/morning_image.jpeg" 
       
    if time == 'E':
        image_path = "images/evening_image.jpeg"
    
    # Create an OAuth1Session with the consumer keys and access tokens
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    # Upload the image to Twitter
    with open(image_path, "rb") as image_file:
        files = {"media": image_file}
        response = oauth.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            files=files
        )

    # Check if the image upload was successful
    if response.status_code != 200:
        raise Exception(
            "Image upload returned an error: {} {}".format(response.status_code, response.text)
        )
    
    # Get the media ID from the response
    media_id = response.json()["media_id_string"]
    return media_id
    



def GetSunRise(event, context):
    consumer_key = event.get('consumer_key')
    consumer_secret = event.get('consumer_secret')
    access_token = event.get('access_token')
    access_token_secret = event.get('access_token_secret')
    
    # Ensure that all necessary environment variables are set
    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        raise EnvironmentError("One or more environment variables are missing. Please set CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, and ACCESS_TOKEN_SECRET.")
    
    
    lat = 24.7136  # Your latitude
    lng = 46.6753  # Your longitude
    
    time = event.get('time')

    if time == 'M':
        tweet_text = "صباح الخير, لا تنسَ اذكار الصباح"
        media_id = get_media_id(time, consumer_key, consumer_secret, access_token, access_token_secret)
        cron_expression = get_sunrise_as_utc(lat, lng)
    if time == 'E':
        tweet_text = "مساء الخير, لا تنسَ اذكار المساء"
        media_id = get_media_id(time, consumer_key, consumer_secret, access_token, access_token_secret)
        cron_expression = get_Sun_Set_as_CUTC(lat, lng)
    
    client = boto3.client('events')
    rule_name = 'RunLambdaBeforeSunrise'
    
    # Update the CloudWatch Events rule with the new cron expression
    response = client.put_rule(
        Name=rule_name,
        ScheduleExpression=f"cron({cron_expression})",
        State='ENABLED'
    )
    
    # Add the PostTweet Lambda function as the target for the rule
    lambda_client = boto3.client('lambda')
    target_arn = lambda_client.get_function(FunctionName='PostTweet')['Configuration']['FunctionArn']
    
    response = client.put_targets(
        Rule=rule_name,
        Targets=[
            {
                'Id': '1',
                'Arn': target_arn,
                'Input': json.dumps({'tweet': tweet_text,
                                     'media_id' : media_id, 
                                     "consumer_key": consumer_key,
                                     "consumer_secret": consumer_secret ,
                                     "access_token": access_token,
                                     "access_token_secret": access_token_secret
                    
                })
            }
        ]
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"Scheduled event updated to: {cron_expression}",
            'tweet': tweet_text,
            'media_id': media_id
        })
    }
