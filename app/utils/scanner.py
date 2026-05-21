import socket
import requests
import time
import netifaces
import ipaddress
from scapy.all import ARP, Ether, srp, conf

# ==========================================
# CONFIGURATION
# ==========================================
API_URL = "https://mars-api-o24g.onrender.com/attendance/scan"
INTERFACE = conf.iface


# ==========================================
# DYNAMIC NETWORK DETECTION
# ==========================================
def get_local_ip_range():
    """
    Detects the current local IP and subnet mask,
    then returns the correct CIDR range (e.g. 192.168.100.0/24 or /16).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()

    try:
        iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
        netmask = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['netmask']
        network = ipaddress.IPv4Network(f"{local_ip}/{netmask}", strict=False)
        return str(network)
    except Exception as e:
        print(f"[!] Error detecting subnet mask: {e}")
        # Fallback to /24 if detection fails
        return ".".join(local_ip.split(".")[:-1]) + ".0/24"


# ==========================================
# SCANNING LOGIC
# ==========================================
def scan_and_report():
    target_ip_range = get_local_ip_range()
    print(f"\n--- Starting Scan on {target_ip_range} ---")

    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=target_ip_range)

    try:
        ans, unans = srp(packet, timeout=3, iface=INTERFACE, verbose=False)

        mac_addresses = [received.hwsrc.lower() for _, received in ans]

        if not mac_addresses:
            print("[!] No devices detected.")
            return

        print("\nDetected MAC addresses:")
        for mac in mac_addresses:
            print(f" - {mac}")

        payload = {"mac_addresses": mac_addresses}
        try:
            response = requests.post(API_URL, json=payload, timeout=5)

            if response.status_code == 201:
                results = response.json()
                print("\n[LOGGED] Students detected:")
                for student in results.get("students", []):
                    print(f" - {student.get('student')} | MAC: {student.get('mac_address')}")
            elif response.status_code == 404:
                print("\n[SKIPPED] Unknown Devices:")
                for mac in mac_addresses:
                    print(f" - {mac}")
            else:
                print(f"[!] API Warning: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print("[ERROR] Could not connect to MARS Backend. Is it running?")

        print(f"--- Scan Complete. {len(mac_addresses)} device(s) detected. ---")

    except Exception as e:
        print(f"[CRITICAL] Scanner failure: {e}")


# ==========================================
# EXECUTION LOOP
# ==========================================
if __name__ == "__main__":
    print("MARS WiFi Scanner is starting...")
    print(f"Interface: {INTERFACE}")

    try:
        while True:
            scan_and_report()
            print("Waiting 120 seconds for next cycle...")
            time.sleep(120)
    except KeyboardInterrupt:
        print("\nScanner stopped.")
