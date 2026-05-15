import os
import json
import gspread

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

print("Google auth OK")

sheet = client.open("MetaTFT").sheet1

sheet.update(
    "A1",
    [["hello"]]
)

print("write ok")