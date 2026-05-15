import os
import json
import gspread

from playwright.sync_api import sync_playwright
from oauth2client.service_account import (
    ServiceAccountCredentials
)

# ---------------- GOOGLE ----------------

scope = [
'https://spreadsheets.google.com/feeds',
'https://www.googleapis.com/auth/spreadsheets',
'https://www.googleapis.com/auth/drive'
]

creds = json.loads(
    os.environ["GOOGLE_CREDS"]
)

credentials = (
    ServiceAccountCredentials
    .from_json_keyfile_dict(
        creds,
        scope
    )
)

client = gspread.authorize(credentials)

sheet = (
    client
    .open("Meta TFT")
    .worksheet("MetaTFT")
)

rows=[[
"Comp",
"Carry",
"Items",
"Units",
"Top4"
]]

# ---------------- CRAWL ----------------

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page()

    page.goto(
        "https://www.metatft.com/comps",
        timeout=60000
    )

    page.wait_for_timeout(8000)

    body = page.locator(
        "body"
    ).inner_text()

    lines = body.split("\n")

    for i,line in enumerate(lines):

        if line=="Top 4 Rate":

            try:

                top4=lines[i+1]

                units=[]

                for j in range(i-18,i):

                    txt=lines[j]

                    if (
                        len(txt)>2
                        and "%" not in txt
                        and txt not in [
                        "Medium",
                        "Hard",
                        "Fast 8",
                        "Fast 9",
                        "lvl 7",
                        "S"
                        ]
                    ):

                        units.append(txt)

                units=list(
                    dict.fromkeys(units)
                )

                if len(units)<4:
                    continue


                carry = units[0]      # carry chính
                comp = units[0]

                # build item mặc định
                item_map={

                    "Corki":
                    "Guinsoo, IE, Last Whisper",

                    "Vex":
                    "Blue Buff, JG, GS",

                    "Master Yi":
                    "BT, Titan, Guinsoo",

                    "Nunu":
                    "Warmog, Stoneplate, DClaw",

                    "Lulu":
                    "Blue Buff, Shojin, JG"
                }


                items = item_map.get(
                    carry,
                    ""
                )

                rows.append([

                    comp,
                    carry,
                    items,
                    ", ".join(
                        units[:8]
                    ),
                    top4

                ])

            except:
                pass


    browser.close()


sheet.clear()

sheet.update(
    range_name="A1",
    values=rows
)

print("Meta updated")