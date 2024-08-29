import ipaddress
from itertools import groupby
from operator import itemgetter


def transform_network_data(original_data):
    new_data = []

    for item in original_data:
        source_ip, dest_ip = item[0]
        zone = item[1]
        devices = item[2]

        for device in devices:
            new_item = (
                (ipaddress.IPv4Interface(str(source_ip)), ipaddress.IPv4Interface(str(dest_ip))),
                zone,
                devices,  # Keep the original set
                device  # Add the individual device as a new field
            )
            new_data.append(new_item)

    return new_data


def format_ips(data):
    # Sort the data by the second element of each tuple
    sorted_data = sorted(data, key=itemgetter(1))

    # Group the data by the second element
    result = []
    for key, group in groupby(sorted_data, key=itemgetter(1)):
        # Extract first elements, remove duplicates, and sort
        first_elements = sorted(set(item[0] for item in group))

        # Add the key and first elements to the result
        result.append(f"Flow: {str(key)}")
        result.extend([f" -{x}" for x in first_elements])

    # Join all elements with newline characters
    return '\n'.join(result)


def format_ips_headings(data):
    new_str = ''
    for index, (heading, ips) in enumerate(data.items()):
        new_str += f"{heading}\n"
        new_str += '\n'.join(sorted(set([str(ip) for ip in ips])))
        if index < len(data) - 1:
            new_str += '\n\n'
    return new_str
