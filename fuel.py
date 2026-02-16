import requests
import threading
from time import sleep

# رنگ‌ها برای خوشگل‌سازی ترمینال
g = '\033[32m'
r = '\033[31m'
w = '\033[0m'

# منابع دریافت پروکسی رایگان (API)
SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://www.proxy-list.download/api/v1/get?type=https",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
]

valid_proxies = []

def check_proxy(proxy):
    """تست سالم بودن پروکسی روی یک سایت هدف"""
    try:
        # تست روی گوگل یا سایت‌های ایرانی برای اطمینان
        res = requests.get("https://basalam.com", proxies={"http": proxy, "https": proxy}, timeout=5)
        if res.status_code == 200:
            print(f"{g}[+] Valid Proxy Found: {proxy}{w}")
            valid_proxies.append(proxy)
            # ذخیره در لحظه توی فایل
            with open("valid_proxies.txt", "a") as f:
                f.write(proxy + "\n")
    except:
        pass

def scrape():
    print(f"{g}[*] Scraping proxies from sources...{w}")
    all_proxies = []
    for source in SOURCES:
        try:
            r = requests.get(source, timeout=10)
            proxies = r.text.splitlines()
            all_proxies.extend(proxies)
        except:
            print(f"{r}[!] Failed to get from: {source}{w}")
    
    print(f"{g}[*] Found {len(all_proxies)} proxies. Starting validation...{w}")
    return list(set(all_proxies)) # حذف تکراری‌ها

def start_fueling():
    # پاک کردن فایل قدیمی
    open("valid_proxies.txt", "w").close()
    
    proxies = scrape()
    threads = []
    
    # استفاده از تردینگ برای سرعت تست بالا
    for p in proxies:
        t = threading.Thread(target=check_proxy, args=(p,))
        threads.append(t)
        t.start()
        
        # جلوگیری از کراش کردن سیستم با محدود کردن تعداد تردها در لحظه
        if len(threads) >= 50:
            for t in threads:
                t.join()
            threads = []

if __name__ == "__main__":
    start_fueling()
    print(f"\n{g}[DONE] Valid proxies saved to valid_proxies.txt{w}")
