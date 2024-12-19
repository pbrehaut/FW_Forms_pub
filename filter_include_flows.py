from ipaddress import IPv4Interface, IPv4Network
from typing import List, Tuple, Dict, Optional, Set


def filter_ip_data(
        data: List[Tuple[Tuple[IPv4Interface, IPv4Interface], str, List[str]]],
        includes: Dict[str, Optional[List[Dict[str, List[str]]]]]
) -> List[Tuple[Tuple[IPv4Interface, IPv4Interface], str, List[str]]]:
    """
    Filter IP data based on include rules:
    1. Find rows that match includes (IPs + topology)
    2. Remove rows with matching IPs but different topology

    Args:
        data: List of tuples containing source IP, destination IP, topology, and devices
        includes: Dictionary of include rules per topology

    Returns:
        Filtered list of IP data tuples
    """

    def is_ip_in_network_list(ip: IPv4Interface, network_list: List[str]) -> bool:
        """Check if an IP is in any of the networks in the list."""
        ip_network = IPv4Network(str(ip.network))
        return any(
            ip_network.overlaps(IPv4Network(network))
            for network in network_list
        )

    # Step 1: Find rows that match includes
    matched_ips = set()  # Store (src_ip, dst_ip) that matched includes
    matched_rows = []  # Store rows that matched includes

    for item in data:
        (src_ip, dst_ip), topology, devices = item

        # Skip if topology has no include rules
        if includes.get(topology) is None:
            continue

        # Check all rules for this topology
        for rule in includes[topology]:
            src_networks = rule.get('src', [])
            dst_networks = rule.get('dst', [])

            # Check if IPs match the rule
            src_match = not src_networks or is_ip_in_network_list(src_ip, src_networks)
            dst_match = not dst_networks or is_ip_in_network_list(dst_ip, dst_networks)

            if src_match and dst_match:
                matched_ips.add((str(src_ip), str(dst_ip)))
                matched_rows.append(item)
                break  # Found a match, no need to check other rules

    # Step 2: Filter out rows with matching IPs but different topology
    result = []
    for item in data:
        (src_ip, dst_ip), topology, devices = item
        ip_pair = (str(src_ip), str(dst_ip))

        # If this IP pair matched includes but in a different topology, skip it
        if ip_pair in matched_ips and item not in matched_rows:
            continue

        result.append(item)

    return result