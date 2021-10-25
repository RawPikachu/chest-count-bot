from db import client

def get_server_list_all():
    db = client.db
    collection = db.server_list 
    server_list = dict({server["name"]: server for server in list(collection.find({}, {"_id":0}).sort([('$natural', 1)]))})
    return server_list

def update_server_list(name, total_players, timestamp, uptime=None, min30_chest_count=None, chest_count=None, last_chest_count=None):
    db = client.db
    collection = db.server_list
    collection.replace_one({"name":name}, {"name":name, "total_players":total_players, "timestamp": timestamp, "uptime":uptime, "min30_chest_count":min30_chest_count, "chest_count":chest_count, "last_chest_count":last_chest_count}, upsert=True)

def delete_server_list(name):
    db = client.db
    collection = db.server_list
    collection.delete_one({"name":name})