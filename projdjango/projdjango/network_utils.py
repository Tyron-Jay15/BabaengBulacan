"""Network helpers — local IPv4 detection and LAN accessibility checks."""
import socket


def get_local_ipv4():
    """
    Return this machine's primary LAN IPv4 address (not 127.0.0.1).

    Uses a UDP connect trick so no packets are sent. Returns None if detection fails.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(0.5)
            sock.connect(('8.8.8.8', 80))
            ip = sock.getsockname()[0]
            if ip and not ip.startswith('127.'):
                return ip
    except OSError:
        pass

    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and not ip.startswith('127.'):
            return ip
    except OSError:
        pass

    return None


def is_port_reachable(host, port, timeout=0.4):
    """Return True if a TCP connection to host:port succeeds."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((host, int(port))) == 0
    except OSError:
        return False


def check_lan_server_access(local_ip, port):
    """
    Return (is_accessible, message).

    When Django runserver binds only to 127.0.0.1, LAN IP connections fail.
    """
    if not local_ip:
        return False, (
            'Could not detect your local network IP address. '
            'Connect to Wi-Fi and restart the server.'
        )

    if is_port_reachable(local_ip, port):
        return True, ''

    return False, (
        'Your server is currently only accessible from this computer. '
        'Run: python manage.py runserver 0.0.0.0:8000 '
        'to allow mobile devices on the same network to connect.'
    )
