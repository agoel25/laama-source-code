import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

s3_bucket = '436-transcriptions'
dynamodb_table = '436-youtube-data'

def check_existing_analysis(video_id, request_id):
    """check if video analysis already exists in the dynamo db table"""
    table = dynamodb.Table(dynamodb_table)

    try:
        response = table.get_item(
            Key={'video_id': video_id}
        )

        final_value = response['Item']['final_result']

        table2 = dynamodb.Table('g13-436-youtube-data')
        table2.update_item(
            Key={
                "RequestID": request_id
            },
            UpdateExpression="SET RequestStatus = :completed, FinalResult = :result",
            ExpressionAttributeValues={
                ":completed": "Completed",
                ":result": final_value
            }
        )

        return 'Item' in response
    except Exception as e:
        logger.info(f"Analysis doesn't already exist: {str(e)}")
        return False

def get_video_id(url):
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    else:
        raise ValueError("Invalid YouTube URL")

def save_to_s3(video_id, data):
    """save the collected data to s3"""
    try:
        s3_key = f'{video_id}.json'
        s3.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=json.dumps(data, default=str),
            ContentType='application/json'
        )
        return s3_key
    except Exception as e:
        logger.error(f"Error saving to S3: {str(e)}")
        raise

def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        video_url = body.get('video_url')
        request_id = body.get('request_id')
        video_comments = body.get('comments')
        
        if not video_url:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No video URL provided'})
            }
        
        video_id = get_video_id(video_url)
        print(video_id)
        
        # check if analysis already exists
        if check_existing_analysis(video_id, request_id):
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Analysis already exists',
                    'video_id': video_id,
                    'status': 'exists'
                })
            }
        
        # combine all data
        video_data = {
            'transcript': video_comments[:2000],
            'id': video_id,
            'request_id': request_id
        }
        
        # save to S3
        s3_key = save_to_s3(video_id, video_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data collection successful',
                'video_id': video_id,
                's3_key': s3_key,
                'status': 'new'
            }, default=str)
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }