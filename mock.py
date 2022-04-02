import json
import time
import random
from pprint import pprint

import requests

url = "http://localhost:4000"
scaling = 3
n = 0

foos = ["default", "user:1", "profile:1"]
bars = ["apple", "banana", "carrot", "donut"]

while True:
    data = {
        "event": random.choice(foos),
        "source": "system",
        "payload": json.dumps({random.choice(bars): random.choice(bars)}),
    }
    response = requests.post(url + "/events", json=data)
    n += 1
    interval = random.random() * scaling
    print(n, response, response.json())
    time.sleep(interval)

# # Create 2 users to have a conversation
# user1 = dict(username="user_one", email="one@example.com", password="one")
# response = requests.post(url + "/users", json=user1)
# print(response)
# user1 = response.json().get("data")
# pprint(user1)

# user2 = dict(username="user_two", email="two@example.com", password="two")
# response = requests.post(url + "/users", json=user2)
# user2 = response.json().get("data")
# pprint(user2)

# user3 = dict(username="user_three", email="three@example.com", password="three")
# response = requests.post(url + "/users", json=user3)
# user3 = response.json().get("data")
# pprint(user3)

# # Generate some polite chatter
# verbs = ["eat", "enjoy", "miss", "feel", "touch", "play"]
# possessives = ["her", "his", "their", "our", "your", "my"]
# adjectives = ["happy", "sad", "tall", "old", "sunny", "loud"]
# nouns = ["dog", "cat", "music", "computer", "lamp", "food"]
# emojis = list("🥳😇🍆👑🐈🌜")
# parts = [verbs, possessives, adjectives, nouns, emojis]

# fks = [1, 2, 3]
# for _ in range(10):
#     random.shuffle(fks)
#     src_fk, dst_fk, _ = fks
#     body = " ".join([random.choice(words) for words in parts])
#     message = {"src_fk": src_fk, "dst_fk": dst_fk, "body": body}
#     print(message)
#     response = requests.post(url + "/messages", json=message)
#     print(response)
