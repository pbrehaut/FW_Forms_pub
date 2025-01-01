from collections import defaultdict
import yaml
from firewalldiagram import FirewallDiagram
from subnetfirewallmapper import SubnetFirewallMapper
from findips import find_ip_addresses
import ip_headings
import filter_include_flows
import filter_excluded_flows
import generate_xls_diagrams



def generate_output(cust_rules, config_mgr, file_prefix=None):
    #  Get the 1st key of the cust_rules dictionary and
    #  generate an exception if there is more than one, we only want one customer
    if len(cust_rules) > 1:
        raise Exception("Only one customer can be processed at a time")
    else:
        cust = list(cust_rules.keys())[0]

    rules = cust_rules[cust]
    rules = [[item.replace('_x000D_', '') for item in sublist] for sublist in rules]

    # Get the topology file paths for each topology for this customer
    # And initialise the subnet firewall Mapper and diagram objects
    topologies = {}

    # Maintain a list of IP addresses that were not found in the topology and returned them to the user
    missing_ips_in_topologies = defaultdict(set)

    topology_inc_flows = {}
    topology_exc_flows = {}
    # Iterate through all subsections for the customer
    for subsection in config_mgr.get_customer_subsections(cust):
        topology_dict = config_mgr.get_topology(cust, subsection)

        fw_subnets_file = topology_dict.get('subnets')
        routes_file = topology_dict.get('routes')
        topology_file = topology_dict.get('topology')

        fw_subnets_file = fw_subnets_file if fw_subnets_file else None
        routes_file = routes_file if routes_file else None
        topology_file = topology_file if topology_file else None

        # Create the firewall diagram
        diagram = FirewallDiagram(topology_file) if topology_file else None

        # Create the subnet firewall mapper
        mapper = SubnetFirewallMapper(fw_subnets_file, routes_file) if fw_subnets_file else None

        with open(fw_subnets_file, 'r') as f:
            yaml_data = yaml.safe_load(f)
            topology_exc_flows[subsection] = yaml_data.get('exclude_flows', None)
            topology_inc_flows[subsection] = yaml_data.get('include_flows', None)

        # Add the topologies to the dictionary using the subsection as the key
        topologies[subsection] = (diagram, mapper)

    rows_to_output = []

    #   Find the IP addresses for the rules
    for original_rule_id, rule in enumerate(rules, start=1):
        # Initialise a dictionary for the mapping of IP addresses to the original content of the rule for that IP
        src_ip_full_text_mapping = {}
        dst_ip_full_text_mapping = {}
        src, dst, port, comment = rule

        # Add headings back in later
        src_headings = ip_headings.map_ip_to_heading(src)
        dst_headings = ip_headings.map_ip_to_heading(dst)

        # swap back in newline to comments
        comment = comment.replace('; ', '\n')
        #   Find the IP addresses for the source and destination
        src_ips, src_text_map = find_ip_addresses(src)
        dst_ips, dst_text_map = find_ip_addresses(dst)
        src_ip_full_text_mapping.update(src_text_map)
        dst_ip_full_text_mapping.update(dst_text_map)

        #   Get the permutations of the source and destination IP's
        rule_src_dst_permutations = []
        for src_ip, dst_ip in generate_xls_diagrams.src_dst_permutations(src_ips, dst_ips):
            #  For each permutation of source to destination IP
            #  Get the source and destination IP firewalls

            #  For each Topology for this customer find the firewalls and firewall flows for this permutation
            for topology_name, (diagram, mapper) in topologies.items():

                src_fw = mapper.find_matching_firewall(src_ip)
                dst_fw = mapper.find_matching_firewall(dst_ip)

                if not src_fw and not dst_fw:
                    #print(f"No firewalls found for both {src_ip} and {dst_ip} in {topology_name}")
                    missing_ips_in_topologies[topology_name].update([src_ip, dst_ip])
                    continue
                if not src_fw:
                    #print(f"No firewall found for {src_ip} in {topology_name}")
                    missing_ips_in_topologies[topology_name].add(src_ip)
                    continue
                if not dst_fw:
                    #print(f"No firewall found for {dst_ip} in {topology_name}")
                    missing_ips_in_topologies[topology_name].add(dst_ip)
                    continue

                flow = diagram.find_flows_with_firewalls(src_fw, dst_fw)
                #  Pick the minimum length flow i.e. the shortest path in the topology
                flow = min(flow, key=len)
                rule_src_dst_permutations.append(((src_ip, dst_ip), topology_name, flow))

        # Expand out from the path determined for this permutation all the gateways
        # that require this rule to be installed on
        # this will allow regrouping based on the installed on gateway
        rule_src_dst_permutations = filter_include_flows.filter_ip_data(rule_src_dst_permutations, topology_inc_flows)
        rule_src_dst_permutations = filter_excluded_flows.filter_ip_data(rule_src_dst_permutations, topology_exc_flows)