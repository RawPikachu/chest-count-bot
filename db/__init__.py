from pymongo import MongoClient
import os

DATABASE_URL = os.environ['DATABASE_URL']
client = MongoClient("mongodb+srv://Raw:<password>@chest-count-db.ir458.mongodb.net/db?retryWrites=true&w=majority")