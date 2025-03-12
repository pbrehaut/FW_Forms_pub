import yaml
import ipaddress
from typing import Dict, Optional, Union, List, Tuple
END_NODE_TYPES = ('server', 'end node', 'load balancer', 'f5')


class SubnetFirewallMapper:
    def __init__(self, yaml_file_path: str, route_dump_path: Optional[str] = None):
        self.node_types = {}
        self.node_names = {}
        self.valid_firewalls = set()
        self.yaml_file_path = yaml_file_path
        self.route_dump_path = route_dump_path
        self.subnet_firewall_map = self._create_subnet_firewall_map()

    def _load_yaml_data(self) -> Optional[Dict]:
        try:
            with open(self.yaml_file_path, 'r') as file:
                return yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(f"Error loading YAML file: {exc}")
            return None

    def _parse_route_dump(self) -> Optional[Dict[str, str]]:
        if self.route_dump_path is None:
            return None

        route_map = {}
        current_heading = ""

        with open(self.route_dump_path, 'r') as file:
            for line in file:
                line = line.strip()
                if len(line.split()) == 1:
                    current_heading = line
                else:
                    parts = line.split()
                    key = f"{parts[0]}/{parts[2]}"
                    route_map[key] = current_heading

        return route_map

    def _create_subnet_firewall_map(self) -> Dict[ipaddress.IPv4Network, str]:
        subnet_firewall_map = {}
        yaml_data = self._load_yaml_data()
        route_data = self._parse_route_dump()

        if yaml_data:
            for firewall, firewall_attrs in yaml_data.items():
                subnets = firewall_attrs.get('subnets', [])
                self.node_types[firewall] = firewall_attrs.get('node_type', 'firewall')
                self.node_names[firewall] = firewall_attrs.get('node_name', "")
                if firewall in ('exclude_flows', 'include_flows'):
                    continue
                for subnet in subnets:
                    subnet_firewall_map[ipaddress.ip_network(subnet)] = firewall
                self.valid_firewalls.add(firewall)

        if route_data:
            for subnet, firewall in route_data.items():
                subnet_firewall_map[ipaddress.ip_network(subnet)] = firewall
                self.valid_firewalls.add(firewall)

        return subnet_firewall_map

    def find_matching_firewall(self, ip_obj: Union[ipaddress.IPv4Interface, ipaddress.IPv4Network]) -> Optional[str]:
        matches: List[Tuple[ipaddress.IPv4Network, str]] = []
        for subnet, firewall in self.subnet_firewall_map.items():
            if (ip_obj.network.subnet_of(subnet) or
                    ip_obj.network.network_address == subnet.network_address):
                matches.append((subnet, firewall))

        if not matches:
            return None

        # Sort matches by prefix length in descending order (most specific first)
        matches.sort(key=lambda x: x[0].prefixlen, reverse=True)

        # Return the firewall associated with the most specific match
        return matches[0][1]

    def get_subnets_for_node(self, node_name: str) -> List[ipaddress.IPv4Network]:
        """
        Get all subnets associated with a specific node/firewall.

        Args:
            node_name (str): The name of the node/firewall to look up

        Returns:
            List[ipaddress.IPv4Network]: List of subnets associated with the node
        """
        if node_name not in self.valid_firewalls:
            return []

        return [subnet for subnet, firewall in self.subnet_firewall_map.items()
                if firewall == node_name]

    def get_node_name(self, node_id: str) -> str:
        """
        Get the node name for a given firewall/node ID.

        Args:
            node_id (str): The ID of the node to look up

        Returns:
            str: The name of the node, or empty string if not found
        """
        return self.node_names.get(node_id, "")

    def get_node_type(self, node_id: str) -> str:
        """
        Get the node type for a given firewall/node ID.

        Args:
            node_id (str): The ID of the node to look up

        Returns:
            str: The type of the node (e.g., 'firewall', 'router', 'server', 'zone'),
                 or empty string if not found
        """
        return self.node_types.get(node_id, "")

    def is_end_node(self, node_name: str) -> bool:
        return self.get_node_type(node_name) in END_NODE_TYPES

    def is_ip_on_node(self, node_name: str, ip_address: str) -> bool:
        """
        Check if an IP address or subnet exists on a specific node.

        Args:
            node_name (str): The name of the node/firewall to check
            ip_address (str): An IP address (treated as /32 if no mask) or subnet

        Returns:
            bool: True if the IP exists on the node, False otherwise
        """
        # Check if node exists
        if node_name not in self.valid_firewalls:
            return False

        # Get all subnets for this node
        node_subnets = self.get_subnets_for_node(node_name)

        # Process the input IP address
        try:
            # Try to parse as a subnet first
            ip_obj = ipaddress.ip_network(ip_address, strict=False)
        except ValueError:
            try:
                # If that fails, try to parse as an IP address (with implicit /32)
                ip_obj = ipaddress.ip_network(f"{ip_address}/32", strict=False)
            except ValueError:
                # Invalid IP format
                return False

        # Check if the IP/subnet is contained in any of the node's subnets
        for subnet in node_subnets:
            # If IP is a single address
            if ip_obj.prefixlen == 32:
                if ip_obj.network_address in subnet:
                    return True
            # If IP is a subnet
            else:
                # Check if our subnet is a subset of node subnet or equal
                if ip_obj.subnet_of(subnet) or ip_obj == subnet:
                    return True
                # Check if node subnet is a subset of our subnet
                elif subnet.subnet_of(ip_obj):
                    return True

        return False
