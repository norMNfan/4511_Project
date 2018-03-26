#!/usr/bin/env python3
# See https://docs.python.org/3.2/library/socket.html
# for a decscription of python socket and its parameters
import socket, os.path, time, datetime, stat

from threading import Thread
from argparse import ArgumentParser
from pathlib import Path
from PyLyrics import *

BUFSIZE = 4096
DEBUG = False

CRLF = '\r\n'
OK = 'HTTP/1.1 200 OK' + CRLF
CREATED = 'HTTP/1.1 201 Created' + CRLF
NOT_FOUND = 'HTTP/1.1 404 NOT FOUND' + CRLF + 'Connection: close' + CRLF

class HTTPServer:
  def __init__(self, host, port):
    print('listening on port {}'.format(port))
    self.host = host
    self.port = port

    self.setup_socket()

    self.accept()

    self.sock.shutdown()
    self.sock.close()

  def setup_socket(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.bind((self.host, self.port))
    self.sock.listen(128)

  def accept(self):
    while True:
      (client, address) = self.sock.accept()
      th = Thread(target=self.accept_request, args=(client, address))
      th.start()
      
  def accept_request(self, client_sock, client_address):
    print('talking to {}'.format(client_address))
    data = client_sock.recv(BUFSIZE)
    request = data.decode('utf-8')
    response = self.process_request(request)
    client_sock.send(bytes(response, 'utf8'))
    client_sock.shutdown(1)
    client_sock.close()
    
  def parse_request(self, data):
    method = data.split()[0].split(" ")[0]
    content = data.split()[-1]
    try:
      resource = data.split("\n")[0].split(" ")[1]
      try:
        file_type = resource.split(".")[1]
      except:
        file_type = u'html'
    except:
      resource = u''
    date_time = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S.%f")
    
    return method, content, resource, file_type, date_time
    
  def process_request(self, data):
    # parse request
    if DEBUG: print("###### REQUEST BODY ######\n\n" + data + "###################\n")
    (method, content, resource, file_type, date_time) = self.parse_request(data)
    
    if(method == "GET"):
      return self.process_GET(content, resource, file_type, date_time)
      
    elif(method == "POST"):
      return self.process_POST(content, resource, file_type, date_time)
      
    else:
      return NOT_ALLOWED
      
  def process_GET(self, content, resource, file_type, date_time):
    response = u''
    if resource is "/":
      response += OK
      response += 'Content-Length: ' + str(len(self.read_file("client/extractData.html").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += self.read_file("client/extractData.html")
    
    elif file_type == "css":
      response += OK
      response += 'Content-Length: ' + str(len(self.read_file("client/css/style.css").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += self.read_file("client/css/style.css")
      
    elif file_type == "js":
      response += OK
      response += 'Content-Length: ' + str(len(self.read_file("client/js/script.js").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += self.read_file("client/js/script.js")
	
    return response
	
  def process_POST(self, content, resource, file_type, date_time):
	
    print(content)
    if resource == "/getArtistInfo":
      albums = PyLyrics.getAlbums(singer='Eminem')
      for a in albums:
        print(a)
	  
    response = u''
    
    response += OK
    response += 'Content-Length: ' + str(len(self.read_file("client/extractData.html").encode('utf-8'))) + CRLF
    response += 'Content-Type: text/' + file_type + '\n' + CRLF
    response += self.read_file("client/extractData.html")
    
    return response
	
  def read_file(self, resource):
    with open(resource, "r") as f:
      return f.read()
      
  def write_file(self, resource, content):
    with open(resource, "w") as f:
      f.write(content)
      os.chmod(resource, 646)
    
  def file_exists(self, resource):
    my_file = Path(resource)
    return my_file.is_file()

def parse_args():
  parser = ArgumentParser()
  parser.add_argument('--host', type=str, default='localhost',
                      help='specify a host to operate on (default: localhost)')
  parser.add_argument('-p', '--port', type=int, default=9001,
                      help='specify a port to operate on (default: 9001)')
  args = parser.parse_args()
  return (args.host, args.port)

if __name__ == '__main__':
  (host, port) = parse_args()
  HTTPServer(host, port)

