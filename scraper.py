import urllib.request
import json

class scrapy(object):
    def __init__(self, url: str):
        self.url = url
    
    def findData(self):
        with urllib.request.urlopen(self.url) as response:
            # Read the content and decode from bytes to string
            raw_data = response.read().decode("utf-8")
            # Parse the string into a Python object
            data = json.loads(raw_data)
        
        return data