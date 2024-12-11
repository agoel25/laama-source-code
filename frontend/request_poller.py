import logging
import requests
import boto3
import uuid
import time
import hashlib

API_ENDPOINT = "https://uqahsjj2e6.execute-api.ca-central-1.amazonaws.com/Stage2/get-analysis"
from botocore.exceptions import RefreshWithMFAUnsupportedError

session = boto3.Session()
REGION_NAME = 'ca-central-1'  
dynamodb = session.resource('dynamodb', region_name=REGION_NAME)
DYNAMODB_TABLE = 'g13-436-youtube-data'

def make_request(video_url, request_id, comments):
    """
    Make a request to the external API with the given video URL and request ID.
    """
    data = {
        "body": {
            "video_url": video_url,
            "request_id": request_id,
            "comments": comments,
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(data)
        response = requests.post(API_ENDPOINT, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return None

class RequestPoller:
    def __init__(self, url, comments):
        """
        Initialize the RequestPoller instance.
        """
        self.table = dynamodb.Table(DYNAMODB_TABLE)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Generate a unique request ID
        self.req_id = self.generate_req_id(url)
        self.url = url 
        self.comments = comments

    def generate_req_id(self, text):
        """
        Generate a unique request ID based on the input text and a UUID.
        """
        hash_input = f"{text}-{uuid.uuid4()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def new_item(self):
        """
        Add a new item to DynamoDB with a status of 'PENDING'.
        """
        self.logger.info(f"Creating new item with ID: {self.req_id}")
        self.table.put_item(
            Item={
                "RequestID": self.req_id,
                "FinalResult": "",
                "RequestStatus": "PENDING"
            }
        )

    def poll(self, interval=5, timeout=600):
        """
        Poll the DynamoDB table for the request status.
        """
        request = make_request(self.url, self.req_id, self.comments)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.table.get_item(
                Key={ 
                    'RequestID': self.req_id
                }
            )

            if "Item" in response:
                item = response["Item"]
                status = item.get("RequestStatus")

                if status == "Completed":
                    self.logger.info(f"Request {self.req_id} completed successfully!")
                    if "FinalResult" in item:
                        print(item)
                        print(request)
                        return item["FinalResult"]
                    else:
                        self.logger.warning(f"Request {self.req_id} completed but 'FinalResult' is missing.")
                        return None
                else:
                    self.logger.info(f"Request {self.req_id} status: {status}. Retrying in {interval} seconds.")
            else:
                self.logger.warning(f"Request ID {self.req_id} not found in the table.")

            time.sleep(interval)

        self.logger.error(f"Request {self.req_id} timed out after {timeout} seconds.")
        print(request)
        return None
