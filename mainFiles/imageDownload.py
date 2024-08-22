import requests

img_data = requests.get("https://files.slack.com/files-tmb/T0266FRGM-F07J98KNXME-f0dcda4b51/image_64.png").content
with open('image_name.jpg', 'wb') as handler:
    handler.write(img_data)