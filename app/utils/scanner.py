import socket
import requests
import time
from scapy.all import ARP, Ether, srp, conf

# ==========================================
# CONFIGURATION
# ==========================================
# Replace with your actual production or local backend URL
API_URL = "http://127.0.0.1:5000/attendance/scan" 

# Standard WiFi interface for most Linux/Ubuntu systems
INTERFACE = conf.iface

# DYNAMIC NETWORK DETECTION
def get_local_ip_range():
    """
    Detects the current local IP address and calculates the 
    /24 subnet range automatically.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        # Converts e.g. 192.168.1.15 to 192.168.1.0/24
        ip_range = ".".join(local_ip.split(".")[:-1]) + ".0/24"
        return ip_range
    except Exception as e:
        print(f"[!] Error detecting network: {e}")
        return "192.168.1.0/24" # Fallback
    finally:
        s.close()

# SCANNING LOGIC
def scan_and_report():
    target_ip_range = get_local_ip_range()
    print(f"\n--- Starting Scan on {target_ip_range} ---")
    
    # 1. Craft the ARP Broadcast Packet
    # ARP: "Who has these IPs?" 
    # Ether: Sends it to every device (broadcast)
    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=target_ip_range)
    
    try:
        # 2. Send the packet and wait 3 seconds for replies
        # srp = Send and Receive Packets (Layer 2)
        ans, unans = srp(packet, timeout=3, iface=INTERFACE, verbose=False)
        
        detected_count = 0
        
        # 3. Process replies
        for sent, received in ans:
            mac_address = received.hwsrc  # Extract the MAC
            
            # 4. POST the MAC to the MARS API
            payload = {"mac_address": mac_address}
            try:
                response = requests.post(API_URL, json=payload, timeout=5)
                
                if response.status_code == 201:
                    student_data = response.json()
                    print(f"[LOGGED] Found: {student_data.get('student')} | MAC: {mac_address}")
                    detected_count += 1
                elif response.status_code == 404:
                    # Device found on network, but not registered in MARS database
                    print(f"[SKIPPED] Unknown Device: {mac_address}")
                else:
                    print(f"[!] API Warning: {response.status_code} for {mac_address}")
                    
            except requests.exceptions.ConnectionError:
                print("[ERROR] Could not connect to MARS Backend. Is it running?")
                break 

        print(f"--- Scan Complete. {detected_count} student(s) logged. ---")

    except Exception as e:
        print(f"[CRITICAL] Scanner failure: {e}")

# EXECUTION LOOP
if __name__ == "__main__":
    print("MARS WiFi Scanner is starting...")
    print(f"Interface: {INTERFACE}")
    
    try:
        # Run indefinitely every 2 minutes
        while True:
            scan_and_report()
            print("Waiting 120 seconds for next cycle...")
            time.sleep(120)
    except KeyboardInterrupt:
        print("\nScanner stopped by user.")