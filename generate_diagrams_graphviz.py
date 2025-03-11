from graphviz import Digraph, Source
from collections import defaultdict
import group_diagram_comments
import ipaddress

# Set up node type shapes
end_node_types = ['server', 'end node', 'load balancer', 'f5']
NODE_STYLE_MAP = {
    'firewall': 'box',
    'router': 'diamond',
    'zone': 'ellipse',
}

for node_type in end_node_types:
    NODE_STYLE_MAP[node_type] = 'box'

# Define color pairs for different node types
NODE_COLOR_MAP = {
    'firewall': ('#FF9933', '#994C00'),  # Orange fill, Dark orange border
    'router': ('#66B3FF', '#004080'),  # Light blue, Dark blue
    'zone': ('#90EE90', '#228B22'),  # Light green, Forest green
}
for node_type in end_node_types:
    NODE_COLOR_MAP[node_type] = ('#FFDAB9', '#CD853F')  # Peach puff, Peru

# Default color for nodes without a specific type
DEFAULT_COLORS = ('#FF9933', '#994C00')  # Orange fill, Dark orange border


def format_ip_list(ip_list, max_display):
    """
    Format the IP list based on max_display parameter.
    If list length <= max_display, show all IPs.
    Otherwise, show first max_display-1 IPs and the last IP.
    """
    if len(ip_list) <= max_display:
        return '\n'.join(ip_list)
    else:
        displayed_ips = ip_list[:max_display - 1] + ['...', ip_list[-1]]
        return '\n'.join(displayed_ips)


def process_tuples(tuple_list):
    """
    Group tuples by their first two elements.
    """
    if not tuple_list or not isinstance(tuple_list[0], tuple):
        return tuple_list

    # Create a defaultdict to group tuples by their first two elements
    grouped = defaultdict(list)

    # Group tuples by their first two elements
    for item in tuple_list:
        key = (tuple(item[0]) if isinstance(item[0], list) else item[0],
               tuple(item[1]) if isinstance(item[1], list) else item[1])
        grouped[key].append(item[2])

    # Combine the grouped items
    result = []
    for key, comments in grouped.items():
        result.append((list(key[0]) if isinstance(key[0], tuple) else key[0],
                       list(key[1]) if isinstance(key[1], tuple) else key[1],
                       comments))

    return result


def create_network_diagram(
        flow,
        ip_data,
        image_filename,
        src_filename,
        diagram_type="multi",  # Options: "multi", "single"
        node_comments=False,  # Controls comment display for both diagram types
        max_ips_display=5,
        node_map=None  # Changed parameter to use SubnetFirewallMapper instance
):
    """
    Unified function to create network flow diagrams.
    """
    # Create the Digraph object
    dot = Digraph(comment='Network Flow Diagram')
    dot.attr(rankdir='LR')  # Left to Right layout
    dot.attr(bgcolor='#F0F8FF')  # Light blue background

    # Handle different diagram types
    if diagram_type == "single":
        # Convert single tuple to expected format
        if isinstance(ip_data, tuple) and len(ip_data) == 3:
            src_ips, dst_ips, comments = ip_data

            # Add diagram title/label if comments are provided and enabled
            if comments and node_comments:
                if isinstance(comments, list):
                    comments_str = '\n// '.join(comments)
                    label_str = group_diagram_comments.group_data(comments)
                else:
                    comments_str = str(comments)
                    label_str = str(comments)
                dot.attr(comment=comments_str)
                dot.attr(label=label_str, labelloc='t', fontsize='12')

            ip_tuples = [([ip for ip in src_ips], [ip for ip in dst_ips], comments)]
        else:
            raise ValueError("For 'single' diagram_type, ip_data must be a tuple of (src_ips, dst_ips, comments)")

    elif diagram_type == "multi":
        # Ensure we have the right format for multi diagrams
        ip_tuples = ip_data
        if ip_tuples and isinstance(ip_tuples[0], tuple) and len(ip_tuples[0]) == 3:
            ip_tuples = process_tuples(ip_tuples)
        else:
            raise ValueError("For 'multi' diagram_type, ip_data must be a list of (src_ips, dst_ips, comments) tuples")
    else:
        raise ValueError("diagram_type must be either 'multi' or 'single'")

    # Check for end nodes (servers or end nodes) at source and destination
    first_node = flow[0]
    last_node = flow[-1]

    src_is_end_node = False
    dst_is_end_node = False

    if node_map:
        first_node_type = node_map.get_node_type(first_node)
        last_node_type = node_map.get_node_type(last_node)

        src_is_end_node = first_node_type in end_node_types
        dst_is_end_node = last_node_type in end_node_types

    # Prepare IP labels for source and destination
    ip_labels = {}
    for idx, (src_ip, dst_ip, comments) in enumerate(ip_tuples):
        # Sort IP lists for consistent display
        if isinstance(src_ip, list):
            src_ip.sort()
        if isinstance(dst_ip, list):
            dst_ip.sort()

        # Format the IP labels
        if isinstance(src_ip, list):
            src_label = format_ip_list(src_ip, max_ips_display)
        else:
            src_label = str(src_ip)

        if isinstance(dst_ip, list):
            dst_label = format_ip_list(dst_ip, max_ips_display)
        else:
            dst_label = str(dst_ip)

        ip_labels[idx] = (src_label, dst_label, comments)

    # Add flow nodes (firewalls, routers, etc.)
    for fw in flow:
        node_type_caption = ""
        node_shape = 'box'
        fillcolor, color = DEFAULT_COLORS

        # Apply node type mapping if available using node_map methods
        if node_map:
            node_type = node_map.get_node_type(fw)
            if node_type:
                node_shape = NODE_STYLE_MAP.get(node_type, 'box')
                node_type_caption = node_type.capitalize()
                fillcolor, color = NODE_COLOR_MAP.get(node_type, DEFAULT_COLORS)

        # Get node name if available using node_map methods
        node_name_caption = node_map.get_node_name(fw) if node_map else None

        # Prepare the caption
        if node_name_caption:
            # Use node_name_caption as primary name
            if node_type_caption:
                node_caption = f"{node_name_caption}\n({node_type_caption})"
            else:
                node_caption = node_name_caption
        else:
            # Fall back to fw if no node_name_caption is available
            if node_type_caption:
                node_caption = f"{fw}\n({node_type_caption})"
            else:
                node_caption = fw

        # Add IP information to the caption for end nodes
        if fw == first_node and src_is_end_node:
            for idx, (src_label, _, _) in enumerate(ip_labels.values()):
                node_caption += f"\nSource IP(s):\n{src_label}"
                break  # Just add the first one to avoid clutter

        if fw == last_node and dst_is_end_node:
            for idx, (_, dst_label, _) in enumerate(ip_labels.values()):
                node_caption += f"\nDestination IP(s):\n{dst_label}"
                break  # Just add the first one to avoid clutter

        dot.node(fw, node_caption,
                 shape=node_shape,
                 style='filled',
                 fillcolor=fillcolor,
                 color=color)

    # Connect flow nodes
    for i in range(len(flow) - 1):
        dot.edge(flow[i], flow[i + 1], color='#994C00')

    # Define different color pairs (fillcolor, color) for multiple groups
    color_pairs = [
        ('#66B3FF', '#004080'),  # Light blue, Dark blue
        ('#FFDAB9', '#CD853F'),  # Peach puff, Peru
        ('#87CEFA', '#4682B4'),  # Light sky blue, Steel blue
        ('#AFEEEE', '#5F9EA0'),  # Pale turquoise, Cadet blue
        ('#F0FFF0', '#228B22'),  # Honeydew, Forest green
        ('#F0FFFF', '#00CED1'),  # Azure, Dark turquoise
        ('#FAF0E6', '#D2691E')  # Linen, Chocolate
    ]

    # Create nodes for each source/destination IP group
    for idx, (src_ip, dst_ip, comments) in enumerate(ip_tuples):
        # Get color pair for this iteration
        fillcolor, color = color_pairs[idx % len(color_pairs)]

        src_label, dst_label = ip_labels[idx][0], ip_labels[idx][1]

        # Add node comments if enabled (but only for multi diagrams)
        if node_comments and comments and diagram_type == "multi":
            if isinstance(comments, list):
                comments_text = group_diagram_comments.group_data(comments)
            else:
                comments_text = str(comments)
            prefix = f"{comments_text}\n"
        else:
            prefix = ""

        # Create source node only if the first flow node is not a server/end node
        if not src_is_end_node:
            src_node = f"src_{idx}"
            dot.node(src_node, f"{prefix}{src_label}", shape='ellipse', style='filled',
                     fillcolor=fillcolor, color=color)
            # Connect to first node in the flow
            dot.edge(src_node, flow[0], label='src', color=color)

        # Create destination node only if the last flow node is not a server/end node
        if not dst_is_end_node:
            dst_node = f"dst_{idx}"
            dot.node(dst_node, f"{prefix}{dst_label}", shape='ellipse', style='filled',
                     fillcolor=fillcolor, color=color)
            # Connect from last node in the flow
            dot.edge(flow[-1], dst_node, label='dst', color=color)

    # Render the diagram
    try:
        diagram_file = dot.render(image_filename, view=False, cleanup=True, format="png")
    except Exception as e:
        print(f"Error rendering diagram: {e}")
        diagram_file = None

    # Write the source to a file
    with open(src_filename + '.txt', "w") as f:
        f.write(dot.source)

    return diagram_file


def convert_from_mermaid(mermaid_input, title=None, node_map=None):  # Updated parameter
    """
    Convert Mermaid flowchart syntax to DOT format for Graphviz

    Args:
        mermaid_input (str): Input string in Mermaid flowchart format
        title (str, optional): Title to be displayed on the graph. Defaults to None.
        node_map (SubnetFirewallMapper, optional): Instance of SubnetFirewallMapper with node information

    Returns:
        str: Converted flowchart in DOT format
    """

    # Split input into lines and remove empty lines
    lines = [line.strip() for line in mermaid_input.split('\n') if line.strip()]

    # Skip the first line (flowchart LR)
    connection_lines = lines[1:]

    # Track node connections
    node_connections = {}
    connections = []

    for line in connection_lines:
        # Split on arrow syntax
        parts = line.split('<-->')
        if len(parts) == 2:
            node1 = parts[0].strip()
            node2 = parts[1].strip()

            # Count connections for each node
            node_connections[node1] = node_connections.get(node1, 0) + 1
            node_connections[node2] = node_connections.get(node2, 0) + 1

            connections.append((node1, node2))

    # Build DOT format output
    dot_output = ['digraph network_diagram {', '    rankdir=LR;  // Left to right layout',
                  '    bgcolor="#F0F8FF";  // Light blue background']

    # Add title if provided
    if title:
        dot_output.append(f'    label="{title}";')
        dot_output.append('    labelloc="t";  // Place title at top')
        dot_output.append('    fontsize=16;')

    # Add node definitions
    dot_output.append('    // Define nodes with appropriate formatting')

    for node in sorted(node_connections.keys()):
        node_formatted = node.replace('-', '_')  # Replace hyphens with underscores

        # Default values
        node_shape = 'box'
        node_type_caption = ""
        node_name_caption = None
        fillcolor, color = DEFAULT_COLORS

        # Apply node type mapping if available using node_map methods
        if node_map:
            node_type = node_map.get_node_type(node)
            if node_type:
                node_shape = NODE_STYLE_MAP.get(node_type, 'box')
                node_type_caption = node_type.capitalize()
                fillcolor, color = NODE_COLOR_MAP.get(node_type, DEFAULT_COLORS)

        # Get node name if available using node_map methods
        if node_map:
            node_name_caption = node_map.get_node_name(node)

        # Prepare the caption using the same logic as in create_network_diagram
        if node_name_caption:
            # Use node_name_caption as primary name
            if node_type_caption:
                node_caption = f"{node_name_caption}\\n({node_type_caption})"
            else:
                node_caption = node_name_caption
        else:
            # Fall back to node if no node_name_caption is available
            if node_type_caption:
                node_caption = f"{node}\\n({node_type_caption})"
            else:
                node_caption = node

        dot_output.append(
            f'    {node_formatted} [label="{node_caption}", shape={node_shape}, style=filled, '
            f'fillcolor="{fillcolor}", color="{color}"];')

    # Add connections
    dot_output.append('    // Define bidirectional connections')
    for node1, node2 in connections:
        node1_formatted = node1.replace('-', '_')
        node2_formatted = node2.replace('-', '_')
        dot_output.append(f'    {node1_formatted} -> {node2_formatted} [dir=both, color="#994C00"];')

    dot_output.append('}')

    return '\n'.join(dot_output)


def render_diagram(diagram_src, output_image):
    try:
        with open(diagram_src, 'r') as f:
            dot_source = f.read()

        graph = Source(dot_source)
        graph.render(output_image.replace('.png', ''), format='png', cleanup=True)
        print(f"Rendered: {output_image}")
    except Exception as e:
        print(f"Error rendering {diagram_src}: {str(e)}")