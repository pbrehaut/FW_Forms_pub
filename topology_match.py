from ipaddress import IPv4Interface, IPv4Network
from typing import Dict, List, Tuple


def check_topology_match(
        src_ip: IPv4Interface,
        dst_ip: IPv4Interface,
        topology_flows: Dict[str, List[Tuple[str, str]]]
) -> bool:
    """
    Check if source and destination IPs match the ranges defined in topology_exc_flows

    Args:
        src_ip (IPv4Interface): Source IP address
        dst_ip (IPv4Interface): Destination IP address
        topology_exc_flows (Dict[str, List[Tuple[str, str]]]): Dictionary mapping topology names to
            lists of (source_range, destination_range) tuples

    Returns:
        bool: True if both IPs match their respective ranges in the topology, False otherwise
    """

    # Check each flow pair in the topology
    for pair in topology_flows:
        src_ranges = pair['src']
        dst_ranges = pair['dst']
        # Convert string ranges to IPv4Network objects
        src_s_topology_net = [IPv4Network(x) for x in src_ranges]
        dst_s_topology_net = [IPv4Network(x) for x in dst_ranges]

        # Check if both source and destination IPs fall within their respective ranges
        if any([src_ip.ip in x for x in src_s_topology_net]) and any([dst_ip.ip in x for x in dst_s_topology_net]):
            return True

    return False