import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import base64
client = OpenAI(
    api_key=os.environ.get("OPEN_AI_TOKEN"),
    base_url="https://jamsapi.hackclub.dev/openai",
)
print(client.base_url)



# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Path to your image
image_path = "/home/v205/grassQuest/mainFiles/U05QJ4CF5QT.png"

# Getting the base64 string
base64_image = encode_image(image_path)

f = open("demofile3.txt", "w")
f.write(base64_image)
f.close()


response = client.chat.completions.create(
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

print(response.choices[0])


image_description = response.choices[0].message.content
print(image_description)