from genericpath import exists
import socket
import sys

from res import Res
from req import Req

from subprocess import Popen, PIPE

import os

ENV = {
    "HOSTNAME":"127.0.0.1",
    "PORT":3000,
    "BUFFER_SIZE":4096
}

class Server:

    def __init__(self , env , app = {}):
        self.hostname = env["HOSTNAME"]
        self.port = env["PORT"]
        self.app = app
        self.env = env

    def start(self):

        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind((self.hostname, self.port))
        self.listen_socket.listen(1)

        print(f"server is listening on port {self.port}")

        self.loop()

    def parse_req(self , request_data):
        
        req = Req()
    
        header_line_end = request_data.index("\r\n")
        header_line = request_data[:header_line_end]
        header_end = request_data.index("\r\n\r\n")

        req.method,req.route,req.http_version = header_line.split(" ")
        header = request_data[header_line_end+2:header_end]

        for line in header.split("\r\n"):
            key,val = line.split(":" , 1)
            req.header[key] = val

        req.body = request_data[header_end+2:]
        
        return req

    def build_header(self , res : Res):
        
        http_header = ""

        for key,value in res.header.items():
            http_header += f"{key}:{value}\r\n"
            pass

        return http_header

    def execute_php(self , client_conn , route, res):

        if not exists(route):
            client_conn.sendall(b"HTTP/1.1 404 Not Found\r\n")
            return

        process = Popen(['php', '-f' , route], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        html = stdout.decode("ascii")

        if stderr:
            print(stderr.decode("ascii"))
            html = ""
            client_conn.sendall(b"HTTP/1.1 500 Internal Server Error\r\n")
            return

        http = "HTTP/1.1 200 OK\r\n"
        http += self.build_header(res)
        http += "\r\n"
        http += html
        client_conn.sendall(http.encode("ascii"))

    def serve_file(self , client_conn , route):
        try:
            with open(route , 'rb') as file:
                    client_conn.sendfile(file)
        except FileNotFoundError:
            client_conn.send(b"HTTP/1.1 404 Not Found\r\n")
        

    def serve_dir(self):
        pass

    def handle_connection(self , client_conn):

        request_data = (client_conn.recv(65535)).decode("ascii")

        if not request_data:
            client_conn.close()
            return

        req = self.parse_req(request_data)

        try:
            req.route.index(".")
            if req.route.split(".")[-1] == "php":
                self.execute_php(client_conn , req.route[1:] , Res())
            else:
                http = "HTTP/1.1 200 OK\r\n\r\n"
                client_conn.send(http.encode("ascii"))
                self.serve_file(client_conn , req.route[1:])
        except ValueError:

            route_name = req.route[1:].replace("/" , "_")
            http_handler = None
            try:
                http_handler = getattr(self.app , f"{req.method.lower()}_{route_name}")
            except:
                client_conn.sendall(b"HTTP/1.1 404 Not Found\r\n")
                client_conn.close()
                return
            res = Res()
            res : Res = http_handler(req , res)
            http = ""

            if res.type in ["json" , "xml" , "text/plain" , "text/css" , "text/html"]:
                http = f"HTTP/1.1 {res.status_code} OK\r\n"
                http += self.build_header(res)
                http += "\r\n"
                http += res.data
                client_conn.sendall(http.encode("ascii"))

            if res.type == "file":
                http = "HTTP/1.1 200 OK\r\n"
                http += self.build_header(res)
                http += "\r\n"
                client_conn.sendall(http.encode("ascii"))
                self.serve_file(client_conn , res.data)

            if res.type == "php":
                self.execute_php(client_conn , res.data , res)

        client_conn.close()
        

    def loop(self):
        while True:
            client_conn,client_addr = self.listen_socket.accept()
            self.handle_connection(client_conn)


routing_scipt = sys.argv[1]
ext_index = routing_scipt.index(".py")

module = __import__(routing_scipt[:ext_index])

server = Server(ENV , module)
server.start()
