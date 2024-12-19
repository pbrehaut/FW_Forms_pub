from ipaddress import IPv4Interface, IPv4Network
from typing import List, Tuple, Dict, Optional


def filter_ip_data(
        data: List[Tuple[Tuple[IPv4Interface, IPv4Interface], str, List[str]]],
        excludes: Dict[str, Optional[List[Dict[str, List[str]]]]]
) -> List[Tuple[Tuple[IPv4Interface, IPv4Interface], str, List[str]]]:
    """
    Filter IP data based on exclude rules:
    - Remove rows that match excludes (IPs + topology)

    Args:
        data: List of tuples containing source IP, destination IP, topology, and devices
        excludes: Dictionary of exclude rules per topology

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

    result = []
    for item in data:
        (src_ip, dst_ip), topology, devices = item

        # Skip if topology has no exclude rules
        if excludes.get(topology) is None:
            result.append(item)
            continue

        # Check if item matches any exclude rules
        should_exclude = False
        for rule in excludes[topology]:
            src_networks = rule.get('src', [])
            dst_networks = rule.get('dst', [])

            # Check if IPs match the exclude rule
            src_match = not src_networks or is_ip_in_network_list(src_ip, src_networks)
            dst_match = not dst_networks or is_ip_in_network_list(dst_ip, dst_networks)

            if src_match and dst_match:
                should_exclude = True
                break  # Found a match, no need to check other rules

        if not should_exclude:
            result.append(item)

    return result