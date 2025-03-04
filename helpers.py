def get_topology(result_list):
    extracted_values = set()

    for item in result_list:
        # Get the third element of each tuple (the string with format like '1:COR:FW1, flow 1')
        field_string = item[2]

        # Split by ':' and get the second element
        fields = field_string.split(':')
        if len(fields) >= 2:
            extracted_values.add(fields[1])

    if len(extracted_values) == 1:
        return extracted_values.pop()
    else:
        return None


def get_topology_single(result_list):
    extracted_values = set()
    for item in result_list[2]:
        # Get the third element of each tuple (the string with format like '1:COR:FW1, flow 1')
        field_string = item

        # Split by ':' and get the second element
        fields = field_string.split(':')
        if len(fields) >= 2:
            extracted_values.add(fields[1])

    if len(extracted_values) == 1:
        return extracted_values.pop()
    else:
        return None

def get_diagram_data(rules_diagrams, detailed_diagrams, combine_func):
    """Helper function to prepare data for diagram generation based on detailed_diagrams flag."""
    if detailed_diagrams:
        # For detailed diagrams, yield each path with its rules directly
        for path, path_rules in rules_diagrams.items():
            yield path, path_rules, get_topology, "multi"
    else:
        # For combined diagrams, apply the combine function first
        for path, path_rules in combine_func(rules_diagrams):
            yield path, path_rules, get_topology_single, "single"