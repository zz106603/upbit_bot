import requests
import os
from dotenv import load_dotenv

load_dotenv()
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

# DeepL API를 사용하여 영어 → 한글 번역
def translate_to_korean(text):
    url = "https://api-free.deepl.com/v2/translate"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": "EN",
        "target_lang": "KO"
    }
    try:
        res = requests.post(url, headers=headers, data=data)
        res.raise_for_status()
        return res.json()['translations'][0]['text']
    except Exception as e:
        print(f"❌ 번역 실패: {e}")
        return "(번역 실패)"
