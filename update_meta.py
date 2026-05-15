import os
import json
import gspread

from playwright.sync_api import sync_playwright
from oauth2client.service_account import ServiceAccountCredentials

# =========================
# TỪ ĐIỂN DỊCH VÀ ĐẢO CHỮ
# =========================

# Dịch Items
ITEM_DICT = {
    "Deathblade": "Kiếm Tử Thần", "LastWhisper": "Cung Xanh",
    "PowerGauntlet": "Găng Bảo Thạch", "JeweledGauntlet": "Găng Bảo Thạch",
    "FrozenHeart": "Tim Băng", "ProtectorsVow": "Lời Thề Hộ Vệ",
    "Crownguard": "Vương Miện", "Bloodthirster": "Huyết Kiếm",
    "GuinsoosRageblade": "Cuồng Đao", "InfinityEdge": "Vô Cực Kiếm",
    "GiantSlayer": "Diệt Khổng Lồ", "WarmogsArmor": "Giáp Máu",
    "GargoyleStoneplate": "Thú Tượng", "BrambleVest": "Áo Choàng Gai",
    "DragonsClaw": "Vuốt Rồng", "Redemption": "Dây Chuyền Chuộc Tội",
    "SunfireCape": "Áo Choàng Lửa", "IonicSpark": "Nỏ Sét",
    "StatikkShiv": "Dao Điện", "ArchangelsStaff": "Quyền Trượng",
    "RabadonsDeathcap": "Mũ Phù Thủy", "Morellonomicon": "Quỷ Thư",
    "SpearOfShojin": "Ngọn Giáo Shojin", "BlueBuff": "Bùa Xanh",
    "TitansResolve": "Quyền Năng", "Quicksilver": "Khăn Giải Thuật",
    "ThiefsGloves": "Găng Đạo Tặc", "HandOfJustice": "Bàn Tay Công Lý",
    "Evenshroud": "Giáp Vai Nguyệt Thần", "NashorsTooth": "Nanh Nashor",
    "AdaptiveHelm": "Mũ Thích Nghi", "SteraksGage": "Móng Vuốt Sterak",
    "HextechGunblade": "Kiếm Súng", "Guardbreaker": "Chùy Xuyên Phá",
    "EdgeOfNight": "Áo Choàng Bóng Tối", "SteadfastHeart": "Trái Tim Kiên Định"
}

# Dịch Hệ/Tộc
TRAIT_DICT = {
    "Meeple": "Tinh Linh Chuông", "Vanguard": "Tiên Phong",
    "Marauder": "Toán Cướp", "Dark Star": "Hắc Tinh",
    "Stargazer": "Chiêm Tinh", "Space Groove": "Hành Tinh",
    "Super": "Siêu Thú", "Cybernetic": "N.O.V.A",
    "Chrono": "Thời Không", "Nomad": "Du Mục",
    "Bruiser": "Đấu Sĩ", "Sniper": "Bắn Tỉa",
    "Challenger": "Thách Đấu", "Invoker": "Dẫn Truyền",
    "Bastion": "Can Trường", "Mage": "Pháp Sư",
    "Sorcerer": "Phù Thủy", "Brawler": "Đấu Sĩ"
}

def translate_comp_name(eng_name):
    """Hàm này để biến 'Meeple Corki' thành 'Corki Tinh Linh Chuông'"""
    parts = eng_name.split(' ')
    if len(parts) >= 2:
        trait = parts[0]
        champ = " ".join(parts[1:])
        # Dịch trait nếu có trong từ điển
        trait_vn = TRAIT_DICT.get(trait, trait)
        return f"{champ} {trait_vn}"
    return eng_name

def translate_items(text):
    for en, vi in ITEM_DICT.items():
        text = text.replace(en, vi)
    return text.replace("_", " ")

# =========================
# GOOGLE SHEETS SETUP
# =========================

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = json.loads(os.environ["GOOGLE_CREDS"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds, scope)
client = gspread.authorize(credentials)
sheet = client.open("Meta TFT").worksheet("MetaTFT")

rows = [["Comp", "Carry", "Items", "Units", "Top4"]]

# =========================
# CRAWL METATFT
# =========================

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.metatft.com/comps", timeout=60000)
    page.wait_for_timeout(10000)

    # Javascript nâng cao để bóc đúng tên Comp và Đồ theo tướng
    comps_data = page.evaluate('''() => {
        let results = [];
        let labels = Array.from(document.querySelectorAll('*')).filter(el => el.textContent.trim() === 'Top 4 Rate' && el.children.length === 0);
        
        labels.forEach((label, index) => {
            if(index >= 10) return; 
            
            let row = label.parentElement;
            for(let i=0; i<8; i++) {
                if(row && row.querySelector('a[href*="/units/"]')) break;
                row = row.parentElement;
            }
            if(!row) return;

            // 1. LẤY TÊN COMP CHUẨN (Thường nằm ở div to nhất có text đầu tiên)
            let nameEl = row.querySelector('div[class*="CompName"]') || row.querySelector('div[style*="font-weight"]');
            let compName = nameEl ? nameEl.innerText.split('\\n')[0].trim() : "Unknown";

            let units = [];
            let carryItems = [];
            let primaryCarry = "";

            let unitNodes = Array.from(row.querySelectorAll('a[href*="/units/"]'));
            unitNodes.forEach(node => {
                let champName = node.getAttribute('href').split('/').pop();
                if (champName.includes('_')) champName = champName.split('_').pop();
                
                if(!units.includes(champName) && champName) units.push(champName);

                let container = node.parentElement;
                let itemNodes = [];
                for(let i=0; i<4; i++) {
                    if(!container) break;
                    if(container.querySelectorAll('a[href*="/units/"]').length > 1) break;
                    let foundItems = Array.from(container.querySelectorAll('a[href*="/items/"]'));
                    if(foundItems.length > 0) {
                        itemNodes = foundItems;
                        break;
                    }
                    container = container.parentElement;
                }
                
                if(itemNodes.length > 0) {
                    let items = [...new Set(itemNodes.map(i => i.getAttribute('href').split('/').pop().replace('TFT_Item_', '')))];
                    carryItems.push(champName + ": " + items.join(', '));
                    if(!primaryCarry) primaryCarry = champName;
                }
            });

            let top4 = "N/A";
            let pct = Array.from(row.querySelectorAll('*')).find(el => el.textContent.includes('%') && el.textContent.length < 7);
            if(pct) top4 = pct.textContent.trim();

            results.push({
                comp: compName,
                carry: primaryCarry || units[0],
                items: carryItems.join('\\n'),
                units: units.join(', '),
                top4: top4
            });
        });
        return results;
    }''')

    for comp in comps_data:
        try:
            # Dịch tên đội hình kiểu 'Meeple Corki' -> 'Corki Tinh Linh Chuông'
            vn_name = translate_comp_name(comp['comp'])
            vn_items = translate_items(comp['items'])
            
            rows.append([vn_name, comp['carry'], vn_items, comp['units'], comp['top4']])
            print(f"Done: {vn_name}")
        except:
            pass

    browser.close()

# UPDATE
sheet.clear()
sheet.update(range_name="A1", values=rows)
print("Xong rồi nhé ông!")