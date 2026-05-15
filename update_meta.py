import os
import json
import gspread

from playwright.sync_api import sync_playwright
from oauth2client.service_account import (
    ServiceAccountCredentials
)

# -------------------
# GOOGLE AUTH
# -------------------

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

client = gspread.authorize(
    credentials
)

sheet = (
    client
    .open("Meta TFT")      # tên FILE Google Sheet
    .worksheet("MetaTFT")  # tên TAB
)

print("Google OK")


rows = [[
    "Comp",
    "Carry",
    "Items",
    "Units",
    "Top4"
]]


# -------------------
# CRAWL META TFT
# -------------------

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page()

    page.goto(
        "https://www.metatft.com/comps",
        timeout=60000
    )

    page.wait_for_timeout(
        8000
    )

    text = page.locator(
        "body"
    ).inner_text()

    browser.close()


lines = text.split("\n")


for i, line in enumerate(lines):

    if line == "Top 4 Rate":

        try:

            top4 = lines[i+1]

            units = []

            for j in range(i-18, i):

                txt = lines[j]

                if (
                    len(txt) > 2
                    and "%" not in txt
                    and txt not in [
                        "Medium","Hard","Easy",
                        "Fast 8","Fast 9","lvl 7",
                        "S","A","B"
                    ]
                ):
                    units.append(txt)

            units = list(
                dict.fromkeys(units)
            )

            if len(units) < 2:
                continue


            comp = units[0]
            carry = units[1]

            # item tạm đoán
            items = []

            item_pool = [

                "Infinity Edge",
                "Guinsoo's Rageblade",
                "Last Whisper",
                "Bloodthirster",
                "Jeweled Gauntlet",
                "Warmog's Armor",
                "Sunfire Cape",
                "Blue Buff",
                "Archangel's Staff"

            ]

            for k in range(
                max(i-30,0),
                min(i+30,len(lines))
            ):

                if lines[k] in item_pool:
                    items.append(
                        lines[k]
                    )

            rows.append([

                comp,
                carry,
                ", ".join(items),
                ", ".join(
                    units[:8]
                ),
                top4

            ])

        except:
            pass


sheet.clear()

sheet.update(
    range_name="A1",
    values=rows
)

print("Meta updated")