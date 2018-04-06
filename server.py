#!/usr/bin/env python3
# See https://docs.python.org/3.2/library/socket.html
import socket, os, time, datetime, stat, sys, json

from threading import Thread
from argparse import ArgumentParser
from pathlib import Path
from PyLyrics import *
import wikipedia
import nltk

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
    print("GET " + resource)
    response = u''
    if resource == "/" or resource == "/extractData.html":
      response += OK
      response += 'Content-Length: ' + str(len(self.read_file("client/extractData.html").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += self.read_file("client/extractData.html")
      
    elif resource == "/displayData.html":
      response += OK
      response += 'Content-Length: ' + str(len(self.read_file("client/displayData.html").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += self.read_file("client/displayData.html")
    
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

    if resource == "/getArtistInfo":
      artists = content.split('&')[0].split('=')[1].replace('+', ' ').replace('%2C',',').split(',')
      genre = content.split('&')[1].split('=')[1]
    
      for artist in artists:
        print("Adding " + artist + "'s lyrics to db...")
      
        # Add artist lyrics
        addArtistLyrics(artist, genre)
      
    if resource == "/processLyrics":
      processLyrics()
	  
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

# Add artist info to artistInfo.json
def addArtistInfo(artist):
	
  with open("Data/artistInfo.json", "w+") as f:
    print("adding artist info...")
    page = wikipedia.page(artist)
    print(page.html())
    
# Add artists lyrics to lyrics.json -- seperate by genre later
def addArtistLyrics(artist, genre):
	
  # check if file exists
  my_file = Path("Data/lyrics.json")
  if not my_file.is_file():
    open("Data/lyrics.json", 'a').close()
  
  # check if file is empty
  if os.stat("Data/lyrics.json").st_size == 0:
    data = '{ "artists": [] }'
    with open("Data/lyrics.json", "w+") as f:
      f.write(data)

  # read current json file
  with open("Data/lyrics.json", "r") as f:
    json_data = json.load(f)
	
  # check if artist already exists
  for x in json_data["artists"]:
    if x["name"] == artist and x["genre"] == genre:
      print("Artist already saved")
      return
	
  # create json template
  data = {"name" : artist,
  "genre" : genre,
  "processed" : 0,
  "albums": []}
  
  # get all albums
  albums = PyLyrics.getAlbums(singer=artist)
  album_index = 0
  
  # iterate through albums
  for album in albums:
    print(str("\t" + album.name))
    
    # get all tracks for album
    album_tracks = album.tracks()
    
    tracks = []
    
    #iterate through tracks
    for track in album_tracks:
      print("\t\t" + track.name)
      tracks.append({
        "name": track.name,
        "lyrics": track.getLyrics()
      })
      
    data["albums"].append({
      "name": album.name,
      "tracks": tracks
    })
    
  json_data['artists'].append(data)
	
  # open file to write to
  with open("Data/lyrics.json", "w+") as f:
    json.dump(json_data, f, indent=4)
    
def processLyrics():
  with open("Data/lyrics.json", "r") as f:
    json_data = json.load(f)
    
  stemmer = nltk.stem.PorterStemmer()
    
  for artist in json_data["artists"]:
    print("Processing " + artist["name"])
    
    for album in artist["albums"]:
      print("\tProcessing " + album["name"])
      
      for track in album["tracks"]:
        print("\t\tProcessing " + track["name"])
        
        if(track["lyrics"]):
          word_tokens = nltk.word_tokenize(track["lyrics"])
          stop_words = set(nltk.corpus.stopwords.words("english"))
          filtered_track = [w for w in word_tokens if not w in stop_words]
          print("*****")
          print(str(len(word_tokens)))
          print(str(len(filtered_track)))
          #json_data["artists"].artist["albums"].album["tracks"].track["lyrics"] = filtered_track
          
  with open("Data/lyrics.json", "w+") as f:
    json.dump(json_data, f, indent=4)

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

