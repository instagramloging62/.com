#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Scanner Module - بديل Burp Suite Enterprise

import os
import subprocess
import json
import socket
from colorama import init, Fore, Style
from banner import show_banner

init(autoreset=True)

class ScannerModule:
    def __init__(self):
        self.name = "Scanner Module"
    
    def show_menu(self):
        menu = f"""
{Fore.YELLOW}╔══════════════════════════════════════════════╗
║        📡  قائمة أدوات فحص الثغرات            ║
╠══════════════════════════════════════════════╣
║                                              ║
║  {Fore.WHITE}[1] {Fore.GREEN}فحص المنافذ (Nmap Scan)            {Fore.YELLOW}║
║  {Fore.WHITE}[2] {Fore.GREEN}فحص الثغرات (Nuclei)              {Fore.YELLOW}║
║  {Fore.WHITE}[3] {Fore.GREEN}فحص SQL Injection                 {Fore.YELLOW}║
║  {Fore.WHITE}[4] {Fore.GREEN}فحص XSS (Cross Site Scripting)    {Fore.YELLOW}║
║  {Fore.WHITE}[5] {Fore.GREEN}فحص خوادم الويب (Nikto)           {Fore.YELLOW}║
║  {Fore.WHITE}[6] {Fore.GREEN}فحص Wordpress                     {Fore.YELLOW}║
║  {Fore.WHITE}[7] {Fore.GREEN}فحص SSH و FTP (Brute Force)       {Fore.YELLOW}║
║  {Fore.WHITE}[8] {Fore.GREEN}فحص جميع الخدمات (Full Scan)      {Fore.YELLOW}║
║  {Fore.WHITE}[9] {Fore.GREEN}تقرير فحص مخصص (Custom Scan)      {Fore.YELLOW}║
║                                              ║
║  {Fore.RED}[0] {Fore.RED}العودة للقائمة الرئيسية            {Fore.YELLOW}║
║                                              ║
╚══════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(menu)
    
    def nmap_scan(self, target, scan_type="-sV -sC"):
        """فحص المنافذ باستخدام Nmap"""
        print(f"\n{Fore.YELLOW}[*] جاري فحص {target} باستخدام Nmap...{Style.RESET_ALL}")
        
        try:
            cmd = f"nmap {scan_type} -T4 --min-rate=1000 {target}"
            print(f"{Fore.CYAN}[*] الأمر: {cmd}{Style.RESET_ALL}")
            
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
            print(f"\n{Fore.GREEN}[+] النتائج:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{result.stdout}{Style.RESET_ALL}")
            
            if result.stderr:
                print(f"{Fore.RED}[!] أخطاء: {result.stderr}{Style.RESET_ALL}")
                
        except subprocess.TimeoutExpired:
            print(f"{Fore.RED}[!] انتهت مهلة الفحص، الهدف قد يحجب الفحوصات{Style.RESET_ALL}")
        except FileNotFoundError:
            print(f"{Fore.RED}[!] Nmap غير مثبت. قم بتشغيل: pkg install nmap{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] خطأ: {e}{Style.RESET_ALL}")
    
    def nuclei_scan(self, target):
        """فحص الثغرات باستخدام Nuclei"""
        print(f"\n{Fore.YELLOW}[*] جاري فحص {target} باستخدام Nuclei...{Style.RESET_ALL}")
        
        try:
            cmd = f"nuclei -u {target} -severity low,medium,high,critical"
            print(f"{Fore.CYAN}[*] الأمر: {cmd}{Style.RESET_ALL}")
            
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
            
            if "No results" in result.stdout or not result.stdout.strip():
                print(f"{Fore.GREEN}[+] لم يتم العثور على ثغرات معروفة{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}[+] تم العثور على ثغرات:{Style.RESET_ALL}")
                for line in result.stdout.split('\n'):
                    if '[critical]' in line.lower():
                        print(f"    {Fore.RED}{line}{Style.RESET_ALL}")
                    elif '[high]' in line.lower():
                        print(f"    {Fore.YELLOW}{line}{Style.RESET_ALL}")
                    elif '[medium]' in line.lower():
                        print(f"    {Fore.CYAN}{line}{Style.RESET_ALL}")
                    elif line.strip():
                        print(f"    {Fore.WHITE}{line}{Style.RESET_ALL}")
                        
        except FileNotFoundError:
            print(f"{Fore.RED}[!] Nuclei غير مثبت. التثبيت: pkg install nuclei{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] خطأ: {e}{Style.RESET_ALL}")
    
    def sqlmap_check(self, url):
        """فحص SQL Injection"""
        print(f"\n{Fore.YELLOW}[*] جاري فحص {url} ضد حقن SQL...{Style.RESET_ALL}")
        
        try:
            cmd = f"sqlmap -u {url} --batch --level=2 --risk=2"
            print(f"{Fore.CYAN}[*] جاري التشغيل... (قد يستغرق وقتاً){Style.RESET_ALL}")
            
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=600)
            
            if "Parameter:" in result.stdout and "appears" in result.stdout:
                print(f"{Fore.RED}[!] تم العثور على ثغرة SQL Injection محتملة!{Style.RESET_ALL}")
                lines = [l for l in result.stdout.split('\n') if 'Parameter:' in l]
                for l in lines:
                    print(f"    {Fore.YELLOW}{l}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}[+] لم يتم العثور على SQL Injection واضحة{Style.RESET_ALL}")
                
        except FileNotFoundError:
            print(f"{Fore.RED}[!] sqlmap غير مثبت. التثبيت: pkg install sqlmap{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] خطأ: {e}{Style.RESET_ALL}")
    
    def quick_port_check(self, target):
        """فحص سريع للمنافذ الشهيرة"""
        print(f"\n{Fore.YELLOW}[*] فحص سريع للمنافذ على {target}...{Style.RESET_ALL}")
        
        common_ports = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
            53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
            443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
            1433: "MSSQL", 1521: "Oracle", 2049: "NFS",
            3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
            5900: "VNC", 6379: "Redis", 8080: "HTTP-Proxy",
            8443: "HTTPS-Alt", 27017: "MongoDB"
        }
        
        open_ports = []
        for port, service in common_ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((target, port))
            if result == 0:
                open_ports.append((port, service))
                print(f"    {Fore.GREEN}[✓] المنفذ {port}/{service} مفتوح{Style.RESET_ALL}")
            sock.close()
        
        if not open_ports:
            print(f"    {Fore.CYAN}[-] لا توجد منافذ مفتوحة من القائمة الشائعة{Style.RESET_ALL}")
        
        return open_ports
    
    def run(self):
        show_banner("scanner")
        
        while True:
            self.show_menu()
            choice = input(f"\n{Fore.GREEN}╰➤ {Fore.YELLOW}اختر العملية [0-9]: {Style.RESET_ALL}")
            
            if choice == "0":
                break
            elif choice == "1":
                target = input(f"\n{Fore.WHITE}[?] الهدف (IP أو Domain): {Style.RESET_ALL}").strip()
                scan_type = input(f"{Fore.WHITE}[?] نوع الفحص [sV/sC/A/sT] (اتركه فارغاً للافتراضي): {Style.RESET_ALL}").strip()
                if target:
                    scan_type = f"-{scan_type}" if scan_type and not scan_type.startswith('-') else scan_type
                    scan_type = scan_type or "-sV -sC"
                    self.nmap_scan(target, scan_type)
            elif choice == "2":
                target = input(f"\n{Fore.WHITE}[?] الهدف (URL): {Style.RESET_ALL}").strip()
                if target:
                    self.nuclei_scan(target)
            elif choice == "3":
                target = input(f"\n{Fore.WHITE}[?] الهدف (URL مع parameter): {Style.RESET_ALL}").strip()
                if target:
                    self.sqlmap_check(target)
            elif choice == "8":
                target = input(f"\n{Fore.WHITE}[?] الهدف (IP أو Domain): {Style.RESET_ALL}").strip()
                if target:
                    print(f"\n{Fore.GREEN}[*] بدء الفحص الشامل...{Style.RESET_ALL}")
                    self.quick_port_check(target)
                    self.nmap_scan(target)
            else:
                print(f"{Fore.RED}[!] خيار غير صالح{Style.RESET_ALL}")
