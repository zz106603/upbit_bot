from telegram.utils.helpers import escape_markdown

def escape(text):
    return escape_markdown(text, version=2)

def build_price_change_message(coin, percent):
    arrow = "📈" if percent >= 0 else "📉"
    return f"{arrow} {coin} {percent:+.2f}%"
