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
    .open("Meta TFT")       # tên FILE
    .worksheet("MetaTFT")   # tên TAB
)

print("Google OK")


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


sheet.clear()

sheet.update(
    range_name="A1",
    values=[[text[:3000]]]
)

print("Meta updated")