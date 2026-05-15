import os
import json
import gspread

from playwright.sync_api import sync_playwright
from oauth2client.service_account import (
    ServiceAccountCredentials
)

# ---------- GOOGLE ----------

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
    .open("Meta TFT")      # tên FILE
    .worksheet("MetaTFT")  # tên TAB
)


rows = [[
"Comp",
"Carry",
"Units",
"Top4"
]]

# ---------- CRAWL ----------

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

for i,line in enumerate(lines):

    if line == "Top 4 Rate":

        try:

            top4 = lines[i+1]

            units=[]

            for j in range(i-15,i):

                x=lines[j]

                if (
                    len(x)>2
                    and "%" not in x
                    and x not in [
                        "Medium","Hard","Easy",
                        "Fast 8","Fast 9","lvl 7",
                        "S","A","B"
                    ]
                ):
                    units.append(x)

            units=list(dict.fromkeys(units))

            comp = units[0]
            carry = units[1] if len(units)>1 else units[0]

            rows.append([
                comp,
                carry,
                ", ".join(units[:8]),
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