import os
from slack_bolt import App

from dotenv import load_dotenv
load_dotenv()

print(os.environ.get("HELPER_SLACK_BOT_TOKEN"))

from slack_bolt.adapter.socket_mode import SocketModeHandler


import logging
import os
import os.path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import os
import requests


import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import base64
AIClient = OpenAI(
    api_key=os.environ.get("OPEN_AI_TOKEN"),
    base_url="https://jamsapi.hackclub.dev/openai",
)
print(AIClient.base_url)



# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')




def download_file(download_url):
    """
    Downloads a file from a given URL with a Slack bot token.

    Args:
        download_url (str): The URL of the file to download.

    Returns:
        bytes: The contents of the file.
    """
    headers = {
        'Authorization': f'Bearer {os.environ.get("HELPER_SLACK_BOT_TOKEN")}',
        'Content-Type': 'application/json'  # Adjust if needed
    }
    try:
        response = requests.get(download_url, headers=headers).content
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None

def save_file(file_content, file_name, save_path):
    """
    Saves the file content to a file at a specific path.

    Args:
        file_content (bytes): The content of the file.
        file_name (str): The name of the file.
        save_path (str): The path to save the file.

    Returns:
        str: The path of the saved file.
    """
    # Create the full file path
    file_path = os.path.join(save_path, file_name)

    try:
        # Save the file
        with open(file_path, 'wb') as file:
            file.write(file_content)
        print(f"File saved to {file_path}")
        return file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

# Example usage
#download_url = "https://example.com/file.pdf"
save_path = "/home/v205/grassQuest/mainFiles/userData"
file_name = "example.png"


    
client = WebClient(token=os.environ.get("HELPER_SLACK_BOT_TOKEN"))
logger = logging.getLogger(__name__)


app = App(token=os.environ["HELPER_SLACK_BOT_TOKEN"])


'''
@app.message()
def say_hello(message, say):
    if(message.get("thread_ts")):
        print("THREAD MESSAGE")
    print(message)
'''

@app.event("message")
def handle_message_events(message, say, logger):

    print(message)

    if message.get("thread_ts"):
        print(f"Thread message detected: {message['thread_ts']}")
    else:
        print("Direct message in channel")

    file_name  = message["user"] + ".png"
    if 'files' in message:
        for file in message['files']:
            print(file["id"])
            #print(client.file.info(file = file["id"]))
            download_file(file["url_private_download"])
            file_content = download_file(file["url_private_download"])
            if file_content:
                    save_file(file_content, file_name, save_path)
                    # Path to your image
                    image_path = "/home/v205/grassQuest/mainFiles/userData/" + message["user"] + ".png"
                    '''
                    # Getting the base64 string
                    base64_image = encode_image(image_path)


                    response = AIClient.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What’s in this image?"},
                            {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                            },
                        ],
                        }
                    ],
                    max_tokens=85,
                    )

                    #print(response)
                    image_description = response.choices[0].message.content
                    print(image_description)
                    '''


            



@app.event("file_created")
def handle_file_created_events(body, logger):
    print(body)

@app.event("file_public")
def handle_file_public_events(body, logger):
    print(body)





if __name__ == "__main__":

    handler = SocketModeHandler(app, os.environ["HELPER_SLACK_APP_TOKEN"])
    handler.start()


'''


@app.event("app_mention")
@app.event("app_mention")
def event_test(say):
    say("Hi there!")
    print("TEST")    


@app.message("<@U07H9T4NVFC>")
def say_hello(message, say):
    user = message['user']
    print("gotcha")
    say(f"Hi there, <@{user}>,  should now be listening")

@app.message("hi")
def say_hello(message, say):
    user = message['user']
    say(f"Hi there, <@{user}>,  should now be listening")

CHANNEL = "C07HNJG1FPT"  # Replace with the actual channel ID or name
'''