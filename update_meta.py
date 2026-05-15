import os
import json
import gspread

from playwright.sync_api import sync_playwright
from oauth2client.service_account import (
    ServiceAccountCredentials
)

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

rows = [
    ["Comp","AvgPlace","Top4","WinRate"]
]


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

    text = page.locator("body").inner_text()

    browser.close()


lines = text.split("\n")

rows = [["Comp","AvgPlace","Top4","WinRate"]]

for i, line in enumerate(lines):

    if line == "Avg Place":

        try:

            comp = lines[i-10]      # tên comp

            avg = lines[i+1]

            win = lines[i+5]

            top4 = lines[i+9]


            rows.append([
                comp,
                avg,
                top4,
                win
            ])

        except:
            pass


sheet.clear()

sheet.update(
    range_name="A1",
    values=rows
)

print("Meta updated")