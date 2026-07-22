#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Web Module - بديل Burp Suite Enterprise

import os
import subprocess
import requests
from colorama import init, Fore, Style
from banner import show_banner

init(autoreset=True)

class WebModule:
    def __init__(self):
        self.name = "Web Module"
    
    def show_menu(self):
        menu = f"""
{Fore.CYAN}╔══════════════════════════════════════════════╗
║       🌍  قائمة أدوات فحص الويب             ║
╠══════════════════════════════════════════════╣
║                                              ║
║  {Fore.WHITE}[1] {Fore.GREEN}فحص الثغرات الشائعة (OWASP Top 10)  {Fore.CYAN}║
║  {Fore.WHITE}[2] {Fore.GREEN}فحص SQL Injection                   {Fore.CYAN}║
║  {Fore.WHITE}[3] {Fore.GREEN}فحص XSS (Cross-Site Scripting)      {Fore.CYAN}║
║  {Fore.WHITE}[4] {Fore.GREEN}فحص CSRF                             {Fore.CYAN}║
║  {Fore.WHITE}[5] {Fore.GREEN}فحص LFI/RFI (File Inclusion)         {Fore.CYAN}║
║  {Fore.WHITE}[6] {Fore.GREEN}فحص Command Injection                {Fore.CYAN}║
║  {Fore.WHITE}[7] {Fore.GREEN}فحص إعدادات الأمان (Security Headers){Fore.CYAN}║
║  {Fore.WHITE}[8] {Fore.GREEN}فحص الـ API Endpoints                 {Fore.CYAN}║
║  {Fore.WHITE}[9] {Fore.GREEN}Directory Busting (اكتشاف المسارات)  {Fore.CYAN}║
║  {Fore.WHITE}[10] {Fore.GREEN}تقرير فحص أمان كامل                 {Fore.CYAN}║
║                                              ║
║  {Fore.RED}[0] {Fore.RED}العودة للقائمة الرئيسية             {Fore.CYAN}║
║                                              ║
╚══════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(menu)
    
    def security_headers_check(self, url):
        """فحص إعدادات الأمان"""
        print(f"\n{Fore.YELLOW}[*] فحص إعدادات أمان HTTP لـ: {url}{Style.RESET_ALL}")
        
        try:
            r = requests.get(url, timeout=10, 
                           headers={'User-Agent': 'Camorro Security Scanner'})
            
            headers = r.headers
            checks = {
                'Strict-Transport-Security': {
                    'desc': 'HSTS - يمنع هجمات SSL Strip',
                    'risk': 'high' if 'Strict-Transport-Security' not in headers else 'safe'
                },
                'X-Frame-Options': {
                    'desc': 'منع Clickjacking',
                    'risk': 'high' if 'X-Frame-Options' not in headers else 'safe'
                },
                'X-Content-Type-Options': {
                    'desc': 'منع MIME sniffing',
                    'risk': 'medium' if 'X-Content-Type-Options' not in headers else 'safe'
                },
                'Content-Security-Policy': {
                    'desc': 'CSP - يمنع XSS و Data Injection',
                    'risk': 'high' if 'Content-Security-Policy' not in headers else 'safe'
                },
                'X-XSS-Protection': {
                    'desc': 'حماية من XSS في المتصفحات القديمة',
                    'risk': 'medium' if 'X-XSS-Protection' not in headers else 'safe'
                },
                'Referrer-Policy': {
                    'desc': 'التحكم بمعلومات الإحالة',
                    'risk': 'low' if 'Referrer-Policy' not in headers else 'safe'
                },
                'Permissions-Policy': {
                    'desc': 'التحكم بصلاحيات المتصفح',
                    'risk': 'low' if 'Permissions-Policy' not in headers else 'safe'
                }
            }
            
            print(f"\n{Fore.GREEN}[+] نتائج فحص الأمان:{Style.RESET_ALL}")
            for header, info in checks.items():
                if info['risk'] == 'safe':
                    print(f"    {Fore.GREEN}[✓] {header}: {headers.get(header, 'موجود')[:60]}")
                    print(f"         {info['desc']}")
                else:
                    color = Fore.RED if info['risk'] == 'high' else Fore.YELLOW
                    print(f"    {color}[✗] {header}: غير موجود!")
                    print(f"         {info['desc']} - المخاطرة: {info['risk'].upper()}")
            
            # معلومات السيرفر
            server = headers.get('Server', 'غير معروف')
            powered_by = headers.get('X-Powered-By', '')
            
            print(f"\n{Fore.CYAN}[+] معلومات السيرفر:{Style.RESET_ALL}")
            print(f"    {Fore.WHITE}Server: {server}{Style.RESET_ALL}")
            if powered_by:
                print(f"    {Fore.WHITE}X-Powered-By: {powered_by}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}[!] خطأ: {e}{Style.RESET_ALL}")
    
    def dir_buster(self, url, wordlist=None):
        """اكتشاف المسارات والمجلدات"""
        print(f"\n{Fore.YELLOW}[*] بدء اكتشاف المسارات لـ: {url}{Style.RESET_ALL}")
        
        # قائمة افتراضية للمسارات الشائعة
        paths = [
            "/admin", "/login", "/wp-admin", "/administrator", "/backup",
            "/config", "/config.php", "/db", "/database", "/sql", "/mysql",
            "/phpmyadmin", "/phpPgAdmin", "/manager", "/panel", "/cpanel",
            "/api", "/v1", "/v2", "/api/v1", "/api/users", "/api/login",
            "/uploads", "/files", "/images", "/img", "/assets", "/static",
            "/robots.txt", "/sitemap.xml", "/.env", "/.git", "/.git/config",
            "/.htaccess", "/.htpasswd", "/server-status", "/info.php",
            "/test", "/debug", "/error", "/log", "/logs", "/error_log",
            "/shell", "/cmd", "/exec", "/console", "/terminal",
            "/webmail", "/email", "/mail", "/owa", "/exchange",
            "/crossdomain.xml", "/clientaccesspolicy.xml",
            "/wsdl", "/soap", "/xmlrpc.php", "/wp-cron.php"
        ]
        
        if wordlist and os.path.exists(wordlist):
            with open(wordlist, "r") as f:
                paths = [p.strip() for p in f.readlines()]
        
        found = []
        for path in paths:
            full_url = url.rstrip('/') + path
            try:
                r = requests.get(full_url, timeout=3, 
                               headers={'User-Agent': 'Camorro Scanner'})
                if r.status_code in [200, 201, 301, 302, 403, 401]:
                    status_color = Fore.GREEN if r.status_code == 200 else Fore.YELLOW
                    found.append((path, r.status_code))
                    print(f"    {status_color}[{r.status_code}] {path}{Style.RESET_ALL}")
            except:
                pass
        
        print(f"\n{Fore.WHITE}[+] تم العثور على {len(found)} مسار{Style.RESET_ALL}")
        
        # حفظ النتائج
        if found:
            with open(f"dirs_{url.replace('https://','').replace('http://','').replace('/','_')}.txt", "w") as f:
                for path, code in found:
                    f.write(f"{path} [{code}]\n")
            print(f"{Fore.GREEN}[+] تم حفظ النتائج{Style.RESET_ALL}")
    
    def check_sql_injection(self, url):
        """فحص SQL Injection"""
        print(f"\n{Fore.YELLOW}[*] فحص SQL Injection لـ: {url}{Style.RESET_ALL}")
        
        payloads = [
            "'", "''", "`", "' OR '1'='1", "' OR '1'='1' --",
            "' OR '1'='1' #", "' OR 1=1 --", "\" OR \"1\"=\"1",
            "1' AND '1'='1", "1' AND '1'='2", "admin' --",
            "admin' #", "' UNION SELECT NULL--", "' UNION SELECT NULL,NULL--"
        ]
        
        error_signals = [
            "sql", "mysql", "sqlite", "postgresql", "odbc",
            "you have an error in your sql", "warning: mysql",
            "unclosed quotation mark", "quoted string not properly terminated",
            "division by zero", "unknown column"
        ]
        
        for payload in payloads:
            try:
                test_url = url + requests.utils.quote(payload)
                r = requests.get(test_url, timeout=5, 
                               headers={'User-Agent': 'Camorro Scanner'})
                
                # فحص الأخطاء
                response_lower = r.text.lower()
                for signal in error_signals:
                    if signal in response_lower:
                        print(f"    {Fore.RED}[!] محتمل SQL Injection: {payload}{Style.RESET_ALL}")
                        print(f"    {Fore.YELLOW}    تم اكتشاف: {signal}{Style.RESET_ALL}")
                        break
            except:
                pass
    
    def run(self):
        show_banner("web")
        
        while True:
            self.show_menu()
            choice = input(f"\n{Fore.GREEN}╰➤ {Fore.YELLOW}اختر العملية [0-10]: {Style.RESET_ALL}")
            
            if choice == "0":
                break
            elif choice == "7":
                url = input(f"\n{Fore.WHITE}[?] الرابط الكامل (https://example.com): {Style.RESET_ALL}").strip()
                if url:
                    self.security_headers_check(url)
            elif choice == "9":
                url = input(f"\n{Fore.WHITE}[?] الرابط الكامل (https://example.com): {Style.RESET_ALL}").strip()
                wl = input(f"{Fore.WHITE}[?] ملف الكلمات (اتركه فارغاً للافتراضي): {Style.RESET_ALL}").strip()
                if url:
                    self.dir_buster(url, wl if wl else None)
            elif choice == "2":
                url = input(f"\n{Fore.WHITE}[?] الرابط مع parameter (https://example.com/page?id=1): {Style.RESET_ALL}").strip()
                if url:
                    self.check_sql_injection(url)
            else:
                print(f"{Fore.RED}[!] خيار غير صالح{Style.RESET_ALL}")
