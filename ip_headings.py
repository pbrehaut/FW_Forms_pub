import re

def map_ip_to_heading(text):
    lines = text.split('\n')
    ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?:/[0-9]{1,3}|_[0-9]{1,3})?\b')

    headings = []
    for n, line in enumerate(lines):
        current_heading = []
        line = line.strip()
        if not re.search(ip_pattern, line):
            current_heading.append(line)
            for i in range(n + 1, len(lines)):
                next_line = lines[i].strip()
                if re.search(ip_pattern, next_line):
                    break
                current_heading.append(next_line)
            headings.append(current_heading)


    return headings

# Example usage
text = """
Cisco Aurora ASR branch routers
Hostname: boznescr01c10 
10.162.248.2/32
10.162.238.68/30

ISE Admin
P-DMZ_WAN-ISE-10.180.128.145_29
ISE Monitoring
P-inb-ISE_Monitoring-10.192.70.65_28
Zscaler App Connector:
P-DMZ_BIN-Zscaler-10.182.35.97_28
P-DMZ_BIN-Zscaler_Whitelist-10.182.35.113_28
P-DMZ_B2B-Zscaler_Partners-10.181.2.17_28

10.162.249.2/32
10.162.239.68/30
"""

result = map_ip_to_heading(text)
pass