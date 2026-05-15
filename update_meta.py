import os
import json
import gspread
import re

from playwright.sync_api import sync_playwright
from oauth2client.service_account import ServiceAccountCredentials

# =========================
# TỪ ĐIỂN DỊCH VÀ ĐẢO CHỮ
# =========================

ITEM_DICT = {
    # Đồ chuẩn
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
    "Evenshroud": "Giáp Vai", "NashorsTooth": "Nanh Nashor",
    "AdaptiveHelm": "Mũ Thích Nghi", "SteraksGage": "Móng Vuốt Sterak",
    "HextechGunblade": "Kiếm Súng", "Guardbreaker": "Chùy Xuyên Phá",
    "EdgeOfNight": "Áo Choàng Bóng Tối", "SteadfastHeart": "Trái Tim Kiên Định",
    
    # Đồ Cổ Đại / Artifact / Chế độ Revival
    "RedBuff": "Bùa Đỏ", "GuardianAngel": "Giáp Thiên Thần",
    "MadredsBloodrazor": "Đao Madred", "Leviathan": "Giáp Tâm Linh",
    "UnstableConcoction": "Dược Phẩm Bất Ổn", "SpectralGauntlet": "Găng Ma Quỷ",
    "BattleBunnyCrossbow": "Nỏ Siêu Thú", "StargazerEmblem": "Ấn Chiêm Tinh",
    "ChemicalCapacitorMod": "Lõi Hóa Kỹ", "PsyOps": "Đặc Vụ"
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
    "Sorcerer": "Phù Thủy"
}

def translate_comp_name(eng_name):
    if eng_name == "Unknown": return "Đội hình Chưa Rõ"
    parts = eng_name.split(' ')
    if len(parts) >= 2:
        trait = parts[0]
        champ = " ".join(parts[1:])
        trait_vn = TRAIT_DICT.get(trait, trait)
        return f"{champ} {trait_vn}"
    return eng_name

def clean_raw_item_name(raw_text):
    # Quét sạch 100% mọi tiền tố chứa chữ TFT (kể cả có số hay không)
    clean = re.sub(r'TFT\d*_Item_', '', raw_text)
    clean = re.sub(r'TFT\d*_', '', clean)
    clean = re.sub(r'Tier\d+_', '', clean)
    clean = re.sub(r'AnimaSquadItem_', '', clean)
    clean = clean.replace('Item', '').replace('  ', ' ')
    return clean

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

            // FIX: Lọc lấy tên đội hình chính xác từ text hiển thị
            let lines = row.innerText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
            const ignoreList = ["S", "A", "B", "Hard", "Medium", "Easy", "Fast 8", "Fast 9", "lvl 7", "Situational", "Avg Place", "Pick Rate", "Win Rate", "Top 4 Rate"];
            let compName = lines.find(txt => !ignoreList.includes(txt) && txt.length > 3 && !txt.includes('%') && isNaN(txt)) || "Unknown";

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
                    let items = [...new Set(itemNodes.map(i => i.getAttribute('href').split('/').pop()))];
                    carryItems.push(champName + ": " + items.join(', '));
                    if(!primaryCarry) primaryCarry = champName;
                }
            });

            let pcts = Array.from(row.querySelectorAll('*'))
                .filter(el => el.textContent.includes('%') && el.textContent.length < 7 && el.children.length === 0)
                .map(el => el.textContent.trim());
            let top4 = pcts.length > 0 ? pcts[pcts.length - 1] : "N/A";

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
            vn_name = translate_comp_name(comp['comp'])
            
            # Quét rác cực mạnh trước khi mang đi dịch
            clean_items = clean_raw_item_name(comp['items'])
            vn_items = translate_items(clean_items)
            
            rows.append([vn_name, comp['carry'], vn_items, comp['units'], comp['top4']])
            print(f"Done: {vn_name}")
        except Exception as e:
            print(f"Lỗi dòng {comp['comp']}: {e}")

    browser.close()

# UPDATE
sheet.clear()
sheet.update(range_name="A1", values=rows)
print("Xong rồi nhé ông!")