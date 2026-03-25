import sys
import json

def get_url():
    with open('output_v2/timestamps.json', 'r') as f:
        data = json.load(f)
        q = data["mondai"][0]["questions"][0]
        st, et = q["start_time"], q["end_time"]
        url = f"https://res.cloudinary.com/demo/video/upload/so_{st},eo_{et}/test_audio.mp3"
        print(url)
get_url()
