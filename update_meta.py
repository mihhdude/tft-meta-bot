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


# -------------------------
# Login Google
# -------------------------

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

print("✅ Google auth OK")


# -------------------------
# Debug: xem service account
# thấy những file nào
# -------------------------

files = client.openall()

print(
    "Sheets nhìn thấy:",
    [f.title for f in files]
)


# -------------------------
# MỞ FILE GOOGLE SHEET
# ĐỔI TÊN CHO ĐÚNG
# -------------------------

SHEET_NAME = "MetaTFT"

try:

    spreadsheet = client.open(
        SHEET_NAME
    )

    sheet = spreadsheet.sheet1

    sheet.update(
        "A1",
        [["hello"]]
    )

    print(
        "✅ write ok"
    )

except Exception as e:

    print(
        "❌ lỗi:",
        str(e)
    )

    raise