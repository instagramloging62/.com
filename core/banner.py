#!/usr/bin/env python3
"""
Camoro Banner & UI Module (Termux-safe)
Works with colorama only. Rich is optional.
"""

import os
import sys

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    R = Fore.RED
    G = Fore.GREEN
    Y = Fore.YELLOW
    C = Fore.CYAN
    M = Fore.MAGENTA
    B = Fore.BLUE
    W = Fore.WHITE
    RE = Style.RESET_ALL
except ImportError:
    R = G = Y = C = M = B = W = RE = ""

# Optional rich
HAS_RICH = False
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    console = Console()
    HAS_RICH = True
except ImportError:
    class _SimpleConsole:
        def print(self, *args, **kwargs):
            text = " ".join(str(a) for a in args)
            # strip simple rich tags
            for tag in ["[cyan]", "[/cyan]", "[green]", "[/green]",
                        "[red]", "[/red]", "[yellow]", "[/yellow]",
                        "[magenta]", "[/magenta]", "[bold]", "[/bold]"]:
                text = text.replace(tag, "")
            print(text)
    console = _SimpleConsole()
    Table = Panel = Progress = None


def clear_screen():
    os.system("clear" if os.name != "nt" else "cls")


def show_banner():
    clear_screen()
    banner = f"""
{R}   ██████╗ █████╗ ███╗   ███╗ ██████╗ ██████╗  ██████╗ 
{R}  ██╔════╝██╔══██╗████╗ ████║██╔═══██╗██╔══██╗██╔═══██╗
{R}  ██║     ███████║██╔████╔██║██║   ██║██████╔╝██║   ██║
{R}  ██║     ██╔══██║██║╚██╔╝██║██║   ██║██╔══██╗██║   ██║
{R}  ╚██████╗██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██║╚██████╔╝
{R}   ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ 
    
{W}  ================================================
{W}  |  {C}Instagram Security Testing Framework {G}v2.1  {W}|
{W}  |  {M}Author: Camoro Team  {W}|  {Y}Termux + Linux      {W}|
{W}  ================================================
{RE}"""
    print(banner)


def show_menu():
    print(f"""
{C}========== [ CAMORO MAIN MENU ] ============{RE}
{C}[1]{W} Target Information Gathering
{C}[2]{W} AI Password Generation
{C}[3]{W} Full Attack Mode
{C}[4]{W} Brute Force Only
{C}[5]{W} Proxy Configuration
{C}[6]{W} View Results
{C}[7]{W} Settings & Config
{C}[0]{W} Exit
{C}============================================{RE}
""")
    print(f"{Y}[*] Select option [0-7]: {RE}", end="")


def show_info_panel(username, data):
    if not data:
        print(f"{R}[!] Could not retrieve information for @{username}{RE}")
        return

    bio = str(data.get("biography", "N/A") or "N/A")[:100]
    followers = data.get("followers", 0) or 0
    following = data.get("following", 0) or 0
    posts = data.get("posts", 0) or 0

    try:
        followers_s = f"{int(followers):,}"
        following_s = f"{int(following):,}"
    except Exception:
        followers_s = str(followers)
        following_s = str(following)

    print(f"""
{G}========== Target Profile: @{username} =========={RE}
{G}Username:{W}      @{username}
{G}Full Name:{W}     {data.get('full_name', 'N/A')}
{G}Bio:{W}           {bio}
{G}Followers:{W}     {followers_s}
{G}Following:{W}     {following_s}
{G}Posts:{W}         {posts}
{G}Verified:{W}      {data.get('verified', False)}
{G}Business:{W}      {data.get('is_business', False)}
{G}Private:{W}       {data.get('is_private', False)}
{G}External URL:{W}  {data.get('external_url', 'N/A') or 'N/A'}
{G}================================================{RE}
""")


def show_password_stats(passwords):
    print(f"\n{M}========== Password Generation Stats =========={RE}")
    print(f"{G}TOTAL:{W} {len(passwords):,} passwords generated{RE}")
    if passwords:
        print(f"{C}Examples:{RE}")
        for p in passwords[:8]:
            print(f"  - {p}")
    print(f"{M}==============================================={RE}\n")


def show_progress_bar():
    if HAS_RICH and Progress is not None:
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("{task.completed}/{task.total}"),
        )
    return None
