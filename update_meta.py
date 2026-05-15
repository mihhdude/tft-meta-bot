import os
import json
import gspread

from playwright.sync_api import sync_playwright
from oauth2client.service_account import (
    ServiceAccountCredentials
)

# =========================
# GOOGLE SHEETS
# =========================

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
    .open("Meta TFT")      # tên FILE
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

# =========================
# CRAWL METATFT
# =========================

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
        10000
    )

    print("Meta loaded")

    body = page.locator(
        "body"
    ).inner_text()

    lines = body.split("\n")

    count = 0

    for i, line in enumerate(lines):

        if line == "Top 4 Rate":

            try:

                if count >= 10:
                    break

                top4 = lines[i+1]

                units = []

                for j in range(i-18, i):

                    txt = lines[j]

                    if (
                        len(txt) > 2
                        and "%" not in txt
                        and txt not in [
                            "S",
                            "A",
                            "B",
                            "Hard",
                            "Medium",
                            "Easy",
                            "Fast 8",
                            "Fast 9",
                            "lvl 7"
                        ]
                    ):
                        units.append(txt)

                units = list(
                    dict.fromkeys(units)
                )

                if len(units) < 4:
                    continue


                carry = units[0]
                comp = carry


                # ---------- ITEM BUILD ----------

                item_links = page.locator(
                    'a[href*="/items/"]'
                ).all()

                items = []

                for item in item_links:

                    href = item.get_attribute(
                        "href"
                    )

                    if (
                        href
                        and "TFT_Item_"
                        in href
                    ):

                        name = (
                            href
                            .split(
                                "TFT_Item_"
                            )[-1]
                            .replace(
                                "_",
                                " "
                            )
                        )

                        if (
                            name not in items
                        ):
                            items.append(
                                name
                            )


                rows.append([

                    comp,

                    carry,

                    ", ".join(
                        items[:5]
                    ),

                    ", ".join(
                        units[:8]
                    ),

                    top4

                ])

                count += 1

                print(
                    "Added:",
                    comp
                )

            except Exception as e:

                print(e)



    browser.close()



# =========================
# WRITE SHEET
# =========================

sheet.clear()

sheet.update(

    range_name="A1",

    values=rows

)

print(
    "Meta updated OK"
)