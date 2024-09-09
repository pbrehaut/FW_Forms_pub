from datetime import datetime
import json
from os.path import join
from firewalldiagram import FirewallDiagram
from subnetfirewallmapper import SubnetFirewallMapper
from findips import find_ip_addresses
from configmanager import ConfigManager
from group_rules import *
from data_transform_funcs import *
from write_excel_from_tmpl import *
import generate_diagram
import generate_detailed_diagram
from combine_diagrams import combine_tuple_fields
import os
import ip_headings


def create_subdirectories(base_dir):
    subdirectories = [
        "diagram_images",
        "diagram_source_files",
        "excel_fw_forms",
        "json_rule_dumps"
    ]

    for subdirectory in subdirectories:
        full_path = os.path.join(base_dir, subdirectory)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created subdirectory: {full_path}")
        else:
            print(f"Subdirectory already exists: {full_path}")


def datetime_for_filename():
    return datetime.now().strftime("%d_%b_%y_%H-%M-%S")


def src_dst_permutations(src_ips, dst_ips):
    '''Yield the permutations of the list of source
    IP's and destination IP's'''
    for src_ip in src_ips:
        for dst_ip in dst_ips:
            yield src_ip, dst_ip


def generate_output(cust_rules, config_mgr, file_prefix=None):
    #  Get the 1st key of the cust_rules dictionary and
    #  generate an exception if there is more than one, we only want one customer
    if len(cust_rules) > 1:
        raise Exception("Only one customer can be processed at a time")
    else:
        cust = list(cust_rules.keys())[0]

    rules = cust_rules[cust]
    # create the output directory if it doesn't exist
    create_subdirectories(config_mgr.get_output_directory(cust))

    # Save cust_rules to a json file so the user can reload this later if they need to
    out_dict = {cust: rules}
    with open(join(config_mgr.get_output_directory(cust), "json_rule_dumps", f'{cust}_{datetime_for_filename()}.json'), 'w') as f:
        json.dump(out_dict, f, indent=4)

    # Get the topology file paths for each topology for this customer
    # And initialise the subnet firewall Mapper and diagram objects
    topologies = {}

    # Maintain a list of IP addresses that were not found in the topology and returned them to the user
    missing_ips_in_topologies = defaultdict(set)

    #  Get the Excel config for this customer
    excel_headers = config_mgr.get_excel_config(cust)

    #  Get the detailed diagram value, this will determine what type diagram is printed
    detailed_diagrams = excel_headers.pop('detailed_diagrams', 'no')
    if detailed_diagrams.lower() == 'no':
        detailed_diagrams = False
    else:
        detailed_diagrams = True

    #  Get the group_gateways value
    #  this will determine whether the rules are regrouped again and the gateways concatenated
    group_gateways = excel_headers.pop('group_gateways', 'no')
    if group_gateways.lower() == 'no':
        group_gateways = False
    else:
        group_gateways = True

    #  Print out the flow count subheading when outputting the rules
    inc_flow_count = excel_headers.pop('include_flow_count', 'no')
    if inc_flow_count.lower() == 'no':
        inc_flow_count = False
    else:
        inc_flow_count = True

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

        # Add the topologies to the dictionary using the subsection as the key
        topologies[subsection] = (diagram, mapper)

    rows_to_output = []
    rules_diagrams = defaultdict(list)

    #   Find the IP addresses for the rules
    for original_rule_id, rule in enumerate(rules, start=1):
        # Initialise a dictionary for the mapping of IP addresses to the original content of the rule for that IP
        ip_full_text_mapping = {}
        src, dst, port, comment = rule

        # Add headings back in later
        src_headings = ip_headings.map_ip_to_heading(src)
        dst_headings = ip_headings.map_ip_to_heading(dst)

        # swap back in newline to comments
        comment = comment.replace('; ', '\n')
        #   Find the IP addresses for the source and destination
        src_ips, text_map1 = find_ip_addresses(src)
        dst_ips, text_map2 = find_ip_addresses(dst)
        ip_full_text_mapping.update(text_map1)
        ip_full_text_mapping.update(text_map2)

        #   Get the permutations of the source and destination IP's
        rule_src_dst_permutations = []
        for src_ip, dst_ip in src_dst_permutations(src_ips, dst_ips):
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
        rule_src_dst_permutations = transform_network_data(rule_src_dst_permutations)

        # Group the permutations/combinations on the topology and the install on firewall
        # Subgroup by flow/path.
        # Each item under the grouping of install on a topology will have
        # its own path and the source and destination IPs for that path
        new_rule = group_and_collapse(rule_src_dst_permutations)

        # For each grouping of install on and topology concatenate and format all rows under it
        # which are made up of the different paths/flows
        # add in a flow count ID to allow the user to print this out
        # if they want to know the individual flows within the rule
        # Add back in group headings and host descriptions
        # Add in all the flows grouped on path to create the diagrams and to avoid duplicating the same diagram.
        # The rule IDs and flows will be added to the endpoints for the grouped path/flow.
        # This will allow the user to map back endpoints on the diagram to flows in the rule set
        for topology_install_on, paths in new_rule.items():
            src_list = []
            dst_list = []
            paths_list = []
            topology, install_on = topology_install_on
            new_rule_id = f"{str(original_rule_id)}:{topology}:{install_on}"
            flow_count = 1
            for path, (src, dst, *_) in paths.items():
                rules_diagrams[path].append((src, dst, f"{new_rule_id}, flow {flow_count}"))
                path_joined = str(flow_count) + ': ' + ' --> '.join(path)
                src_list.extend([(x, flow_count) for x in src])
                dst_list.extend([(x, flow_count) for x in dst])
                paths_list.append(path_joined)
                flow_count += 1
            # Swap back in the original text entered by the user
            src_list = [(ip_full_text_mapping.get(ip, ip), fc) for ip, fc in src_list]
            dst_list = [(ip_full_text_mapping.get(ip, ip), fc) for ip, fc in dst_list]

            src_headings_ip = defaultdict(list)
            dst_headings_ip = defaultdict(list)

            for ip, _ in src_list:
                src_headings_ip[src_headings[ip]].append(ip)

            for ip, _ in dst_list:
                dst_headings_ip[dst_headings[ip]].append(ip)

            if inc_flow_count:
                src_str = format_ips(src_list)
                dst_str = format_ips(dst_list)
            else:
                src_str = format_ips_headings(src_headings_ip)
                dst_str = format_ips_headings(dst_headings_ip)

            paths_str = '\n'.join(paths_list)
            rows_to_output.append((src_str, dst_str, port, comment, new_rule_id, paths_str, install_on))

    diagram_files = []
    if detailed_diagrams:
        # If detailed diagrams is specified each flow will have its own source and destination object on the diagram.
        # This will result in separate rules that are grouped together on the same diagram having different
        # source and destination objects
        for path, path_rules in rules_diagrams.items():
            diagram_image_file_name = join(config_mgr.get_output_directory(cust), "diagram_images", "_".join(path))
            diagram_src_file_name = join(config_mgr.get_output_directory(cust), "diagram_source_files", "_".join(path))
            diagram_file = generate_detailed_diagram.create_graphviz_diagram(
                path, path_rules,
                image_filename=diagram_image_file_name,
                src_filename=diagram_src_file_name
            )
            if diagram_file:
                diagram_files.append(join(config_mgr.get_output_directory(cust), diagram_file))
    else:
        # Combine all the flows together that match this path and represent them as one source and destination
        # combination. The IP addresses for the flows will be represented by a start and end IP. The rule numbers and
        # flow IDs will be printed at the top of the diagram in one text block to allow the user to map back the
        # flows on this diagram to the rule set
        for path, path_rules in combine_tuple_fields(rules_diagrams):
            diagram_image_file_name = join(config_mgr.get_output_directory(cust), "diagram_images", "_".join(path))
            diagram_src_file_name = join(config_mgr.get_output_directory(cust), "diagram_source_files", "_".join(path))
            diagram_file = generate_diagram.create_graphviz_diagram(
                path, *path_rules,
                image_filename=diagram_image_file_name,
                src_filename=diagram_src_file_name
            )
            if diagram_file:
                diagram_files.append(join(config_mgr.get_output_directory(cust), diagram_file))

    # Map the field names to index values in each row
    field_mapping = {
        'comments': 3,
        'destination_ips': 1,
        'gateway': 6,
        'services': 2,
        'source_ips': 0,
        'rule_id': 4,
        'paths': 5
    }

    if rows_to_output:
        if group_gateways:
            # Group together any rows that have the same source, destination, port and comments but
            # different install on firewalls and concatenate the install on firewalls
            rows_to_output = group_and_concat_gateways(rows_to_output)
        if file_prefix:
            file_prefix = f"_{file_prefix}"
        else:
            file_prefix = ""
        xlsx_file = join(config_mgr.get_output_directory(cust), "excel_fw_forms", f"FW_Req_{cust}{file_prefix}_{datetime_for_filename()}.xlsx")
        write_to_excel(rows_to_output, excel_headers, field_mapping,
                       filename=xlsx_file,
                       image_files=diagram_files,
                       template=config_mgr.get_template_file(cust))

    # Create a string of missing IPs for each topology
    # This will be output to the user if there are any missing IPs
    # The user can then use this to update the topology file
    missing_ips_str = "\n\n".join([f"Topology: {topology}\n\nSource file: {config_mgr.get_topology(cust, topology).get('topology')}:\n\nMissing IPs (YAML)\n\n  - {'\n  - '.join([str(x) for x in sorted(ips)])}" for topology, ips in missing_ips_in_topologies.items()])
    return missing_ips_str


if __name__ == "__main__":
    config_mgr = ConfigManager('config.ini')
    TEST_DATA = r'C:\Users\pbrehaut4\PycharmProjects\FW_Forms_pub\Sample_data\TEST_Data.json'
    with open(TEST_DATA, 'r') as file:
        cust_rules = json.load(file)
        x_str = generate_output(cust_rules, config_mgr)
    print(x_str)