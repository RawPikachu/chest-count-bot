from pymongo import MongoClient
import certifi
import os

ca = certifi.where()
DATABASE_URL = os.environ['DATABASE_URL']
client = MongoClient(DATABASE_URL, tlsCAFile=ca)