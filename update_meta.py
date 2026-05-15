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
# CRAWL METATFT
# =========================

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()