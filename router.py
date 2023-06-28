from req import Req
from res import Res

def get_(req : Req , res : Res):
    return res.status(200).php("index.php")

def get_api_test(req : Req , res : Res):
    return res.status(200).json({"message":"you can use this"})

def get_api_user(req : Req , res : Res):
    return res.status(200).json({"username":"Bob"})