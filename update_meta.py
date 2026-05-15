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

client = gspread.authorize(
    credentials
)

sheet = (
    client
    .open("Meta TFT")
    .worksheet("MetaTFT")
)

print("Google OK")


rows=[]

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

    rows.append(
        [text[:1000]]
    )

    browser.close()


sheet.clear()

sheet.update(
    values=rows,
    range_name="A1"
)

print("Meta updated")