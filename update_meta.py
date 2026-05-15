import os
import json
import gspread

from playwright.sync_api import sync_playwright
from oauth2client.service_account import ServiceAccountCredentials

# =========================
# TỪ ĐIỂN DỊCH TIẾNG VIỆT TFT
# =========================

ITEM_DICT = {
    "Deathblade": "Kiếm Tử Thần", "LastWhisper": "Cung Xanh",
    "PowerGauntlet": "Găng Bảo Thạch", "JeweledGauntlet": "Găng Bảo Thạch",
    "FrozenHeart": "Tim Băng", "ProtectorsVow": "Lời Thề Hộ Vệ",
    "Crownguard": "Vương Miện Hoàng Gia", "Bloodthirster": "Huyết Kiếm",
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

def translate_tft(text, dictionary):
    for en, vi in dictionary.items():
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
print("Google Sheets OK")

rows = [["Comp", "Carry", "Items", "Units", "Top4"]]

# =========================
# CRAWL METATFT BẰNG JS MẠNH MẼ HƠN
# =========================

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.metatft.com/comps", timeout=60000)
    page.wait_for_timeout(10000)
    print("Meta page loaded")

    # Bơm Javascript thẳng vào trình duyệt để bóc tách đúng Tướng nào cầm Đồ nấy
    comps_data = page.evaluate('''() => {
        let results = [];
        let labels = Array.from(document.querySelectorAll('*')).filter(el => el.textContent.trim() === 'Top 4 Rate' && el.children.length === 0);
        
        labels.forEach((label, index) => {
            if(index >= 10) return; // Lấy 10 đội hình đầu
            
            let row = label.parentElement;
            for(let i=0; i<8; i++) {
                if(row && row.querySelector('a[href*="/units/"]')) break;
                row = row.parentElement;
            }
            if(!row) return;

            // 1. TÊN ĐỘI HÌNH
            let allTexts = Array.from(row.querySelectorAll('*'))
                .filter(el => el.children.length === 0)
                .map(el => el.textContent.trim())
                .filter(txt => txt.length > 2 && !txt.includes('%') && isNaN(txt));
            const ignoreList = ["S", "A", "B", "Hard", "Medium", "Easy", "Fast 8", "Fast 9", "lvl 7", "Avg Place", "Pick Rate", "Win Rate", "Top 4 Rate"];
            let compName = allTexts.find(txt => !ignoreList.includes(txt)) || "Unknown Comp";

            // 2. TƯỚNG & TRANG BỊ
            let units = [];
            let carryItems = [];
            let primaryCarry = "";

            let unitNodes = Array.from(row.querySelectorAll('a[href*="/units/"]'));
            unitNodes.forEach(node => {
                let href = node.getAttribute('href');
                let champName = href.split('/').pop();
                if (champName.includes('_')) {
                    let parts = champName.split('_');
                    champName = parts[parts.length - 1]; 
                }
                
                if(!units.includes(champName) && champName) units.push(champName);

                // Gắn đúng đồ cho con tướng đang quét
                let parent = node.parentElement.parentElement; 
                let itemNodes = Array.from(parent.querySelectorAll('a[href*="/items/"]'));
                
                if(itemNodes.length > 0) {
                    let items = itemNodes.map(iNode => {
                        let iHref = iNode.getAttribute('href');
                        let iName = iHref.split('/').pop();
                        if(iName.includes('Item_')) iName = iName.split('Item_')[1];
                        return iName;
                    });
                    carryItems.push(champName + ": " + items.join(', '));
                    if(!primaryCarry) primaryCarry = champName;
                }
            });

            // 3. TỈ LỆ TOP 4
            let top4 = "N/A";
            let top4Container = label.parentElement;
            if(top4Container) {
                let pct = Array.from(top4Container.querySelectorAll('*')).find(el => el.textContent.includes('%'));
                if(pct) top4 = pct.textContent.trim();
            }

            results.push({
                comp: compName,
                carry: primaryCarry || units[0] || "Unknown",
                items: carryItems.join('\\n'), // Ngắt dòng cho mỗi tướng trên Telegram
                units: units.join(', '),
                top4: top4
            });
        });
        return results;
    }''')

    # Dịch ra tiếng Việt và đẩy vào mảng
    for comp in comps_data:
        try:
            comp_name_vn = translate_tft(comp['comp'], TRAIT_DICT)
            items_vn = translate_tft(comp['items'], ITEM_DICT)
            
            rows.append([
                comp_name_vn,
                comp['carry'],
                items_vn,
                comp['units'],
                comp['top4']
            ])
            print(f"Added: {comp_name_vn}")
        except Exception as e:
            print(f"Error mapping: {e}")

    browser.close()

# =========================
# UPDATE SHEETS
# =========================

sheet.clear()
sheet.update(range_name="A1", values=rows)
print("Meta updated OK")