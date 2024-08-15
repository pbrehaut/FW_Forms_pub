import re
import ipaddress


def find_ip_addresses(text):
    # Regular expression to match valid IPv4 addresses with optional / followed by 1 to 3 digits (any length subnet mask)
    ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?:/[0-9]{1,3}|_[0-9]{1,3})?\b')

    # Split the text by multiple delimiters
    sections = re.split(r'[\n\r;,]', text)

    # List to store valid ip_address objects
    valid_ip_addresses = []
    # Dictionary to store mappings of IP addresses to original text
    ip_text_mapping = {}

    for section in sections:
        # Find all matches in the current section
        ip_addresses = ip_pattern.findall(section)

        for ip in ip_addresses:
            ip_parts = re.split(r'[/_]', ip)  # Split the base IP and the subnet mask
            ip_base = ip_parts[0]  # Base IP address

            # Validate IP address
            if all(0 <= int(part) <= 255 for part in ip_base.split('.')):
                if len(ip_parts) == 2:
                    subnet = int(ip_parts[1])  # Subnet mask or suffix
                    if 0 <= subnet <= 32:  # Typical CIDR validation range for IPv4
                        try:
                            valid_ip_address = ipaddress.ip_interface(f"{ip_base}/{subnet}")
                            valid_ip_addresses.append(valid_ip_address)
                            ip_text_mapping[str(valid_ip_address)] = section.strip()
                        except ValueError:
                            continue
                else:
                    try:
                        valid_ip_address = ipaddress.ip_interface(f"{ip_base}/32")
                        valid_ip_addresses.append(valid_ip_address)
                        ip_text_mapping[str(valid_ip_address)] = section.strip()
                    except ValueError:
                        continue

    return valid_ip_addresses, ip_text_mapping