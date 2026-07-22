#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Camorro - Advanced Penetration Testing Framework for Termux
# Author: Your Name
# GitHub: https://github.com/yourusername/camorro

import os
import sys
import json
import subprocess
import platform
from datetime import datetime
from colorama import init, Fore, Back, Style

init(autoreset=True)

# ============= التهيئة =============
VERSION = "2.0.0"
AUTHOR = "Camorro Team"
CONFIG_FILE = "config/settings.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"theme": "dark", "language": "ar", "targets_file": ""}

def save_config(config):
    os.makedirs("config", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

config = load_config()

def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")

def print_banner():
    clear_screen()
    banner = f"""
{Fore.RED} ██████╗ █████╗ ███╗   ███╗ ██████╗ ██████╗ ██████╗ ██████╗ 
{Fore.RED}██╔════╝██╔══██╗████╗ ████║██╔═══██╗██╔══██╗██╔══██╗██╔══██╗
{Fore.RED}██║     ███████║██╔████╔██║██║   ██║██████╔╝██████╔╝██████╔╝
{Fore.RED}██║     ██╔══██║██║╚██╔╝██║██║   ██║██╔══██╗██╔══██╗██╔══██╗
{Fore.RED}╚██████╗██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██║██║  ██║██████╔╝
{Fore.RED} ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ 
{Fore.YELLOW}═══════════════════════════════════════════════════════════
{Fore.GREEN}  Advanced Pentesting Framework v{VERSION}
{Fore.CYAN}  المصدر المفتوح | Open Source | for authorized testing only
{Fore.YELLOW}═══════════════════════════════════════════════════════════
{Fore.WHITE}  [•] التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{Fore.WHITE}  [•] الجهاز: {platform.system()} | المستخدم: {os.getenv('USER', 'root')}
{Fore.YELLOW}═══════════════════════════════════════════════════════════{Style.RESET_ALL}
"""
    print(banner)

def print_menu():
    menu = f"""
{Fore.CYAN}╔════════════════════════════════════════════════════╗
{Fore.CYAN}║            ♛  قائمة الأدوات الرئيسية  ♛          ║
{Fore.CYAN}╠════════════════════════════════════════════════════╣
{Fore.CYAN}║                                                    ║
{Fore.YELLOW}║  {Fore.WHITE}[1] {Fore.GREEN}جمع المعلومات (OSINT)        {Fore.YELLOW}║
{Fore.YELLOW}║  {Fore.WHITE}[2] {Fore.GREEN}فحص الثغرات (Scanner)        {Fore.YELLOW}║
{Fore.YELLOW}║  {Fore.WHITE}[3] {Fore.GREEN}الاستغلال (Exploitation)      {Fore.YELLOW}║
{Fore.YELLOW}║  {Fore.WHITE}[4] {Fore.GREEN}توليد البايلودات (Payloads)   {Fore.YELLOW}║
{Fore.YELLOW}║  {Fore.WHITE}[5] {Fore.GREEN}هجمات الشبكة (Network)        {Fore.YELLOW}║
{Fore.YELLOW}║  {Fore.WHITE}[6] {Fore.GREEN}الاستطلاع (Recon)             {Fore.YELLOW}║
{Fore.YELLOW}║  {Fore.WHITE}[7] {Fore.GREEN}فحص تطبيقات الويب (Web)       {Fore.YELLOW}║
{Fore.YELLOW}║  {Fore.WHITE}[8] {Fore.GREEN}نظام التحكم (C2 Framework)    {Fore.YELLOW}║
{Fore.YELLOW}║  {Fore.WHITE}[9] {Fore.GREEN}أداة Flipper Zero وهمية       {Fore.YELLOW}║
{Fore.YELLOW}║  {Fore.WHITE}[10] {Fore.GREEN}أداة Rubber Ducky Generator  {Fore.YELLOW}║
{Fore.CYAN}║                                                    ║
{Fore.RED}║  {Fore.WHITE}[0] {Fore.RED}خروج                          {Fore.YELLOW}║
{Fore.CYAN}║                                                    ║
{Fore.CYAN}╚════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(menu)

def check_termux():
    """التحقق من وجود Termux وتثبيت المتطلبات"""
    try:
        result = subprocess.run(["uname", "-o"], capture_output=True, text=True)
        return "Android" in result.stdout
    except:
        return False

def install_dependencies():
    """تثبيت جميع المتطلبات تلقائياً"""
    print(f"{Fore.YELLOW}[*] جاري تثبيت المتطلبات...{Style.RESET_ALL}")
    
    packages = [
        "python", "python2", "git", "wget", "curl", "nmap",
        "metasploit", "hydra", "john", "sqlmap", "nuclei",
        "nikto", "dnsutils", "net-tools", "openssh"
    ]
    
    if check_termux():
        for pkg in packages:
            print(f"{Fore.CYAN}[+] جاري تثبيت {pkg}...{Style.RESET_ALL}")
            subprocess.run(["pkg", "install", "-y", pkg], 
                         capture_output=True, check=False)
        
        # تثبيت أدوات إضافية
        subprocess.run(["pip3", "install", "-r", "requirements.txt"], 
                     capture_output=True, check=False)
        
        # تثبيت أدوات خاصة
        tools = {
            "theHarvester": "git clone https://github.com/laramies/theHarvester.git tools/theHarvester",
            "Sherlock": "git clone https://github.com/sherlock-project/sherlock.git tools/sherlock",
            "Bettercap": "pkg install bettercap -y"
        }
        
        for name, cmd in tools.items():
            print(f"{Fore.CYAN}[+] تثبيت {name}...{Style.RESET_ALL}")
            if name == "Bettercap":
                subprocess.run(cmd.split(), capture_output=True, check=False)
            else:
                if not os.path.exists(f"tools/{name.lower()}"):
                    subprocess.run(cmd.split(), capture_output=True, check=False)
        
        print(f"{Fore.GREEN}[✓] تم تثبيت جميع المتطلبات بنجاح!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[!] هذا السكريبت مخصص لـ Termux على Android{Style.RESET_ALL}")

def show_stats():
    print(f"\n{Fore.CYAN}╔══════════════════════════════════╗")
    print(f"║         إحصائيات الأداة           ║")
    print(f"╠══════════════════════════════════╣")
    print(f"║ {Fore.WHITE}• الأدوات المتاحة: {Fore.GREEN}8{Fore.CYAN}              ║")
    print(f"║ {Fore.WHITE}• المكتبات المثبتة: {Fore.GREEN}Checking...{Fore.CYAN}  ║")
    print(f"║ {Fore.WHITE}• الإصدار: {Fore.GREEN}v{VERSION}{Fore.CYAN}               ║")
    print(f"║ {Fore.WHITE}• الهدف الحالي: {Fore.GREEN}{config.get('target', 'غير محدد')}{Fore.CYAN}║")
    print(f"╚══════════════════════════════════╝{Style.RESET_ALL}")

# ============= استيراد الوحدات =============
from modules.osint_module import OSINTModule
from modules.scanner_module import ScannerModule
from modules.exploit_module import ExploitModule
from modules.payload_module import PayloadModule
from modules.network_module import NetworkModule
from modules.recon_module import ReconModule
from modules.web_module import WebModule
from modules.c2_module import C2Module

def main():
    try:
        print_banner()
        
        # تشغيل فحص البيئة
        if not os.path.exists("modules"):
            print(f"{Fore.RED}[!] يجب تشغيل install.sh أولاً{Style.RESET_ALL}")
            sys.exit(1)
        
        while True:
            print_banner()
            print_menu()
            show_stats()
            
            choice = input(f"\n{Fore.GREEN}╰➤ {Fore.YELLOW}اختر رقم الأداة [0-10]: {Style.RESET_ALL}")
            
            modules = {
                "1": OSINTModule,
                "2": ScannerModule,
                "3": ExploitModule,
                "4": PayloadModule,
                "5": NetworkModule,
                "6": ReconModule,
                "7": WebModule,
                "8": C2Module,
                "9": FlipperZeroEmulator,
                "10": RubberDuckyGenerator
            }
            
            if choice == "0":
                print(f"\n{Fore.RED}[!] الخروج... شكراً لاستخدامك Camorro!{Style.RESET_ALL}")
                sys.exit(0)
            elif choice == "99":
                # القائمة المخفية للتحديث
                install_dependencies()
                input(f"\n{Fore.GREEN}اضغط Enter للعودة...{Style.RESET_ALL}")
            elif choice in modules:
                module = modules[choice]()
                module.run()
                input(f"\n{Fore.GREEN}اضغط Enter للعودة للقائمة الرئيسية...{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[!] اختيار غير صالح!{Style.RESET_ALL}")
                input(f"\n{Fore.GREEN}اضغط Enter للمحاولة مرة أخرى...{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}[!] تم إيقاف التشغيل بواسطة المستخدم{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}[!] خطأ: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
