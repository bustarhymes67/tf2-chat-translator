"""TF2 chat translator.

Reads TF2's chat from console.log (the -condebug launch option), translates it to English
and shows it in a see-through overlay over the game. In a "chat" mode it also says each
translation in TF2's chat for everyone (over RCON: run Setup first).

Start it with "Start Translator.bat" and pick a mode, or:
    python translator.py --languages russian|all --output overlay|chat

In game, press F8 to unlock the overlay:
  drag            move it (saved when you lock it again)
  left-click      copy that line's translation
  right-click     copy the original message
  the buttons     switch between Russian only and All languages
Press F8 again to lock it (clicks go through to the game again).
"""

import argparse
import ctypes
import ctypes.wintypes
import json
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request

from rcon import Rcon

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")

DEFAULTS = {
    "log_path": r"C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\tf\console.log",
    "target_lang": "en",
    "languages": "all",        # "russian": only lines in the Russian alphabet; "all": every language
    "output": "overlay",       # "overlay": only you see it; "chat": also said in chat for everyone
    "toggle_key": "F8",
    "x": 20,
    "y": 520,
    "width": 620,
    "max_lines": 6,
    "line_seconds": 15,
    "font_size": 13,
    "rcon_port": 27069,
    "rcon_password": "",       # made by setup_tf2.py, kept only in config.json on this PC
}

CHAT_RE = re.compile(
    r"^(?P<dead>\*DEAD\*|\*SPEC\*)?\s*(?P<team>\(TEAM\))?\s*(?P<name>.+?) :  (?P<msg>.+)$"
)
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
# Letters only Turkish (and Azerbaijani) use, plus common words for Turks who
# type without them.
TURKISH_LETTERS_RE = re.compile(r"[ğĞşŞıİ]")  # not re.I: that makes ı and İ match a plain i
TURKISH_RE = re.compile(r"\b(?:amk|aq|amq|knk|kanka|naber|nbr|nasilsin|lan|olm|olum|abi|"
                        r"bir|ve|degil|yok|evet|hayir|tamam|neden|nasil|simdi|burda|orda|oyun|"
                        r"takim|hile|hileci|ben|sen|biz|siz|benim|senin|cok|iyi|kotu|sagol|"
                        r"tesekkurler|merhaba|selam|salak|aptal|yani|hadi|bekle|neyse|bence|"
                        r"herkes|nerde|kardes|gel|bak|napiyon|noldu|sikerim|orospu|pic)\b", re.I)
# Common words typed without Turkish letters that Google gets wrong that way
# ("takim kotu" came back as "such a cat"). Put back before translating.
TURKISH_SPELLING = dict(pair.split("=") for pair in (
    "takim=takım|takima=takıma|takimi=takımı|kotu=kötü|kotusun=kötüsün|cok=çok|degil=değil|"
    "guzel=güzel|simdi=şimdi|hayir=hayır|tesekkurler=teşekkürler|tesekkur=teşekkür|sagol=sağol|"
    "nasil=nasıl|nasilsin=nasılsın|kardes=kardeş|icin=için|hic=hiç|boyle=böyle|soyle=söyle|"
    "gor=gör|gordum=gördüm|gorduk=gördük|dusman=düşman|yardim=yardım|saldir=saldır|"
    "saldirin=saldırın|oldur=öldür|oldurun=öldürün|olduruyor=öldürüyor|olen=ölen|cik=çık|"
    "cikin=çıkın|gec=geç|bos=boş|kac=kaç|lutfen=lütfen|iyilestir=iyileştir|ust=üst|"
    "arkadas=arkadaş|arkadaslar=arkadaşlar|sagdan=sağdan|yavas=yavaş|hizli=hızlı|"
    "kullaniyor=kullanıyor|aptalsin=aptalsın|salaksin=salaksın|kotuyuz=kötüyüz|guclu=güçlü|"
    "cunku=çünkü|baslayalim=başlayalım|kazandik=kazandık|ucuncu=üçüncü").split("|"))
TURKISH_WORD_RE = re.compile(r"\b[a-z]+\b", re.I)


# English gamer chat Google takes for another language ("ez" Basque, "kys" Danish, "rekt" Esperanto).
CHAT_SLANG = set("gg ggs ggwp wp ez ezz ezpz gl hf glhf rekt kys bruh lol lel lul kek xd xdd lmao lmfao "
                 "rofl omg wtf afk brb ty thx np gj nt mb idc idk ikr smh tbh imo irl ffs stfu gtfo "
                 "noob nub n00b pog poggers sus ok k kk".split())
WORD_RE = re.compile(r"\w+")
# Common English and TF2 words: a plain-letter line made mostly of these is English and isn't sent to
# Google at all. Sending every English line got Google's "too many requests" in a busy lobby.
ENGLISH_WORDS = CHAT_SLANG | set("""
a an the i me my mine you your yours u ur he him his she her it its we us our they them their this that
these those is am are was were be been being do does did done dont doesnt didnt isnt arent wasnt cant
cannot wont wouldnt couldnt shouldnt im ive id ill youre youve hes shes its were theyre thats whats
have has had having will would can could should shall may might must not no yes yeah yea yep nah nope
and or but if so then than because cause cuz bc just only also too very really still even again ever
never always now here there where when why how what who whom which while all any some every each
other another more most less much many few lot lots of in on at to from for with without about into
out up down off over under after before by as like get got go going gone went come came coming make
made take took give gave see saw seen look know knew think thought want need say said tell told play
playing played win won lose lost kill killed killing die died dead dying shoot shot help stop try
let keep put use used one two three four five first last good bad bro dude man guys guy team enemy
enemies game games match map round time back well right left fuck fucking fucked shit damn hell ass
bitch hacker hackers cheater cheaters cheating cheat cheats bot bots hack hacks aimbot kick vote ban
report spy spies sniper snipers medic heavy scout pyro engi engie engineer demo demoman soldier sentry
uber dispenser tele teleporter intel cart point push defend attack crit crits nice great sorry thanks
thank please lmao haha hahaha yo hey hi hello bye gl hf rip lag laggy ping server wait fast slow
ready oh wow hehe hate love welcome random unfair idiot stupid meme sry cool fun funny best worst
""".split())


def looks_english(msg):
    """True for a line in plain letters where most words are common English ones: "spy is crocket",
    "nice shot". "hola amigos" or "hallo allemaal" still go to the translator."""
    if re.search(r"[^\x00-\x7f]", msg):
        return False
    words = WORD_RE.findall(msg.lower())
    return not words or sum(w in ENGLISH_WORDS for w in words) * 2 > len(words)


def not_really_foreign(msg, text):
    """True for an English line Google guessed as another language: its "translation" is the same
    text ("bruh", "1v1 me", "f1"), or it's only gamer slang ("gg ez", "kys")."""
    def bare(s):
        return "".join(WORD_RE.findall(s.lower()))
    words = WORD_RE.findall(msg.lower())
    return bare(text) == bare(msg) or bool(words) and all(w in CHAT_SLANG for w in words)


def turkish(msg):
    return bool(TURKISH_LETTERS_RE.search(msg) or TURKISH_RE.search(msg))


def turkish_spelling(msg):
    def fix(m):
        word = m.group()
        fixed = TURKISH_SPELLING.get(word.lower())
        return fixed.upper() if fixed and word.isupper() and len(word) > 1 else fixed or word
    return TURKISH_WORD_RE.sub(fix, msg)


KEY_COLOR = "#010101"  # painted pixels of this color become transparent
UNLOCKED_BG = "#1e1e1e"
HISTORY_SIZE = 50


def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def on_screen(x, y):
    """True if a connected monitor shows the point x, y."""
    return bool(ctypes.windll.user32.MonitorFromPoint(ctypes.wintypes.POINT(x, y), 0))


# The overlay's two buttons (shown while it's unlocked): setting value -> its text.
LANGUAGE_MODES = {"russian": "Russian only", "all": "All languages"}


def parse_chat(line):
    m = CHAT_RE.match(line.strip())
    if not m:
        return None
    return m.group("name"), m.group("msg"), bool(m.group("team"))


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=6) as resp:
        return json.loads(resp.read().decode("utf-8"))


def google(text, target, source="auto"):
    data = get_json("https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(
        {"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text}))
    return "".join(part[0] for part in data[0] if part[0]), (data[2] or "?")


def google_chrome(text, target, source="auto"):
    """The endpoint Chrome's translate extension uses: Google limits it separately."""
    data = get_json("https://clients5.google.com/translate_a/t?" + urllib.parse.urlencode(
        {"client": "dict-chrome-ex", "sl": source, "tl": target, "q": text}))
    first = data[0]
    return (first[0], first[1]) if isinstance(first, list) else (first, "?")


def mymemory(text, target, source="auto"):
    """Free with a daily limit. It needs the source language, so it only takes
    Cyrillic messages (as Russian) and Turkish-looking ones."""
    if source == "auto":
        source = "ru" if CYRILLIC_RE.search(text) else "tr" if turkish(text) else None
    if not source:
        raise ValueError("source language unknown")
    data = get_json("https://api.mymemory.translated.net/get?" + urllib.parse.urlencode(
        {"q": text, "langpair": f"{source}|{target}"}))
    if data.get("responseStatus") != 200:
        raise ValueError(data.get("responseDetails") or "MyMemory error")
    return data["responseData"]["translatedText"], source


TRANSLATORS = [google, google_chrome, mymemory]
resting_until = {}   # translator -> time it may be tried again after "too many requests"
cache = {}           # (text, target, source) -> (translation, lang): chat repeats a lot


def translate(text, target, source="auto"):
    """Returns (translation, source_lang). Tries free services in turn: one that
    says "too many requests" is left alone for 15 minutes."""
    if (text, target, source) in cache:
        return cache[(text, target, source)]
    error = None
    for translator in TRANSLATORS:
        if resting_until.get(translator, 0) > time.time():
            continue
        try:
            result = translator(text, target, source)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                resting_until[translator] = time.time() + 15 * 60
                print(f"Translator: {translator.__name__} said {e.code} (too many requests): "
                      f"not asked again for 15 minutes", flush=True)
            error = e
            continue
        except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
            error = e
            continue
        if len(cache) > 500:
            cache.clear()
        if source != "auto":
            result = result[0], source
        cache[(text, target, source)] = result
        return result
    raise error or RuntimeError("every translation service is resting")


def claim_instance(name):
    """True if no other program holds this name, which it then keeps for as long
    as this process runs."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW(None, False, name)  # released when this process exits
    return ctypes.get_last_error() != 183  # ERROR_ALREADY_EXISTS


def single_instance(name, message="Already running in another window; close that one first."):
    """Exits if this script is already running (e.g. its .bat was opened twice),
    so chat doesn't get translated twice and Steam/Google aren't asked twice."""
    if not claim_instance(name):
        if ctypes.windll.kernel32.GetConsoleWindow():
            print(message)
        else:  # started without a console: a print would go nowhere
            ctypes.windll.user32.MessageBoxW(None, message, "TF2 Chat Translator", 0x40)
        sys.exit(1)


def tail(path, out):
    """Pushes each new line appended to path. Starts at the end of the file."""
    while not os.path.exists(path):
        time.sleep(1)
    f = open(path, "rb")
    f.seek(0, os.SEEK_END)
    buf = b""
    while True:
        chunk = f.read()
        if chunk:
            buf += chunk
            *lines, buf = buf.split(b"\n")
            for raw in lines:
                out.put(raw.decode("utf-8", errors="replace").rstrip("\r"))
        else:
            # File was recreated or truncated (e.g. TF2 restarted): start over.
            try:
                if os.path.getsize(path) < f.tell():
                    f.close()
                    f = open(path, "rb")
                    buf = b""
            except OSError:
                pass
            time.sleep(0.15)


def translate_chat(msg, target):
    """Google spots Turkish typed without its letters on its own ("sniperi
    oldurun" -> tr), but not always ("takim kotu" -> Polish), and translates it
    better with the letters put back. Common Turkish words settle it."""
    text, lang = translate(msg, target)
    if CYRILLIC_RE.search(msg) or lang == target and not TURKISH_LETTERS_RE.search(msg):
        return text, lang
    if lang == "tr" or turkish(msg):
        fixed = turkish_spelling(msg)
        if fixed != msg or lang != "tr":
            return translate(fixed, target, "tr")
    return text, lang


# Short Russian chat as TF2 players mean it. Google gets one- or two-word lines wrong without
# context ("стой" -> "stand" where a player means "wait", "дурни" read as something else), so a
# line made only of these words is translated from here, word by word or as a whole phrase. Lowercase, with ё written as е. Anything else still goes to Google.
RUSSIAN_PHRASES = {
    "не сдавай": "don't give up", "не сдавайтесь": "don't give up", "иди нахуй": "fuck off",
    "пошел нахуй": "fuck off", "пошел ты": "screw you", "держите точку": "hold the point",
    "толкайте телегу": "push the cart", "на точку": "to the point", "за мной": "follow me",
    "что за": "what the", "кто читер": "who is cheating", "он читер": "he's cheating",
    "это читер": "that's a cheater", "кикните его": "kick him", "спасибо медик": "thanks medic",
    "нужен медик": "need a medic", "нужен хил": "need healing", "у них шпион": "they have a spy",
    "шпион здесь": "spy here", "сзади шпион": "spy behind", "все сюда": "everyone here",
    "давай давай": "come on come on", "ну давай": "come on", "ни хрена": "no way",
}
RUSSIAN_WORDS = {
    "стой": "wait", "стоп": "stop", "стойте": "wait", "дурни": "fools", "дурень": "fool", "дурак": "fool",
    "идиот": "idiot", "идиоты": "idiots", "дебил": "moron", "дебилы": "morons", "тупой": "stupid",
    "тупые": "dumb", "лох": "loser", "лохи": "losers", "нуб": "noob", "нубы": "noobs", "бот": "bot",
    "боты": "bots", "читер": "cheater", "читеры": "cheaters", "читы": "hacks", "аим": "aimbot",
    "кик": "kick", "кикните": "kick him", "голосуйте": "vote", "лаги": "lag", "лагает": "it's lagging",
    "пинг": "ping", "медик": "medic", "медика": "medic", "хил": "heal", "хилл": "heal", "хильте": "heal",
    "лечи": "heal me", "убер": "uber", "уберка": "uber", "шпион": "spy", "спай": "spy", "снайпер": "sniper",
    "снайпера": "sniper", "инж": "engi", "инженер": "engineer", "пулемет": "sentry", "турель": "sentry",
    "точка": "the point", "точку": "the point", "телега": "the cart", "тележка": "the cart",
    "толкайте": "push", "держите": "hold", "назад": "back", "вперед": "go forward", "отходим": "fall back",
    "бегите": "run", "сюда": "over here", "туда": "over there", "где": "where", "кто": "who",
    "что": "what", "че": "what", "чё": "what", "зачем": "why", "почему": "why", "как": "how",
    "го": "go", "гоу": "go", "давай": "come on", "давайте": "come on", "помогите": "help",
    "помоги": "help me", "гг": "gg", "изи": "ez", "лол": "lol", "ахах": "haha", "ахаха": "haha",
    "хаха": "haha", "пж": "please", "пжл": "please", "пожалуйста": "please", "спс": "thanks",
    "спасибо": "thanks", "сяб": "thanks", "норм": "fine", "ок": "ok", "окей": "ok", "да": "yes",
    "нет": "no", "неа": "nope", "ага": "yeah", "привет": "hi", "здарова": "hey", "пока": "bye",
    "удачи": "good luck", "красава": "nice one", "красавчик": "nice one", "молодец": "well done",
    "хорош": "nice", "круто": "cool", "жесть": "insane", "капец": "damn", "блин": "damn",
    "бля": "fuck", "блять": "fuck", "блядь": "fuck", "сука": "bitch", "пиздец": "this is fucked",
    "нахуй": "fuck off", "мда": "hmm", "ну": "well", "ладно": "alright", "понятно": "got it",
    "ясно": "got it", "сорян": "sorry", "сори": "sorry", "извини": "sorry", "опять": "again",
    "снова": "again", "все": "everyone", "всем": "everyone", "ты": "you", "он": "he", "они": "they",
    "мы": "we", "я": "I", "тут": "here", "здесь": "here",
}


def russian_chat(text):
    """The English for a short Russian line made only of the words above (numbers are kept),
    or None to ask Google."""
    words = [w.replace("ё", "е") for w in WORD_RE.findall(text.lower())]
    if not words or len(words) > 4 or not any(CYRILLIC_RE.search(w) for w in words):
        return None
    phrase = " ".join(w for w in words if not w.isdigit())
    if phrase in RUSSIAN_PHRASES:
        names = [w for w in words if w.isdigit()]
        return " ".join(names + [RUSSIAN_PHRASES[phrase]])
    if all(w.isdigit() or w in RUSSIAN_WORDS for w in words):
        return " ".join(w if w.isdigit() else RUSSIAN_WORDS[w] for w in words)
    return None


def worker(cfg, lines, results, said=None):
    """Translates each chat line from `lines` and puts the result in `results`.
    said: lines this program said in chat itself, which come back in console.log: skipped."""
    said = said if said is not None else set()
    while True:
        parsed = parse_chat(lines.get())
        if not parsed:
            continue
        name, msg, team = parsed
        if msg.strip() in said:
            continue  # our own translation, said in chat a moment ago
        if cfg["languages"] == "russian" and not CYRILLIC_RE.search(msg):
            continue  # Russian only: a line without the Russian alphabet isn't sent anywhere
        if not WORD_RE.search(msg):
            continue
        if cfg["target_lang"] == "en" and looks_english(msg):  # not worth one of Google's requests
            continue
        try:
            known = russian_chat(msg) if cfg["target_lang"] == "en" else None
            text, lang = (known, "ru") if known else translate_chat(msg, cfg["target_lang"])
        except Exception:
            # Only lines that surely aren't English say they failed: the rest are most likely English.
            if not (CYRILLIC_RE.search(msg) or turkish(msg)):
                continue
            text, lang = msg + "  (translation failed)", "?"
        if lang == cfg["target_lang"]:
            continue
        if lang != "?" and not CYRILLIC_RE.search(msg) and not_really_foreign(msg, text):
            continue
        results.put({"name": name, "text": text, "original": msg, "lang": lang, "team": team})


# --- saying translations in chat (the "chat" modes) ------------------------------------

CHAT_LIMIT = 127  # bytes TF2 accepts in one chat message


class ChatLimit:
    """TF2's chat spam limit, as the server runs it (CBasePlayer::CanPlayerTalk in Valve's
    source-sdk-2013): 0.66 s between lines, plus two token buckets (4 lines, one more every
    3 s; 30 lines, one more every 10 s). A refused line still costs a token, so lines are only
    sent when they'll get through."""
    GAP = 0.66
    MARGIN = 0.15
    GAP_MARGIN = 0.15

    def __init__(self):
        self.talked = self.attempted = time.time()
        self.tier1, self.tier2 = 1.0, 10.0

    def note(self, at=None):
        """A chat line reached the server."""
        at = time.time() if at is None else at
        elapsed = at - self.attempted
        self.attempted = self.talked = at
        per_msg = 3.0 - min(0.0, self.tier1)
        self.tier1 = max(-2.5, min(4.0, self.tier1 + max(0.0, elapsed / per_msg)) - 1.0)
        if self.tier1 > 0:
            self.tier2 = max(0.0, min(30.0, self.tier2 + max(0.0, elapsed / 10.0)) - 1.0)

    def wait(self, at=None):
        """Seconds until a line sent would get through (0: now)."""
        at = time.time() if at is None else at
        need = 2.0 + self.MARGIN
        per_msg = 3.0 - min(0.0, self.tier1)
        ready = max(self.talked + self.GAP + self.GAP_MARGIN,
                    self.attempted + (need - self.tier1) * per_msg,
                    self.attempted + (need - self.tier2) * 10.0)
        return max(0.0, ready - at)


def fits(text, limit=CHAT_LIMIT):
    return len(text.encode("utf-8")) <= limit


def cut_to(text, limit=CHAT_LIMIT):
    """text cut short to `limit` bytes, at a space where possible."""
    if fits(text, limit):
        return text
    cut = len(text.encode("utf-8")[:limit - 3].decode("utf-8", "ignore"))
    space = text.rfind(" ", 0, cut)
    return text[:space if space > cut // 2 else cut].rstrip() + "..."


def console_safe(text):
    """Text that can't break out of a quoted console command (a player could type `x"; quit`)."""
    return text.replace('"', "'").replace(";", ",").replace("\n", " ").replace("\r", " ")


def chat_text(entry):
    return console_safe(f"{entry['name']} says: {entry['text']}")


def next_chat_line(waiting):
    """Takes the next line to say from `waiting` (a list of entries, oldest first). When several
    wait, they go out together as one line, "A says: x | B says: y", as TF2 lets few lines through."""
    command = "say_team" if waiting[0]["team"] else "say"
    text = chat_text(waiting.pop(0))
    while waiting and ("say_team" if waiting[0]["team"] else "say") == command \
            and fits(f"{text} | {chat_text(waiting[0])}"):
        text += " | " + chat_text(waiting.pop(0))
    return command, cut_to(text)


def chat_sender(cfg, entries, said, status):
    """Background thread: says each translation from `entries` in TF2's chat over RCON, as fast
    as TF2's spam limit allows. Team chat is answered in team chat."""
    rcon, limit, waiting = Rcon(cfg["rcon_port"], cfg["rcon_password"]), ChatLimit(), []
    connected = False
    while True:
        timeout = None if not waiting else max(0.05, limit.wait())
        try:
            waiting.append(entries.get(timeout=timeout))
            while not entries.empty():
                waiting.append(entries.get_nowait())
        except queue.Empty:
            pass
        waiting = waiting[-8:]  # in a flood, old lines don't matter any more
        if not waiting or limit.wait() > 0:
            continue
        command, text = next_chat_line(waiting)
        try:
            if not connected:
                rcon.connect()
                connected = True
                status.put("Connected to TF2: translations go to chat")
            rcon.command(f'{command} "{text}"')
            said.add(text.strip())
            if len(said) > 50:
                said.pop()
            limit.note()
        except PermissionError:
            status.put("TF2 refused the RCON password: run Setup again, then restart TF2")
            connected = False
            time.sleep(10)
        except OSError:
            if connected:
                status.put("Lost TF2's RCON connection: retrying")
            connected = False
            rcon.close()
            time.sleep(3)


# Keys by name, as Windows numbers them (virtual-key codes).
NAMED_KEYS = {"END": 0x23, "HOME": 0x24, "INSERT": 0x2D, "DELETE": 0x2E, "PAGEUP": 0x21, "PAGEDOWN": 0x22,
              "PAUSE": 0x13, "SCROLLLOCK": 0x91}


def key_to_vk(key):
    key = key.strip().upper().replace(" ", "")
    if key.startswith("F") and key[1:].isdigit():
        return 0x70 + int(key[1:]) - 1
    if len(key) == 1 and key.isalnum():
        return ord(key)
    if key in NAMED_KEYS:
        return NAMED_KEYS[key]
    raise ValueError(f"Unsupported key {key!r}, use F1-F24, a letter or digit, or one of {', '.join(NAMED_KEYS)}")


def hotkey_listener(vk, on_press, name="the toggle key"):
    """Global hotkey: fires even while TF2 has focus."""
    user32 = ctypes.windll.user32
    MOD_NOREPEAT, WM_HOTKEY = 0x4000, 0x0312
    if not user32.RegisterHotKey(None, 1, MOD_NOREPEAT, vk):
        print(f"Could not register {name} (another program may be using it, and Windows keeps F12 for itself).")
        return
    msg = ctypes.wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == WM_HOTKEY:
            on_press()


def set_click_through(root, enabled):
    user32 = ctypes.windll.user32
    hwnd = user32.GetParent(root.winfo_id())
    GWL_EXSTYLE = -20
    WS_EX_TRANSPARENT = 0x20
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    # layered | toolwindow (no taskbar/alt-tab) | noactivate (never steals focus from TF2)
    style |= 0x80000 | 0x80 | 0x08000000
    style = style | WS_EX_TRANSPARENT if enabled else style & ~WS_EX_TRANSPARENT
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)


class Overlay:
    def __init__(self, cfg):
        self.cfg = cfg
        self.history = []   # newest last; each entry is a result dict plus "expires"
        self.unlocked = False
        self.status = ""    # short feedback shown in unlocked mode, e.g. "Copied"
        self.press = None   # drag/click state while a mouse button is down

        self.root = root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        self.line_h = cfg["font_size"] * 2 + 6
        height = (cfg["max_lines"] + 1) * self.line_h + 10
        if not on_screen(cfg["x"] + 40, cfg["y"] + 10):
            cfg["x"], cfg["y"] = 20, 520  # its monitor isn't connected now: back to the main screen
        root.geometry(f"{cfg['width']}x{height}+{cfg['x']}+{cfg['y']}")
        root.configure(bg=KEY_COLOR)
        root.attributes("-transparentcolor", KEY_COLOR)
        self.canvas = c = tk.Canvas(root, bg=KEY_COLOR, highlightthickness=0)
        c.pack(fill="both", expand=True)
        self.font = ("Segoe UI Semibold", cfg["font_size"])
        self.small_font = ("Segoe UI", max(9, cfg["font_size"] - 3))

        c.bind("<ButtonPress-1>", self._press)
        c.bind("<B1-Motion>", self._motion)
        c.bind("<ButtonRelease-1>", self._release)
        c.bind("<Button-3>", self._copy_original)
        root.update_idletasks()
        set_click_through(root, True)

    # --- lock / unlock -------------------------------------------------------

    def toggle(self):
        self.unlocked = not self.unlocked
        self.status = ""
        set_click_through(self.root, not self.unlocked)
        self.canvas.configure(bg=UNLOCKED_BG if self.unlocked else KEY_COLOR)
        if not self.unlocked:
            self.cfg["x"], self.cfg["y"] = self.root.winfo_x(), self.root.winfo_y()
            save_config(self.cfg)
        self.redraw()

    # --- mouse (only reaches us while unlocked) --------------------------------

    def _entry_under_mouse(self):
        for tag in self.canvas.gettags("current"):
            if tag.startswith("e"):
                return self.history[int(tag[1:])]
        return None

    def _mode_under_mouse(self):
        for tag in self.canvas.gettags("current"):
            if tag.startswith("mode_"):
                return tag[5:]
        return None

    def set_languages(self, mode):
        """A button: Russian only, or All languages. Saved, and used from the next chat line."""
        if mode in LANGUAGE_MODES and mode != self.cfg["languages"]:
            self.cfg["languages"] = mode
            save_config(self.cfg)
            self._show_status(f"Translating: {LANGUAGE_MODES[mode].lower()}")

    def _press(self, e):
        mode = self._mode_under_mouse()
        if mode:
            self.press = None
            self.set_languages(mode)
            return
        self.press = {
            "x": e.x_root, "y": e.y_root,
            "wx": self.root.winfo_x(), "wy": self.root.winfo_y(),
            "entry": self._entry_under_mouse(), "dragging": False,
        }

    def _motion(self, e):
        p = self.press
        if not p:
            return
        dx, dy = e.x_root - p["x"], e.y_root - p["y"]
        if not p["dragging"] and abs(dx) + abs(dy) < 4:
            return  # small wobble during a click is not a drag
        p["dragging"] = True
        self.root.geometry(f"+{p['wx'] + dx}+{p['wy'] + dy}")

    def _release(self, _e):
        p, self.press = self.press, None
        if p and not p["dragging"] and p["entry"]:
            self._copy(f'{p["entry"]["name"]} says: {p["entry"]["text"]}', "Copied translation")

    def _copy_original(self, _e):
        entry = self._entry_under_mouse()
        if entry:
            self._copy(f'{entry["name"]} says: {entry["original"]}', "Copied original")

    def _copy(self, text, status):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._show_status(status)

    def _show_status(self, status):
        self.status = status
        self.redraw()
        self.root.after(1500, self._clear_status, status)

    def _clear_status(self, status):
        if self.status == status:
            self.status = ""
            self.redraw()

    # --- drawing -------------------------------------------------------------

    def add(self, entry):
        entry["expires"] = time.time() + self.cfg["line_seconds"]
        self.history = (self.history + [entry])[-HISTORY_SIZE:]
        self.redraw()

    def visible(self):
        """(index, entry) pairs to draw. Unlocked shows recent history so you can copy."""
        now = time.time()
        items = list(enumerate(self.history))
        if not self.unlocked:
            items = [(i, e) for i, e in items if e["expires"] > now]
        return items[-self.cfg["max_lines"]:]

    def redraw(self):
        c = self.canvas
        c.delete("all")
        wrap = self.cfg["width"] - 10
        top_limit = 0
        if self.unlocked:
            key = self.cfg["toggle_key"]
            hint = self.status or f"{key}: lock  ·  drag: move  ·  click: copy  ·  right-click: original"
            c.create_text(6, 4, text=hint, anchor="nw", font=self.small_font,
                          fill="#7CFC9A" if self.status else "#bbbbbb")
            # The two buttons, right of the hint: the chosen one lit up.
            x = self.cfg["width"] - 6
            for mode in reversed(LANGUAGE_MODES):
                on = self.cfg["languages"] == mode
                label = c.create_text(x - 8, 6, text=LANGUAGE_MODES[mode], anchor="ne", font=self.small_font,
                                      fill="#ffffff" if on else "#bbbbbb", tags=(f"mode_{mode}",))
                x0, y0, x1, y1 = c.bbox(label)
                box = c.create_rectangle(x0 - 8, y0 - 2, x1 + 8, y1 + 2, fill="#5b8cff" if on else "#2a2f38",
                                         outline="", tags=(f"mode_{mode}",))
                c.tag_lower(box, label)
                x = x0 - 22
            top_limit = self.line_h + 4
        y = c.winfo_height() - 5
        for i, e in reversed(self.visible()):
            label = f"[{e['lang'].upper()}]{' (TEAM)' if e['team'] else ''} {e['name']} says: {e['text']}"
            # Shadow first, then text, so it stays readable on any background.
            shadow = c.create_text(6, y + 1, text=label, anchor="sw", width=wrap,
                                   font=self.font, fill="black", tags=(f"e{i}",))
            c.create_text(5, y, text=label, anchor="sw", width=wrap, tags=(f"e{i}",),
                          font=self.font, fill="#ffd866" if e["team"] else "#9fe7ff")
            top = c.bbox(shadow)[1]
            if top < top_limit:
                c.delete(f"e{i}")
                break
            y = top - 4

    def run(self, results, toggles):
        self.start(results, toggles)
        self.root.mainloop()

    def start(self, results, toggles):
        """Schedules the overlay's updates on the Tk loop that's already running."""
        shown = []

        def tick():
            nonlocal shown
            while not toggles.empty():
                toggles.get()
                self.toggle()
            while not results.empty():
                self.add(results.get())
            now_shown = [i for i, _ in self.visible()]
            if now_shown != shown:  # something expired
                shown = now_shown
                self.redraw()
            self.root.after(150, tick)

        def keep_on_top():
            self.root.attributes("-topmost", True)
            self.root.lift()
            self.root.after(2000, keep_on_top)

        tick()
        keep_on_top()


def start(cfg):
    if not os.path.exists(cfg["log_path"]):
        print(f"Waiting for {cfg['log_path']}")
        print("Make sure TF2 has -condebug in its launch options (run Setup).")
    lines, results, toggles = queue.Queue(), queue.Queue(), queue.Queue()
    said, to_chat, status = set(), queue.Queue(), queue.Queue()
    threading.Thread(target=tail, args=(cfg["log_path"], lines), daemon=True).start()
    threading.Thread(target=worker, args=(cfg, lines, results, said), daemon=True).start()
    vk = key_to_vk(cfg["toggle_key"])
    threading.Thread(target=hotkey_listener, args=(vk, lambda: toggles.put(1)), daemon=True).start()
    if cfg["output"] == "chat":
        if not cfg["rcon_password"]:
            print("No RCON password yet: run Setup first (option 5 in Start Translator.bat).")
            print("Showing the overlay only for now.")
        else:
            threading.Thread(target=chat_sender, args=(cfg, to_chat, said, status), daemon=True).start()
    overlay = Overlay(cfg)
    shown = []

    def tick():
        nonlocal shown
        while not toggles.empty():
            toggles.get()
            overlay.toggle()
        while not results.empty():
            entry = results.get()
            overlay.add(entry)
            if cfg["output"] == "chat":
                to_chat.put(entry)
        while not status.empty():
            print(status.get(), flush=True)
        now_shown = [i for i, _ in overlay.visible()]
        if now_shown != shown:  # something expired
            shown = now_shown
            overlay.redraw()
        overlay.root.after(150, tick)

    def keep_on_top():
        overlay.root.attributes("-topmost", True)
        overlay.root.lift()
        overlay.root.after(2000, keep_on_top)

    tick()
    keep_on_top()
    return overlay


MODES = {("russian", "overlay"): "Russian -> English, overlay only",
         ("all", "overlay"): "All languages -> English, overlay only",
         ("russian", "chat"): "Russian -> English, said in chat for everyone",
         ("all", "chat"): "All languages -> English, said in chat for everyone"}


def main(argv=None):
    p = argparse.ArgumentParser(description="TF2 chat translator")
    p.add_argument("--languages", choices=["russian", "all"])
    p.add_argument("--output", choices=["overlay", "chat"])
    args = p.parse_args(argv)
    single_instance("tf2_chat_translator")
    cfg = load_config()
    if args.languages:
        cfg["languages"] = args.languages
    if args.output:
        cfg["output"] = args.output
    save_config(cfg)
    print(f"Mode: {MODES[(cfg['languages'], cfg['output'])]}")
    print(f"Press {cfg['toggle_key']} in game to unlock/lock the overlay. Close this window to stop.")
    start(cfg).root.mainloop()


if __name__ == "__main__":
    main()
