from graphviz import Digraph
from collections import defaultdict
import group_diagram_comments

def process_tuples(tuple_list):
    # Create a defaultdict to group tuples by their first two elements
    grouped = defaultdict(list)

    # Group tuples by their first two elements
    for item in tuple_list:
        key = (tuple(item[0]), tuple(item[1]))  # Convert lists to tuples for hashability
        grouped[key].append(item[2])

    # Combine the grouped items
    result = []
    for key, comments in grouped.items():
        result.append((list(key[0]), list(key[1]), comments))

    return result

def format_ip_list(ip_list, max_display):
    """
    Format the IP list based on max_display parameter.
    If list length <= max_display, show all IPs.
    Otherwise, show first max_display-1 IPs and the last IP.
    """
    if len(ip_list) <= max_display:
        return '\n'.join(ip_list)
    else:
        displayed_ips = ip_list[:max_display-1] + ['...', ip_list[-1]]
        return '\n'.join(displayed_ips)

def create_graphviz_diagram(flow, ip_tuples, image_filename, src_filename, node_comments, max_ips_display):
    dot = Digraph(comment='Network Flow Diagram')
    dot.attr(rankdir='LR')  # Left to Right layout
    dot.attr(bgcolor='#F0F8FF')  # Light blue background

    ip_tuples = process_tuples(ip_tuples)

    # Define different color pairs (fillcolor, color)
    color_pairs = [
        ('#66B3FF', '#004080'),  # Light blue, Dark blue
        ('#FFDAB9', '#CD853F'),  # Peach puff, Peru
        ('#87CEFA', '#4682B4'),  # Light sky blue, Steel blue
        ('#AFEEEE', '#5F9EA0'),  # Pale turquoise, Cadet blue
        ('#F0FFF0', '#228B22'),  # Honeydew, Forest green
        ('#F0FFFF', '#00CED1'),  # Azure, Dark turquoise
        ('#FAF0E6', '#D2691E')   # Linen, Chocolate
    ]

    # Add nodes (firewalls)
    for fw in flow:
        dot.node(fw, fw, shape='box', style='filled', fillcolor='#FF9933', color='#994C00')  # Orange firewalls

    # Connect firewalls
    for i in range(len(flow) - 1):
        dot.edge(flow[i], flow[i + 1], color='#994C00')

    # Create nodes for each tuple
    for idx, (src_ip, dst_ip, comments) in enumerate(ip_tuples):
        # Get color pair for this iteration
        fillcolor, color = color_pairs[idx % len(color_pairs)]

        # Sort source IP and destination IP lists
        src_ip.sort()
        dst_ip.sort()

        # Format IP labels using the new function
        src_label = format_ip_list(src_ip, max_ips_display)
        dst_label = format_ip_list(dst_ip, max_ips_display)

        if node_comments:
            new_comments = f"{group_diagram_comments.group_data(comments)}\\n"
        else:
            new_comments = ""

        # Create source IP node
        src_node = f"src_{idx}"
        dot.node(src_node, f"{new_comments}{src_label}", shape='ellipse', style='filled', fillcolor=fillcolor, color=color)

        # Create destination IP node
        dst_node = f"dst_{idx}"
        dot.node(dst_node, f"{new_comments}{dst_label}", shape='ellipse', style='filled', fillcolor=fillcolor, color=color)

        # Connect source IP to first firewall
        dot.edge(src_node, flow[0], label='src', color=color)

        # Connect last firewall to destination IP
        dot.edge(flow[-1], dst_node, label='dst', color=color)

    try:
        diagram_file = dot.render(image_filename, view=False, cleanup=True, format="png")
    except Exception as e:
        print(f"Error rendering diagram: {e}")
        diagram_file = None

    # Write a copy of the diagram text as well to a file
    with open(src_filename + '.txt', "w") as f:
        f.write(dot.source)

    return diagram_file