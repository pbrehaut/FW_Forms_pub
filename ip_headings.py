import re
from collections import defaultdict


def map_ip_to_heading(text):
    lines = text.split('\n')
    ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?:/[0-9]{1,3}|_[0-9]{1,3})?\b')

    headings_ips = defaultdict(list)
    line_n = 0
    current_heading = ''
    while line_n < len(lines):
        if not re.search(ip_pattern, lines[line_n].strip()):
            line_heading_n = line_n
            current_heading = ''
            while line_heading_n < len(lines):
                if re.search(ip_pattern, lines[line_heading_n].strip()):
                    break
                current_heading += lines[line_heading_n].strip() + '\n'
                line_heading_n += 1
            line_n = line_heading_n
        else:
            if re.search(ip_pattern, lines[line_n].strip()):
                sections = [x.strip() for x in re.split(r'[;,]', lines[line_n].strip())]
                headings_ips[current_heading.strip()].extend(sections)
            line_n += 1

    # Reverse the headings_ips dictionary
    ips_headings = {}
    for heading, ips in headings_ips.items():
        for ip in ips:
            ips_headings[ip] = heading
    return ips_headings


if __name__ == '__main__':
    # Example usage
    text = """
    
    10.1.1.1
    10.1.1.2,  10.1.1.3
    
    Cisco Aurora ASR branch routers
    Hostname: boznescr01c10 
    10.162.248.2/32
    10.162.238.68/30
    
    ISE Admin
    P-DMZ_WAN-ISE-10.180.128.145_29
    ISE Monitoring
    P-inb-ISE_Monitoring-10.192.70.65_28
    Zscaler App Connector:
    P-DMZ_BIN-Zscaler-10.182.35.97_28,  10.182.35.98_28, 10.182.35.99_28, 10.182.35.100_28, 10.182.35.101_28
    P-DMZ_BIN-Zscaler_Whitelist-10.182.35.113_28; 10.182.35.114_28; 10.182.35.115_28; 10.182.35.116_28; 10.182.35.117_28
    P-DMZ_B2B-Zscaler_Partners-10.181.2.17_28
    
    10.162.249.2/32
    10.162.239.68/30
    """

    result = map_ip_to_heading(text)
    pass