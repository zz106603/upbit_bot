from telegram.utils.helpers import escape_markdown
import re
from urllib.parse import quote

# def escape(text):
#     return escape_markdown(text, version=2)

def escape(text: str) -> str:
    # Telegram MarkdownV2 특수문자 전체 이스케이프
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text)

def escape_url(url: str) -> str:
    # MarkdownV2 문법에서 ()는 반드시 백슬래시로 이스케이프되어야 함
    # URL은 그대로 두되 괄호만 수동 이스케이프
    return re.sub(r'([\(\)])', r'\\\1', url)

def build_price_change_message(coin, percent):
    arrow = "📈" if percent >= 0 else "📉"
    return f"{arrow} {coin} {percent:+.2f}%"
