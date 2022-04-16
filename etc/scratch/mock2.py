import os
import json
import random
import base64
from pprint import pprint
from io import BytesIO

import requests
import numpy as np
from PIL import Image
from tqdm import tqdm

api = "http://localhost:4000"
N = 10
phrases = [
    "Angel Egotrip",
    "Made Savage",
    "Binary Bark",
    "The Deal",
    "Fiddle Pie",
    "Raid Brigade",
    "Geez God",
    "Mindhack Diva",
    "Sugar Lump",
    "K For Kun",
    "Armor of Odd",
    "Loop Hole Mindset",
    "Asterism Zeevine",
    "Droolbug",
    "Starry Divinity",
    "Zig Wagon",
    "Blu Zoo",
    "Lens Patriot",
    "Doll Throne",
    "Sweetielicious",
    "Krazy Encounter",
    "Strife Life",
    "Ice Minister",
    "Twinkle Doll",
    "Meat Mojo",
    "Evil Rage",
    "Apogee Point",
    "Cluster of Hope",
    "Angel Berry",
    "Mind Pixell",
    "It Was Me",
    "Marker Dee",
    "Ahem Girl",
    "Emoster Pink",
    "Diva Comet",
    "Prep Station",
    "Whack Stack",
    "Cutefest Fizzle",
    "Him Again",
    "Dread Monster",
    "Exit Hound",
    "Mind Trick Poodle",
    "Prom Doll",
    "Rainbow Passion",
    "Cislunar Doll",
    "Bright Nut",
    "Fruit Loop Diva",
    "Grimster",
    "Cynic Poet",
    "Illustrious Doom",
    "Hippo Thump",
    "Cosmotech Junkie",
    "Doppler Thing",
    "Sleep Walker Swag",
    "Take Away Step",
    "Azimuth Mindspace",
    "Black Hole Thing",
    "Singular Desire",
    "Size Does Splatter",
    "Dark Disaster",
    "New Pole Meteorite",
    "Beyond This",
    "Free Fall Matter",
    "Peace Pangs",
    "Shout Out Facts",
    "Prom Storm Diva",
    "Choc O Block",
    "Hug Me Tight",
    "Egoflash",
    "Bold Bazooka",
    "Mind Dweller",
    "Psycho Poodle",
    "Monk Doodles",
    "Star Bit Angel",
    "Chub Bubbly",
    "High Pink",
    "Lunar Doll",
    "Here There and Everywhere",
    "Sweet Pandora",
    "Pill Thinker",
    "I Squad Solace",
    "Just My Thing",
    "Gamma Girl",
    "Stripe Hype",
    "Moonlight Breed",
    "Camerashy Crusader",
    "Singular Mindspeak",
    "Wax M Clean",
    "Fine Sin Ego",
    "Coriolis Extreme",
    "Sting Thing",
    "Alien Coffee Maker",
    "Full Indie Tank",
    "Rainbow Love",
    "Flame Drone",
    "Pixel Poney",
    "Croon Girl",
    "Sublime Ranter",
    "Phase Zun",
    "Angelight Arc",
]
center = [42.9, -78.67]

T = {
    "email": "alice@alice.com",
    "username": "alice",
    "password": "alice",
    "profile": {
        "alias": "alice in wonderland",
        "age": 28,
        "bio": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed pellentesque luctus metus eu accumsan.",
        "handicap": 3.2,
        "mobility": 1,
        "drinking": 2,
        "weather": 2,
    },
    "location": {"location": {"coordinates": center, "type": "Point"}},
}

payloads = list()
payloads.append(T)

for i, phrase in enumerate(phrases):
    if i >= N:
        break
    slug = phrase.lower().replace(" ", "")
    lat, lon = center

    ## IMAGE
    array = np.stack(
        [np.full((300, 300), random.randint(0, 255)) for _ in range(3)], axis=2
    )
    img = Image.fromarray(array.astype("uint8"))
    # im.show()
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    myimage = buffer.getvalue()
    image = dict(img=base64.b64encode(myimage).decode("utf-8"))

    profile = dict(
        alias=phrase.split()[0],
        age=random.randint(18, 81),
        bio="ipsum lorem odus de",
        handicap=random.random() * 18,
        mobility=random.choice(range(0, 3)),
        drinking=random.choice(range(0, 3)),
        weather=random.choice(range(0, 4)),
    )

    location = dict(location=dict(coordinates=[lat, lon], type="Point"))

    payloads.append(
        dict(
            email=slug + "@mail.com",
            username=slug,
            password=slug,
            image=image,
            profile=profile,
            location=location,
        )
    )

pprint(payloads)

for payload in tqdm(payloads):
    print("---")
    print(json.dumps(payload, indent=2))
    response = requests.post(api + "/users", json=payload)
    print(json.dumps(response.json(), indent=2))
    print(response)

# print(f"Success: {ok}/{len(payloads)}")
