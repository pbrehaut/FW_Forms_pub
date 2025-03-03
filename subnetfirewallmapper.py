import yaml
import ipaddress
from typing import Dict, Optional, Union, List, Tuple


class SubnetFirewallMapper:
    def __init__(self, yaml_file_path: str, route_dump_path: Optional[str] = None):
        self.node_types = {}
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
