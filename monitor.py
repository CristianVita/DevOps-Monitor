import urllib.request
import urllib.error
import datetime
import time 
import json
import os
import threading
import atexit
import os
from dotenv import load_dotenv

load_dotenv()

# ── Configuratie ──────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID        = os.getenv("CHAT_ID")
INTERVAL       = 60
SITES_FILE     = "sites.json"
OFFSET         = 0
# ──────────────────────────────────────────────────────

def load_sites():
    if os.path.exists(SITES_FILE):
        with open(SITES_FILE, "r") as f:
            return json.load(f)
    return []

def save_sites(sites):
    with open(SITES_FILE, "w") as f:
        json.dump(sites, f, indent=2)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": message}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)

def explain_error(e):
    err = str(e)
    if "403" in err: return "403 Forbidden — site-ul blocheaza requesturi automate"
    if "404" in err: return "404 Not Found — pagina nu exista"
    if "500" in err: return "500 Server Error — eroare interna pe server"
    if "timed out" in err: return "Timeout — site-ul nu raspunde in timp util"
    if "Name or service not known" in err: return "DNS Fail — numele domeniului nu se rezolva"
    if "No route to host" in err: return "No Route — problema de retea"
    return f"Eroare necunoscuta: {err}"

def check_site(url):
    try:
        urllib.request.urlopen(url, timeout=5)
        return "UP", None
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return "BLOCKED", "403 Forbidden — site-ul blocheaza requesturi automate, dar functioneaza"
        elif e.code == 404:
            return "DOWN", "404 Not Found — pagina nu exista"
        elif e.code == 500:
            return "DOWN", "500 Server Error — eroare interna pe server"
        else:
            return "DOWN", f"HTTP Error {e.code}"
    except Exception as e:
        err = str(e)
        if "timed out" in err:
            return "DOWN", "Timeout — site-ul nu raspunde in timp util"
        if "Name or service not known" in err:
            return "DOWN", "DNS Fail — numele domeniului nu se rezolva"
        return "DOWN", f"Eroare: {err}"

# ── Thread 1: Monitoring automat ──────────────────────
def monitor_loop():
    while True:
        sites = load_sites()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] Verificare automata...")
        for site in sites:
            status, reason = check_site(site)
            if status == "UP":
                print(f"  ✅ {site}")
            elif status == "BLOCKED":
                print(f"  ⚠️ {site} — {reason}")
            else:
                msg = f"🚨 ALERT [{now}]\n{site}\nStatus: DOWN\nMotiv: {reason}"
                print(f"  ❌ {site} — {reason}")
                send_telegram(msg)
        time.sleep(INTERVAL)

# ── Thread 2: Asculta comenzi Telegram ───────────────
def telegram_loop():
    global OFFSET
    print("📡 Ascult comenzi Telegram...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={OFFSET}&timeout=30"
            response = urllib.request.urlopen(url, timeout=35)
            data = json.loads(response.read().decode())

            for update in data.get("result", []):
                OFFSET = update["update_id"] + 1
                message = update.get("message", {})
                text = message.get("text", "").strip()

                if text.startswith("/add "):
                    url_to_add = text[5:].strip()
                    sites = load_sites()
                    if url_to_add not in sites:
                        sites.append(url_to_add)
                        save_sites(sites)
                        send_telegram(f"✅ Adaugat: {url_to_add}")
                    else:
                        send_telegram(f"⚠️ Deja in lista: {url_to_add}")

                elif text.startswith("/remove "):
                    url_to_remove = text[8:].strip()
                    sites = load_sites()
                    if url_to_remove in sites:
                        sites.remove(url_to_remove)
                        save_sites(sites)
                        send_telegram(f"🗑️ Sters: {url_to_remove}")
                    else:
                        send_telegram(f"⚠️ Nu am gasit: {url_to_remove}")

                elif text == "/list":
                    sites = load_sites()
                    if sites:
                        msg = "📋 Site-uri monitorizate:\n" + "\n".join(f"• {s}" for s in sites)
                    else:
                        msg = "📋 Lista e goala."
                    send_telegram(msg)

                elif text == "/status":
                    sites = load_sites()
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    msg = f"📊 Status [{now}]\n"
                    for site in sites:
                        status, reason = check_site(site)
                        icon = "✅" if status == "UP" else "⚠️" if status == "BLOCKED" else "❌"
                        msg += f"{icon} {site}"
                        if reason:
                            msg += f"\n   ↳ {reason}"
                        msg += "\n"
                    send_telegram(msg)

                elif text == "/help":
                    send_telegram(
                        "🤖 DevOps Monitor — Comenzi:\n\n"
                        "/add https://site.com — adauga site\n"
                        "/remove https://site.com — sterge site\n"
                        "/list — vezi toate site-urile\n"
                        "/status — verifica acum\n"
                        "/help — aceasta lista"
                    )

        except Exception as e:
            print(f"Eroare telegram loop: {e}")
            time.sleep(5)

# ── Main ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=== DevOps Monitor pornit ===")
    send_telegram("✅ DevOps Monitor pornit!\nScrie /help pentru comenzi.")

    def cleanup():
        if os.path.exists(SITES_FILE):
            os.remove(SITES_FILE)
            print("🗑️ sites.json sters.")

    atexit.register(cleanup)

    t1 = threading.Thread(target=monitor_loop, daemon=True)
    t2 = threading.Thread(target=telegram_loop, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()