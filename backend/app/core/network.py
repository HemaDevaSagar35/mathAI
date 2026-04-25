import socket


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def print_local_ip() -> None:
    ip = get_local_ip()
    print("\n" + "=" * 50)
    print("  MathPath API is running!")
    print(f"  Local:   http://localhost:8000")
    print(f"  Network: http://{ip}:8000")
    print()
    print("  Open the MathPath app on your phone and enter:")
    print(f"  http://{ip}:8000")
    print()
    print(f"  API docs: http://localhost:8000/docs")
    print("=" * 50 + "\n")
