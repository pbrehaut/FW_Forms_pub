from collections import defaultdict

def group_data(data):
    # Dictionary to store grouped data
    grouped_data = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    for item in data:
        # Split the string on the first comma to separate rule and firewall/flow parts
        rule_part, firewall_flow = item.split(', ')

        # Split the rule part on the ':' to get the individual components
        rule_id, topology, firewall = rule_part.split(':')

        # Store the rule ID and firewall flow in the grouped data under the topology and firewall keys
        grouped_data[topology][firewall][rule_id].add(firewall_flow)

    #  Convert to a printable string with indenting and carriage returns
    printable_data = ""
    for topology, firewall_data in grouped_data.items():
        printable_data += f"Topolgoy: {topology}\n"
        for firewall, rules in firewall_data.items():
            printable_data += f"{firewall}: ["
            for n, rule_flows in enumerate(rules.items()):
                rule, flows = rule_flows
                printable_data += f" Rule: {rule}, Flow: {', '.join([x.split()[-1] for x in flows])}"
                if n < len(rules) - 1:
                    printable_data += " | "  # Add a separator if it's not the last rule
                else:
                    printable_data += "]"  # Close the rule list
            printable_data += "\n"  # Add a newline after each firewall
        printable_data += "\n"

    return printable_data

