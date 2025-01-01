from collections import defaultdict
from ipaddress import IPv4Interface


def group_by_second_element(data):
    grouped = defaultdict(list)

    for item in data:
        # Extract the IP tuple and the group key (COR/DMZ)
        ip_tuple, group_key, _ = item

        # Add the IP tuple to the appropriate group
        grouped[group_key].append(ip_tuple)

    return dict(grouped)


# Example usage:
data = [
    ((IPv4Interface('10.181.0.32/29'), IPv4Interface('10.233.2.0/27')), 'COR', ['BQA-PVCORFW401', 'BQA-PVDMZFW301']),
    ((IPv4Interface('10.181.0.32/29'), IPv4Interface('10.233.2.0/27')), 'DMZ', ['BQA-PVDMZFW401', 'BQA-PVDMZFW301']),
    # ... rest of your data
]

result = group_by_second_element(data)