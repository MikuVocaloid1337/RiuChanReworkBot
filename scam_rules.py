# scam_rules.py

SCAM_KEYWORDS = [
    "заработок", "инвестиции", "быстрый доход",
    "пассивный доход", "без вложений", "прямо сейчас", "гарантированно",
    "доход от", "удаленная работа", "удалённая работа", "ставки", "1xbet", "казино", "бинанс", "crypto", "бинарные опционы", "Места ограничены", "места ограничены",
    "высокая оплата", "высокой оплатой", "Занятость", "занятость"
]

SCAM_DOMAINS = [
    "t.me/", "bit.ly/", "binance", "1xbet", "rich-", "profit", "earn", "drop", "crypto", "invest", "fastmoney"
]

import re
SCAM_PATTERNS = [
    re.compile(r"зараб.*\d+\s*(руб|₽|доллар|$)", re.IGNORECASE),
    re.compile(r"(инвест|вложи).*гарант", re.IGNORECASE),
    re.compile(r"(https?:\/\/)?(www\.)?(t\.me|bit\.ly|tinyurl|taplink)\.com\/[^\s]+", re.IGNORECASE),
]
