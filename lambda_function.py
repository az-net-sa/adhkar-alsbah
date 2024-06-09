from requests_oauthlib import OAuth1Session
import os
import json



def postTweet( consumer_key, consumer_secret, access_token, access_token_secret , text, media_id=0  ):
        


    # Ensure that all necessary environment variables are set
    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        raise EnvironmentError("One or more environment variables are missing. Please set CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, and ACCESS_TOKEN_SECRET.")

    if media_id:
        payload = {"text": text, "media": {"media_ids": [media_id]}}
    else:
        payload = {"text": text}


    # Create an OAuth1Session with the consumer keys and access tokens
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    # Make the POST request to the Twitter API to create a tweet
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    # Check if the request was successful
    if response.status_code != 201:
        raise Exception(
            "Request returned an error: {} {}".format(response.status_code, response.text)
        )

    # Print the response code and the response content
    print("Response code: {}".format(response.status_code))
    json_response = response.json()
    print(json.dumps(json_response, indent=4, sort_keys=True))
    # end of postTweet function



def lambda_handler(event, context):
    tweet_text = event.get('tweet')
    media_id = event.get('media_id')
    
    if media_id == "NULL":
        media_id = None
        
    consumer_key = event.get('consumer_key')
    consumer_secret = event.get('consumer_secret')
    access_token = event.get('access_token')
    access_token_secret = event.get('access_token_secret')
    
    postTweet( consumer_key, consumer_secret, access_token, access_token_secret , tweet_text , media_id )
    return {
        'statusCode': 200,
        'body': json.dumps(f"Tweeted: {tweet_text} with media_id: {media_id}")
        }
