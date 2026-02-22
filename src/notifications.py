"""Desktop notifications and alerts for CAPTCHA detection"""

import os
import select
import subprocess
import sys
import threading
import time
from rich.console import Console

console = Console()

def show_desktop_notification(title, message, timeout=10):
    """
    Show a desktop notification popup
    
    Supports:
    - Linux (notify-send)
    - macOS (osascript)
    - Windows (via winsound or powershell)
    """
    try:
        if sys.platform == 'linux':
            # Linux: use notify-send
            subprocess.run(
                ['notify-send', '-u', 'critical', '-t', str(timeout * 1000), title, message],
                timeout=2,
                check=False
            )
        elif sys.platform == 'darwin':
            # macOS: use osascript
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(
                ['osascript', '-e', script],
                timeout=2,
                check=False
            )
        elif sys.platform == 'win32':
            # Windows: try PowerShell notification
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $APP_ID = 'GoogleMapsScraper'
            $template = @"
            <toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{title}</text>
                        <text id="2">{message}</text>
                    </binding>
                </visual>
            </toast>
            "@
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
            '''
            subprocess.run(
                ['powershell', '-Command', ps_script],
                timeout=2,
                check=False,
                capture_output=True
            )
    except Exception as e:
        # Silently fail - notification not critical
        pass

def play_alert_sound(repeat_count=5):
    """
    Play system alert sound
    
    On Linux:
    - Uses paplay if available (freedesktop sound)
    - Falls back to beep command
    - Falls back to terminal bell
    """
    try:
        if sys.platform == 'linux':
            # Try paplay first (better quality)
            try:
                for _ in range(repeat_count):
                    subprocess.run(
                        ['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'],
                        stderr=subprocess.DEVNULL,
                        timeout=1,
                        check=False
                    )
                    time.sleep(0.5)
                return
            except FileNotFoundError:
                pass
            
            # Try beep command
            try:
                for _ in range(repeat_count):
                    subprocess.run(['beep', '-l', '100', '-f', '1000'], timeout=1, check=False)
                    time.sleep(0.5)
                return
            except FileNotFoundError:
                pass
        
        # Fallback: terminal bell (works everywhere)
        for _ in range(repeat_count):
            print('\a', end='', flush=True)
            time.sleep(0.3)
            
    except Exception:
        pass

def _is_interactive():
    """Check if stdin is connected to an interactive terminal"""
    try:
        return os.isatty(sys.stdin.fileno())
    except (AttributeError, ValueError, OSError):
        return False


def _wait_for_input(timeout_seconds=300):
    """
    Wait for user input with a timeout.
    
    Args:
        timeout_seconds: Max seconds to wait (default 5 minutes)
    
    Returns:
        True if user pressed Enter, False if timed out or non-interactive
    """
    if not _is_interactive():
        # Non-interactive (batch/headless with no terminal) — auto-continue after delay
        time.sleep(30)
        return True
    
    # Interactive terminal — use select for timeout on Linux/macOS
    if sys.platform != 'win32':
        ready, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
        if ready:
            sys.stdin.readline()
            return True
        return True  # Timed out, auto-continue
    else:
        # Windows: no select on stdin, fall back to plain input with thread timeout
        result = [False]
        
        def _read():
            try:
                input()
                result[0] = True
            except EOFError:
                result[0] = True
        
        t = threading.Thread(target=_read, daemon=True)
        t.start()
        t.join(timeout=timeout_seconds)
        return True  # Continue regardless


def captcha_alert_popup(logger, headless_mode=False, timeout_seconds=300):
    """
    Show CAPTCHA alert with desktop notification and sound
    
    Args:
        logger: Logger instance
        headless_mode: Whether running in headless mode
        timeout_seconds: Max seconds to wait for user (default 5 minutes)
    
    Returns:
        Boolean - True if user wants to continue, False if wants to abort
    """
    logger.warning("CAPTCHA DETECTED!")
    
    interactive = _is_interactive()
    
    # Play loud alert sound
    play_alert_sound(repeat_count=3)
    
    # Show desktop notification
    if headless_mode:
        show_desktop_notification(
            title="CAPTCHA DETECTED",
            message="A CAPTCHA has been detected. Browser will open for you to solve it.",
            timeout=10
        )
    else:
        show_desktop_notification(
            title="CAPTCHA DETECTED",
            message="Please solve the CAPTCHA in the browser window.",
            timeout=10
        )
    
    # Show console alert
    console.print("\n")
    console.print("[bold red]" + "="*60 + "[/bold red]")
    console.print("[bold red]CAPTCHA DETECTED![/bold red]")
    console.print("[bold red]" + "="*60 + "[/bold red]")
    
    if not interactive:
        console.print("[yellow]Non-interactive mode detected (batch script).[/yellow]")
        console.print(f"[cyan]Waiting 30 seconds then auto-continuing...[/cyan]")
        console.print("[cyan]Solve the CAPTCHA in the browser if possible.[/cyan]")
    elif headless_mode:
        console.print("[yellow]A browser window will open for you to solve the CAPTCHA.[/yellow]")
        console.print("[cyan]Once solved, the browser will close and scraping will continue.[/cyan]")
    else:
        console.print("[yellow]Please solve the CAPTCHA in the browser window.[/yellow]")
        console.print("[cyan]You can see the page content - solve it and press Enter below.[/cyan]")
    
    if interactive:
        console.print(f"[green]Press Enter when CAPTCHA is solved (auto-continues in {timeout_seconds}s)...[/green]")
    console.print("[bold red]" + "="*60 + "[/bold red]\n")
    
    # Keep playing alert every 10 seconds
    stop_alert = threading.Event()
    
    def repeat_alert():
        while not stop_alert.is_set():
            time.sleep(10)
            if not stop_alert.is_set():
                play_alert_sound(repeat_count=2)
                if interactive:
                    console.print("[bold yellow]Still waiting for CAPTCHA to be solved...[/bold yellow]")
    
    alert_thread = threading.Thread(target=repeat_alert, daemon=True)
    alert_thread.start()
    
    try:
        _wait_for_input(timeout_seconds)
        stop_alert.set()
        logger.info("Continuing after CAPTCHA pause...")
        return True
    except KeyboardInterrupt:
        stop_alert.set()
        logger.warning("Scraping cancelled by user.")
        return False
