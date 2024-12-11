import boto3
import json

runtime = boto3.client("sagemaker-runtime")
s3 = boto3.client('s3')
dynamodb = boto3.client("dynamodb")

endpoint_name = "huggingface-pytorch-inference-2024-11-25-01-59-19-440"
dynamodb_table = '436-youtube-data'
status_table = 'g13-436-youtube-data'

CONTENT_CATEGORIES = {
    'educational': [
        'learn', 'explain', 'tutorial', 'guide', 'how to', 'lesson',
        'educational', 'tips', 'tricks', 'walkthrough', 'strategy',
        'hack', 'instructional', 'knowledge', 'overview', 'step-by-step',
        'beginner', 'advanced', 'breakdown', 'teaching', 'skill',
        'demonstration', 'DIY', 'example', 'practice', 'training'
    ],
    'entertainment': [
        'fun', 'game', 'play', 'laugh', 'amusing', 'exciting',
        'reaction', 'funny', 'hilarious', 'joke', 'challenge',
        'meme', 'prank', 'roast', 'parody', 'stream',
        'let\'s play', 'entertaining', 'skit', 'comedy', 'laughing',
        'epic', 'awesome', 'movie', 'series', 'show', 'cinematic',
        'clips', 'viral', 'highlight', 'storytime', 'cartoon'
    ],
    'news': [
        'news', 'update', 'current', 'report', 'breaking', 'analysis',
        'headline', 'coverage', 'story', 'recent', 'press', 'announcement',
        'live', 'today', 'world', 'investigation', 'trending',
        'fact', 'journalism', 'interview', 'commentary', 'politics',
        'economy', 'debate', 'event', 'coverage', 'exclusive'
    ],
    'lifestyle': [
        'lifestyle', 'daily', 'routine', 'life', 'vlog', 'personal',
        'fitness', 'self-care', 'travel', 'home', 'family', 'relax',
        'style', 'fashion', 'beauty', 'morning', 'night', 'experience',
        'story', 'wellness', 'health', 'food', 'day in the life',
        'minimalism', 'decor', 'week', 'adventure', 'memories',
        'hobby', 'balance', 'diary', 'journey', 'cooking', 'pets'
    ],
    'tech': [
        'technology', 'software', 'hardware', 'coding', 'programming', 'digital',
        'python', 'aws', 'cloud', 'gadget', 'device', 'setup',
        'review', 'tutorial', 'explanation', 'features', 'specs',
        'comparison', 'update', 'script', 'coding', 'automation',
        'system', 'framework', 'setup guide', 'debug', 'ML', 'AI',
        'machine learning', 'deep learning', 'data', 'workflow', 'neural network',
        'robotics', 'test', 'configuration', 'benchmark', 'video',
        'Marques', 'unboxing', 'performance', 'teardown', 'engineering',
        'functionality', 'optimization', 'API', 'SDK', 'tools',
        'cybersecurity', 'apps', 'developer', 'project'
    ],
    'business': [
        'business', 'finance', 'money', 'entrepreneur', 'startup', 'market',
        'economy', 'growth', 'strategy', 'investing', 'stock', 'shares',
        'revenue', 'profit', 'marketing', 'sales', 'trade', 'analysis',
        'branding', 'consulting', 'debt', 'valuation', 'cash flow',
        'plan', 'capital', 'fund', 'budget', 'venture', 'taxes',
        'accounting', 'expense', 'earnings', 'wealth', 'success',
        'corporate', 'industry', 'trend', 'pitch', 'productivity',
        'organization', 'team', 'CEO', 'founder', 'leader', 'management'
    ]
}

def lambda_handler(event, context):
    try:
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_key = event['Records'][0]['s3']['object']['key']
        
        file_obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        
        file_content = file_obj['Body'].read().decode('utf-8')
        print(file_content)
        
        data = json.loads(file_content)
        input_text = data.get('transcript')
        video_id = data.get('id')
        request_id = data.get('request_id')
        print("request id: " + request_id)

        print(input_text)
        
        if not input_text:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No transcript found in uploaded file"})
            }

        max_length = 150
        min_length = 40

        max_chunk_length = 1024
        chunks = [input_text[i:i + max_chunk_length] for i in range(0, len(input_text), max_chunk_length)]

        summaries = []
        for chunk in chunks:
            payload = {
                "inputs": chunk,
                "parameters": {
                    "max_length": max_length,
                    "min_length": min_length,
                    "do_sample": False
                }
            }

            response = runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType="application/json",
                Body=json.dumps(payload)
            )

            result = json.loads(response["Body"].read().decode())
            summaries.append(result[0]["summary_text"])

        final_summary = " ".join(summaries)
        print("Final Summary: " + final_summary)

        category = getCategorization(final_summary)
        sentiment_score = getSentiment(final_summary)
        top_videos = getTopVideos(category)
        
        if top_videos:
            video_list = "\n".join(f"- {link}" for link in top_videos[:5])
            video_suggestions = video_list
        else:
            video_suggestions = " Unfortunately, we couldn't find top videos in this category at the moment."

        sentiment_score_mult = sentiment_score * 100
        sentiment_score_round = sentiment_score_mult // 1
        sentiment_score_percentage = str(sentiment_score_round) + "%"

        sentiment_feedback = ""
        if sentiment_score > 0.5:
            sentiment_feedback = f"Your video in the '{category}' category is doing well! The sentiment is very positive. Keep up the great work! If you are curious about some other well-performing videos in this category, check them out below!"
        elif sentiment_score == 0.5:
            sentiment_feedback =  f"Your video in the '{category}' category has a neutral sentiment. It’s good, but there’s room for improvement. Consider engaging your audience more. Take a look at some video suggestions below for inspiration!"
        else:
            sentiment_feedback = f"Your video in the '{category}' category received negative sentiment feedback. Analyze the comments and consider addressing viewer concerns to improve. Here are some videos in the same category that might help you understand how to better engage your audience."
        
        final_result = json.dumps({
            "video_id": video_id,
            "category": category,
            "sentiment_score_percentage": sentiment_score_percentage,
            "sentiment_feedback": sentiment_feedback,
            "video_suggestions": video_suggestions
        })

        # write summary to dynamo
        dynamodb.put_item(
            TableName=dynamodb_table,
            Item={
                "video_id": {"S": str(video_id)},
                "input_text": {"S": input_text},
                "summary": {"S": final_summary},
                "category": {"S": category.lower()},
                "sentiment_score": {"N": str(sentiment_score)},
                "video_suggestions": {"S": video_suggestions},
                "final_result": {"S": final_result},
            }
        )

        # update row in status dynamo
        updateStatusDynamo(request_id, final_result)

        return {
            "statusCode": 200,
            "body": final_result
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def getCategorization(text):
    text = text.lower()
    categories = []
    
    category_scores = {}
    for category, keywords in CONTENT_CATEGORIES.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            category_scores[category] = score
    
    # get top category
    sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_categories[0][0] if sorted_categories else 'general'

def getSentiment(text):
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 'love', 'lovely',
        'beautiful', 'nice', 'cool', 'perfect', 'funny', 'hilarious', 'superb', 'wonderful',
        'brilliant', 'incredible', 'dope', 'epic', 'genius', 'sweet', 'lit', 'wow', 'impressive',
        'inspiring', 'helpful', 'cheerful', 'fun', 'enjoyable', 'informative', 'well done',
        'outstanding', 'creative', 'unique', 'spectacular', 'entertaining', 'breathtaking',
        'thoughtful', 'insightful', 'engaging', 'relatable', 'exciting', 'uplifting', 'supportive',
        'motivating', 'refreshing', 'heartwarming', 'innovative', 'kind', 'charming', 'pleasant',
        'admirable', 'favorite', 'fav', 'fave', 'adorable', 'blessed', 'legendary', 'proud',
        'super', 'positive vibes', 'respect', 'accurate', 'clever', 'funniest', 'amused'
    ]
    negative_words = [
        'bad', 'poor', 'terrible', 'horrible', 'awful', 'hate', 'worst', 'boring', 'dull',
        'annoying', 'cringe', 'stupid', 'lame', 'weak', 'ugly', 'nonsense', 'trash', 'garbage',
        'disgusting', 'lazy', 'failure', 'broken', 'toxic', 'negative', 'sad', 'angry',
        'disappointed', 'mad', 'upset', 'hurt', 'sick', 'nasty', 'arrogant', 'ignorant', 'fake',
        'cheap', 'overrated', 'pathetic', 'pointless', 'shame', 'gross', 'irritating', 'useless',
        'mean', 'offensive', 'irrelevant', 'childish', 'immature', 'tired', 'annoyed', 'biased',
        'misleading', 'horrendous', 'ridiculous', 'awful', 'dreadful', 'insulting', 'hated it',
        'unnecessary', 'trash tier', 'boring af', 'hate this', 'worst ever', 'waste', 'ugh',
        'ruined', 'nonsense', 'fail', 'lies'
    ]

    text_words = text.lower().split()

    sentiment_score = 0.7

    for word in text_words:
        if word in positive_words:
            sentiment_score += 0.1
        elif word in negative_words:
            sentiment_score -= 0.1

    sentiment_score = max(0.2, min(1, sentiment_score))
    return sentiment_score

def getTopVideos(category, min_sentiment_score=0.55):
    try:
        # use a scan to find videos with the same category and sentiment score > 0.55
        response = dynamodb.scan(
            TableName=dynamodb_table,
            FilterExpression="category = :category AND sentiment_score > :min_sentiment_score",
            ExpressionAttributeValues={
                ":category": {"S": category.lower()},
                ":min_sentiment_score": {"N": str(min_sentiment_score)}
            }
        )

        # extract video IDs from the results and make urls
        top_videos = [
            f"https://www.youtube.com/watch?v={item['video_id']['S']}"
            for item in response.get('Items', [])
        ]
        return top_videos

    except Exception as e:
        print(f"Error querying top videos: {str(e)}")
        return []
    
def updateStatusDynamo(request_id, result):
    dynamodb.update_item(
            TableName=status_table,
            Key={
                "RequestID": {"S": request_id}
            },
            UpdateExpression="SET RequestStatus = :completed, FinalResult = :result",
            ExpressionAttributeValues={
                ":completed": {"S": "Completed"},
                ":result": {"S": result} 
            }
        )