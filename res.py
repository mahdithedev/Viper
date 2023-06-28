import json

class Res:
    def __init__(self):
        self.type = ""
        self.data = ""
        self.status_code = ""
        self.header = {}

    def status(self , status_code):
        self.status_code = status_code
        return self

    def json(self , data):
        self.header["Content-Type"] = "application/json"
        self.type = "json"
        self.data = json.dumps(data , indent = 4)
        return self

    def php(self , file_name):
        self.header["Content-Type"] = "text/html"
        self.type = "php"
        self.data = file_name
        return self

    def file(self , file_name):
        self.type = "file"
        self.data = file_name
        return self