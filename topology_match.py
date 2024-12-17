from ipaddress import IPv4Interface, IPv4Network
from typing import Dict, List, Tuple


def check_topology_match(
        src_ip: IPv4Interface,
        dst_ip: IPv4Interface,
        topology_exc_flows: Dict[str, List[Tuple[str, str]]]
) -> bool:
    """
    Check if source and destination IPs match the ranges defined in topology_exc_flows

    Args:
        src_ip (IPv4Interface): Source IP address
        dst_ip (IPv4Interface): Destination IP address
        topology_name (str): Name of the topology to check against
        topology_exc_flows (Dict[str, List[Tuple[str, str]]]): Dictionary mapping topology names to
            lists of (source_range, destination_range) tuples

    Returns:
        bool: True if both IPs match their respective ranges in the topology, False otherwise
    """

    # Get the source and destination IP networks
    src_network = src_ip.network
    dst_network = dst_ip.network

    # Check each flow pair in the topology
    for src_range, dst_range in topology_exc_flows:
        # Convert string ranges to IPv4Network objects
        src_topology_net = IPv4Network(src_range)
        dst_topology_net = IPv4Network(dst_range)

        # Check if both source and destination IPs fall within their respective ranges
        if (src_ip.ip in src_topology_net and
                dst_ip.ip in dst_topology_net):
            return True

    return False