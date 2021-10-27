from discord.ext import commands
#from discord_slash import cog_ext
#from discord_slash.context import SlashContext
#from discord_slash.model import SlashCommandOptionType
#from discord_slash.utils.manage_commands import create_option
from collections import Counter
import asyncio
import time
from db import db_adapter as db
from corkus import Corkus
from tabulate import tabulate
import requests


class Wynncraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.server_check())
        self.bot.loop.create_task(self.chest_count_check())

    async def limited(self, until):
        duration = int(round(until - time.time()))
        print('Rate limited, sleeping for {:d} seconds'.format(duration))
    
    @commands.command(name='listservers')
    async def _listservers(self, ctx):
        db_server_list = db.get_server_list_all()
        table = [[db_server["name"], db_server["total_players"], db_server["uptime"], db_server["min30_chest_count"]] for key, db_server in db_server_list.items()]
        table.insert(0, ["Server", "Player Count", "Uptime (min)", "Chest Count (30 mins)"])
        tabulated_table = tabulate(table)
        await ctx.send(f"```prolog\n{tabulated_table}\n```")
    
    async def server_check(self):
        while True:
            db_server_list = db.get_server_list_all()
            
            response = requests.get("https://athena.wynntils.com/cache/get/serverList")

            serverlist = response.json()["servers"]

            db_server_names = db_server_list.keys()

            for key, value in serverlist.items():
                server = value
                server["name"] = key
                if not (key in db_server_names):
                    db.update_server_list(server["name"], len(serverlist[server["name"]]["players"]), serverlist[server["name"]]["firstSeen"] / 1000, uptime=int((time.time() - (serverlist[server["name"]]["firstSeen"] / 1000)/60)))
            for key, value in db_server_list.items():
                db_server = value
                db_server["name"] = key
                if not (db_server["name"] in serverlist):
                    db.delete_server_list(db_server["name"])
                db_server["uptime"] = int((time.time() - db_server["timestamp"])/60)
                for server in serverlist:
                    if server == db_server["name"]:
                        db_server["total_players"] = len(serverlist[server]["players"])
                        db.update_server_list(server, db_server["total_players"], serverlist[server]["firstSeen"] / 1000, uptime=db_server["uptime"], min30_chest_count=db_server["min30_chest_count"], chest_count=db_server["chest_count"], last_chest_count=db_server["last_chest_count"])

            await asyncio.sleep(30)
    
    async def chest_count_check(self):
        async with Corkus() as corkus:
            while True:
                db_server_list = db.get_server_list_all()

                db_server_list_5_plus = [key for key, value in db_server_list.items() if value["uptime"] >= 300]
                
                onlineplayers = await corkus.network.online_players()
                serverlist = onlineplayers.servers
                
                chosen_server_list = [server for server in serverlist if server.name in db_server_list_5_plus]

                players_chests_found = {}

                for chosen_server in chosen_server_list:
                    partial_players = chosen_server.players
                    for partial_player in partial_players:
                        player = await partial_player.fetch()
                        player_chests_found = player.statistics.chests_found
                        players_chests_found[player.username] = player_chests_found

                    db_server = db_server_list[chosen_server.name]
                    if db_server["chest_count"] == None:
                        db_server["chest_count"] = players_chests_found

                    keys_to_delete = [key for key in players_chests_found if not (key in db_server["chest_count"])]
            
                    for key in keys_to_delete:
                        del players_chests_found[key]

                    keys_to_check = [key for key in db_server["chest_count"] if not (key in players_chests_found)]
                    last_players_chests_found = players_chests_found
            
                    for key in keys_to_check:
                        player = await corkus.player.get(key)
                        players_chests_found[key] = player.statistics.chests_found
            
                    c_db_server_chest_count = Counter(db_server["chest_count"])
                    c_players_chests_found = Counter(players_chests_found)
                    server_total_chests_found = int(sum(list((c_players_chests_found - c_db_server_chest_count).values())))

                    db_server["min30_chest_count"] = server_total_chests_found
                    db_server["last_chest_count"] = db_server["chest_count"]
                    db_server["chest_count"] = last_players_chests_found

                    db.update_server_list(db_server["name"], db_server["total_players"], db_server["timestamp"], uptime=db_server["uptime"], min30_chest_count=db_server["min30_chest_count"], chest_count=db_server["chest_count"], last_chest_count=db_server["last_chest_count"])

                await asyncio.sleep(1800)


