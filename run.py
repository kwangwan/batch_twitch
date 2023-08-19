import re
import json
import socket
import time
from datetime import datetime

from emoji import demojize
from elasticsearch import Elasticsearch, helpers

with open("config.json", "r") as f:
    config = json.load(f)


OAUTH = config["oauth"]
TWITCH_ID = config["twitch_id"]
CHANNELS = "#"+",#".join(config["channels"])
OUTPUT_FORMATS = config["output_formats"]
ELASTICSEARCH = config["elasticsearch"]
ELASTICSEARCH_INDEX = config["elasticsearch_index"]
ELASTICSEARCH_BULK_SIZE = config["elasticsearch_bulk_size"]


privmsg = re.compile(":[a-z0-9_]{1,}![a-z0-9_]{1,}@[a-z0-9_]{1,}.tmi.twitch.tv PRIVMSG #")
connectionmsg1 = re.compile(f":tmi.twitch.tv")
connectionmsg2 = re.compile(f":{TWITCH_ID}!{TWITCH_ID}@{TWITCH_ID}.tmi.twitch.tv JOIN #")
connectionmsg3 = re.compile(f":{TWITCH_ID}.tmi.twitch.tv 353 {TWITCH_ID}")
channel_name = re.compile(f"[a-z0-9_]{1,} :")


items= []


def __connect_es():
    return Elasticsearch(**ELASTICSEARCH)


def __update_elk():
    global items
    if len(items) == 0:
        return None
    item_copy = items[:]
    items = []
    es = __connect_es()
    print(item_copy)
    res = helpers.bulk(client=es, actions=item_copy)
    print(res)
    print(f">> {len(item_copy)}")


def __collect_data(chat):
    current_datetime = datetime.utcnow()
    channel_name = chat.split(" :")[0]
    chat = " :".join(chat.split(" :")[1:])
    log = f"{current_datetime.strftime('%Y-%m-%d %H:%M:%S')}\t{channel_name}\t{chat}"
    print(log)
    if "textfile" in OUTPUT_FORMATS:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        with open(f"log_{today}.txt", "a") as f:
            f.write(log)
            f.write("\n")
    if "elasticsearch" in OUTPUT_FORMATS:
        _id = f"{channel_name}_{current_datetime.timestamp()}"
        item = {
            "_index": ELASTICSEARCH_INDEX,
            "_id": _id,
            "_source":{
                "channel": channel_name,
                "chat": chat,
                "datetime": current_datetime
            }
        }
        global items
        items.append(item)
        if len(items) >= ELASTICSEARCH_BULK_SIZE:
            __update_elk()


# https://dev.twitch.tv/docs/irc/
# https://twitchapps.com/tmi/
def __get_chat(retry_time=60):
    time_start = time.time()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server = "irc.chat.twitch.tv"
    port = 6667
    sock.connect((server, port))
    sock.send(f"PASS {OAUTH}\n".encode("utf-8"))
    sock.send(f"NICK {TWITCH_ID}\n".encode("utf-8"))
    sock.send(f"JOIN {CHANNELS}\n".encode("utf-8"))
    while (time.time()-time_start) <= retry_time*60:
        response = sock.recv(2048).decode("utf-8")
        if response.startswith("PING"):
            sock.send("PONG\n".encode("utf-8"))
        elif len(response) > 0:
            if (re.search(connectionmsg1, response)
                or re.search(connectionmsg2, response)
                or re.search(connectionmsg3, response)):
                continue
            chats = demojize(response)
            chats = re.sub(privmsg, "", chats)
            for chat in [chat.replace("\r", "") for chat in chats.split("\n") if chat != ""]:
                __collect_data(chat)
    if "elasticsearch" in OUTPUT_FORMATS:
        __update_elk()
    sock.close()
    return None
    
    
def run(retry_time=60):
    while True:
        __get_chat(retry_time=retry_time)
    

if __name__ == "__main__":
    run(retry_time=60)
