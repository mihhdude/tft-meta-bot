import os
import json
import gspread

from playwright.sync_api import sync_playwright
from oauth2client.service_account import (
    ServiceAccountCredentials
)

# =========================
# GOOGLE SHEETS SETUP
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

client = gspread.authorize(credentials)

sheet = (
    client
    .open("Meta TFT")      # tên FILE
    .worksheet("MetaTFT")  # tên TAB
)

print("Google Sheets OK")

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

    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("https://www.metatft.com/comps", timeout=60000)
    page.wait_for_timeout(10000)

    print("Meta page loaded")

    # 🚀 DÙNG JAVASCRIPT ĐỂ LẤY ITEMS CỰC KỲ CHÍNH XÁC (KHÔNG DỰA VÀO CLASS)
    comps_items = page.evaluate('''() => {
        let results = [];
        
        // Tìm tất cả các nhãn "Top 4 Rate" trên màn hình
        let labels = Array.from(document.querySelectorAll('*'))
            .filter(el => el.textContent.trim() === 'Top 4 Rate' && el.children.length === 0);

        labels.forEach(label => {
            let container = label.parentElement;
            let found = false;
            
            // Lùi dần lên các thẻ cha (tối đa 15 cấp) để tìm khu vực chứa item links
            for(let i = 0; i < 15; i++) {
                if(!container) break;
                
                let links = container.querySelectorAll('a[href*="/items/"]');
                if(links.length > 0) {
                    let items = Array.from(links).map(a => {
                        let parts = a.href.split('TFT_Item_');
                        return parts.length > 1 ? parts[1].replace(/_/g, ' ') : '';
                    }).filter(Boolean);
                    
                    // Lọc trùng lặp đồ
                    results.push([...new Set(items)]);
                    found = true;
                    break;
                }
                container = container.parentElement;
            }
            if(!found) results.push([]);
        });
        
        return results;
    }''')

    # Lấy thông tin Tướng và Tỉ lệ Top 4 bằng Text
    body = page.locator("body").inner_text()
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
                            "S", "A", "B", "Hard", "Medium", "Easy", "Fast 8", "Fast 9", "lvl 7"
                        ]
                    ):
                        units.append(txt)

                units = list(dict.fromkeys(units))

                if len(units) < 4:
                    continue

                carry = units[0]
                comp = carry

                # Lấy Items từ mảng Javascript ghép sang (chống trượt index)
                items = comps_items[count] if count < len(comps_items) else []

                rows.append([
                    comp,
                    carry,
                    ", ".join(items[:5]),
                    ", ".join(units[:8]),
                    top4
                ])

                count += 1
                print("Added:", comp)

            except Exception as e:
                print(f"Error parsing comp {count}: {e}")

    browser.close()

# =========================
# WRITE SHEET
# =========================

sheet.clear()
sheet.update(range_name="A1", values=rows)

print("Meta updated OK")