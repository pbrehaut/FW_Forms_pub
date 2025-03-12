def organize_network_paths(rule_src_dst_permutations, mapper):
    """
    Reorganize network paths by grouping common paths together and separating end nodes.

    Args:
        rule_src_dst_permutations: List of tuples with (IP pair, rule, path list)
        mapper: Object with is_end_node method to identify end nodes

    Returns:
        Dictionary with grouped paths and their source/destination nodes
    """
    result = {}

    for ip_pair, topology_name, path in rule_src_dst_permutations:
        # Separate end nodes and regular nodes
        source_nodes = []
        destination_nodes = []
        regular_nodes = []

        for node in path:
            if mapper[topology_name][1].is_end_node(node):
                # Determine if source or destination based on position
                if not regular_nodes:  # If we haven't seen regular nodes yet, it's a source
                    source_nodes.append(node)
                else:  # Otherwise, it's a destination
                    destination_nodes.append(node)
            else:
                regular_nodes.append(node)

        # Create a key for the regular path without end nodes
        path_key = tuple(regular_nodes)

        # Build or update the result dictionary
        if path_key not in result:
            result[path_key] = {
                'topology': topology_name,
                'ip_pairs': [],
                'source_nodes': set(),
                'destination_nodes': set()
            }

        # Add the current information
        result[path_key]['ip_pairs'].append(ip_pair)
        result[path_key]['source_nodes'].update(source_nodes)
        result[path_key]['destination_nodes'].update(destination_nodes)

    # Convert sets to lists for better readability in the final result
    for path_data in result.values():
        path_data['source_nodes'] = list(path_data['source_nodes'])
        path_data['destination_nodes'] = list(path_data['destination_nodes'])

    return result