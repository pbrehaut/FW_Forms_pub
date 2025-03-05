import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
import os
import random

# Define node style maps (unchanged from original)
NODE_STYLE_MAP = {
    'firewall': 's',  # square (equivalent to box)
    'router': 'd',  # diamond
    'zone': 'o',  # circle (closest to ellipse)
    'server': 'o'  # circle (closest to oval)
}

# Define color pairs for different node types (unchanged from original)
NODE_COLOR_MAP = {
    'firewall': ('#FF9933', '#994C00'),  # Orange fill, Dark orange border
    'router': ('#66B3FF', '#004080'),  # Light blue, Dark blue
    'zone': ('#90EE90', '#228B22'),  # Light green, Forest green
    'server': ('#FFDAB9', '#CD853F')  # Peach puff, Peru
}

# Default color for nodes without a specific type
DEFAULT_COLORS = ('#FF9933', '#994C00')  # Orange fill, Dark orange border

# Color pairs for multiple groups
GROUP_COLOR_PAIRS = [
    ('#66B3FF', '#004080'),  # Light blue, Dark blue
    ('#FFDAB9', '#CD853F'),  # Peach puff, Peru
    ('#87CEFA', '#4682B4'),  # Light sky blue, Steel blue
    ('#AFEEEE', '#5F9EA0'),  # Pale turquoise, Cadet blue
    ('#F0FFF0', '#228B22'),  # Honeydew, Forest green
    ('#F0FFFF', '#00CED1'),  # Azure, Dark turquoise
    ('#FAF0E6', '#D2691E')  # Linen, Chocolate
]


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


def create_node_label(node_id, node_type_map=None, node_name_map=None):
    """
    Create a node label based on mappings.
    """
    node_type_caption = ""

    # Apply node type mapping if available
    if node_type_map and node_id in node_type_map:
        node_type = node_type_map[node_id]
        node_type_caption = node_type.capitalize()

    # Get node name if available
    node_name_caption = node_name_map.get(node_id) if node_name_map else None

    # Prepare the caption
    if node_name_caption:
        # Use node_name_caption as primary name
        if node_type_caption:
            node_caption = f"{node_name_caption}\n({node_type_caption})"
        else:
            node_caption = node_name_caption
    else:
        # Fall back to node_id if no node_name_caption is available
        if node_type_caption:
            node_caption = f"{node_id}\n({node_type_caption})"
        else:
            node_caption = node_id

    return node_caption


def create_network_diagram(
        flow,
        ip_data,
        image_filename,
        src_filename,
        diagram_type="multi",  # Options: "multi", "single"
        node_comments=False,  # Controls comment display for both diagram types
        max_ips_display=5,
        node_type_map=None,
        node_name_map=None
):
    """
    Unified function to create network flow diagrams using NetworkX and Matplotlib.

    Parameters:
    -----------
    flow : list
        List of network nodes (e.g., firewalls) in the flow
    ip_data : list or tuple
        For diagram_type="multi": List of tuples (src_ips, dst_ips, comments)
        For diagram_type="single": Tuple of (src_ips, dst_ips, comments)
    image_filename : str
        Base filename for the output diagram image
    src_filename : str
        Base filename for the source file
    diagram_type : str, optional
        "multi" for multiple source/destination IP groups
        "single" for a single source/destination group
    node_comments : bool, optional
        Controls comment display differently based on diagram_type
    max_ips_display : int, optional
        Maximum number of IPs to display for each node
    node_type_map : dict, optional
        Mapping of node names to their types for shape determination
    node_name_map : dict, optional
        Mapping of node IDs to display names

    Returns:
    --------
    str or None
        Path to the generated diagram file, or None if rendering failed
    """
    # Create a directed graph
    G = nx.DiGraph()

    # Handle different diagram types
    if diagram_type == "single":
        # Convert single tuple to expected format
        if isinstance(ip_data, tuple) and len(ip_data) == 3:
            src_ips, dst_ips, comments = ip_data
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

    # Create figure and axis
    plt.figure(figsize=(14, 8))
    ax = plt.gca()

    # Add flow nodes to the graph
    for i, node_id in enumerate(flow):
        # Determine node styling
        node_type = node_type_map.get(node_id) if node_type_map else None
        node_shape = NODE_STYLE_MAP.get(node_type, 's')  # Default to square
        fillcolor, edgecolor = NODE_COLOR_MAP.get(node_type, DEFAULT_COLORS)

        # Create label
        label = create_node_label(node_id, node_type_map, node_name_map)

        # Add node to graph with attributes
        G.add_node(node_id,
                   pos=(i, 0),  # Horizontal position for flow nodes
                   node_type=node_type,
                   shape=node_shape,
                   fillcolor=fillcolor,
                   edgecolor=edgecolor,
                   label=label)

    # Connect flow nodes
    for i in range(len(flow) - 1):
        G.add_edge(flow[i], flow[i + 1],
                   color='#994C00',
                   connection_type='flow')

    # Create IP group nodes
    y_offset_src = -1.5  # Vertical offset for source nodes
    y_offset_dst = 1.5  # Vertical offset for destination nodes

    for idx, (src_ip, dst_ip, comments) in enumerate(ip_tuples):
        # Get color pair for this iteration
        fillcolor, edgecolor = GROUP_COLOR_PAIRS[idx % len(GROUP_COLOR_PAIRS)]

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

        # Add node comments if enabled (but only for multi diagrams)
        if node_comments and comments and diagram_type == "multi":
            if isinstance(comments, list):
                # In a real implementation, you would include group_diagram_comments.group_data here
                comments_text = " / ".join(comments)
            else:
                comments_text = str(comments)

            src_label = f"{comments_text}\n{src_label}"
            dst_label = f"{comments_text}\n{dst_label}"

        # Create unique node IDs
        src_node = f"src_{idx}"
        dst_node = f"dst_{idx}"

        # Add source and destination nodes with attributes
        G.add_node(src_node,
                   pos=(0, y_offset_src - idx * 0.75),  # Position below flow
                   shape='o',  # Circle for IP groups
                   fillcolor=fillcolor,
                   edgecolor=edgecolor,
                   label=src_label,
                   node_type='ip_group')

        G.add_node(dst_node,
                   pos=(len(flow) - 1, y_offset_dst + idx * 0.75),  # Position above flow
                   shape='o',  # Circle for IP groups
                   fillcolor=fillcolor,
                   edgecolor=edgecolor,
                   label=dst_label,
                   node_type='ip_group')

        # Connect source to first flow node and last flow node to destination
        G.add_edge(src_node, flow[0],
                   color=edgecolor,
                   label='src',
                   connection_type='ip')

        G.add_edge(flow[-1], dst_node,
                   color=edgecolor,
                   label='dst',
                   connection_type='ip')

    # Add title for single diagram type
    if diagram_type == "single" and node_comments and ip_tuples[0][2]:
        comments = ip_tuples[0][2]
        if isinstance(comments, list):
            # In a real implementation, you would include group_diagram_comments.group_data here
            title = " / ".join(comments)
        else:
            title = str(comments)
        plt.title(title, fontsize=12)

    # Draw the network diagram
    try:
        # Get node positions
        pos = nx.get_node_attributes(G, 'pos')

        # Draw nodes by type
        flow_nodes = [n for n, data in G.nodes(data=True) if
                      'node_type' in data and data.get('node_type') != 'ip_group']
        ip_nodes = [n for n, data in G.nodes(data=True) if data.get('node_type') == 'ip_group']

        # Draw flow nodes
        for node in flow_nodes:
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=[node],
                node_shape=G.nodes[node]['shape'],
                node_color=G.nodes[node]['fillcolor'],
                edgecolors=G.nodes[node]['edgecolor'],
                node_size=3000,
                alpha=0.8
            )

        # Draw IP group nodes
        for node in ip_nodes:
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=[node],
                node_shape='o',
                node_color=G.nodes[node]['fillcolor'],
                edgecolors=G.nodes[node]['edgecolor'],
                node_size=5000,
                alpha=0.8
            )

        # Draw edges
        flow_edges = [(u, v) for u, v, data in G.edges(data=True) if data.get('connection_type') == 'flow']
        ip_edges = [(u, v) for u, v, data in G.edges(data=True) if data.get('connection_type') == 'ip']

        nx.draw_networkx_edges(
            G, pos,
            edgelist=flow_edges,
            width=2,
            edge_color='#994C00',
            arrows=True,
            arrowstyle='->'
        )

        # Draw IP connection edges with different colors
        edge_colors = [G.edges[edge]['color'] for edge in ip_edges]
        nx.draw_networkx_edges(
            G, pos,
            edgelist=ip_edges,
            width=1.5,
            edge_color=edge_colors,
            arrows=True,
            arrowstyle='->'
        )

        # Draw edge labels
        edge_labels = {(u, v): data.get('label', '') for u, v, data in G.edges(data=True) if 'label' in data}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

        # Draw node labels
        node_labels = {node: data.get('label', node) for node, data in G.nodes(data=True)}

        # Use different font sizes for IP nodes vs. flow nodes
        for node_type, nodes in [('flow', flow_nodes), ('ip', ip_nodes)]:
            labels = {n: node_labels[n] for n in nodes}
            font_size = 10 if node_type == 'flow' else 8
            nx.draw_networkx_labels(G, pos, labels=labels, font_size=font_size, font_weight='bold')

        # Set background color
        ax.set_facecolor('#F0F8FF')  # Light blue background

        # Remove axes
        plt.axis('off')

        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(f"{image_filename}.png", dpi=300, bbox_inches='tight')
        diagram_file = f"{image_filename}.png"

        # Write the graph structure to a file
        with open(f"{src_filename}.txt", "w") as f:
            f.write(f"NetworkX Graph Structure for {image_filename}\n")
            f.write("Nodes:\n")
            for node, data in G.nodes(data=True):
                f.write(f"  {node}: {data}\n")
            f.write("Edges:\n")
            for u, v, data in G.edges(data=True):
                f.write(f"  {u} -> {v}: {data}\n")

        plt.close()
        return diagram_file

    except Exception as e:
        print(f"Error rendering diagram: {e}")
        plt.close()
        return None


def convert_from_mermaid(mermaid_input, title=None, node_type_map=None, node_name_map=None):
    """
    Convert Mermaid flowchart syntax to NetworkX graph

    Args:
        mermaid_input (str): Input string in Mermaid flowchart format
        title (str, optional): Title to be displayed on the graph. Defaults to None.
        node_type_map (dict, optional): Mapping of node names to their types for shape determination
        node_name_map (dict, optional): Mapping of node IDs to display names

    Returns:
        nx.Graph: NetworkX graph representing the flowchart
    """
    # Create an undirected graph for bidirectional connections
    G = nx.Graph()

    # Split input into lines and remove empty lines
    lines = [line.strip() for line in mermaid_input.split('\n') if line.strip()]

    # Skip the first line (flowchart LR)
    connection_lines = lines[1:]

    # Track nodes
    nodes = set()

    # Parse connections
    for line in connection_lines:
        # Split on arrow syntax
        parts = line.split('<-->')
        if len(parts) == 2:
            node1 = parts[0].strip()
            node2 = parts[1].strip()

            # Add nodes to tracking set
            nodes.add(node1)
            nodes.add(node2)

            # Add edge
            G.add_edge(node1, node2)

    # Set node attributes
    for node in nodes:
        # Determine node type and styling
        node_type = node_type_map.get(node) if node_type_map else None
        node_shape = NODE_STYLE_MAP.get(node_type, 's')  # Default to square
        fillcolor, edgecolor = NODE_COLOR_MAP.get(node_type, DEFAULT_COLORS)

        # Create label
        label = create_node_label(node, node_type_map, node_name_map)

        # Set node attributes
        G.nodes[node]['node_type'] = node_type
        G.nodes[node]['shape'] = node_shape
        G.nodes[node]['fillcolor'] = fillcolor
        G.nodes[node]['edgecolor'] = edgecolor
        G.nodes[node]['label'] = label

    # Set graph attributes
    G.graph['title'] = title

    return G


def draw_networkx_diagram(G, output_filename):
    """
    Draw a NetworkX graph as a network diagram using Matplotlib

    Args:
        G (nx.Graph): NetworkX graph to draw
        output_filename (str): Base filename for output image

    Returns:
        str: Path to the generated image file
    """
    # Create figure and axis
    plt.figure(figsize=(12, 8))
    ax = plt.gca()

    # Set positions (using spring layout)
    pos = nx.spring_layout(G, seed=42)

    # Draw nodes
    for node, data in G.nodes(data=True):
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=[node],
            node_shape=data.get('shape', 's'),
            node_color=data.get('fillcolor', DEFAULT_COLORS[0]),
            edgecolors=data.get('edgecolor', DEFAULT_COLORS[1]),
            node_size=3000,
            alpha=0.8
        )

    # Draw edges (bidirectional)
    nx.draw_networkx_edges(
        G, pos,
        width=2,
        edge_color='#994C00',
        arrows=False  # No arrows for undirected
    )

    # Draw node labels
    node_labels = {node: data.get('label', node) for node, data in G.nodes(data=True)}
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10, font_weight='bold')

    # Add title if available
    if 'title' in G.graph and G.graph['title']:
        plt.title(G.graph['title'], fontsize=14)

    # Set background color
    ax.set_facecolor('#F0F8FF')  # Light blue background

    # Remove axes
    plt.axis('off')

    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(f"{output_filename}.png", dpi=300, bbox_inches='tight')

    plt.close()
    return f"{output_filename}.png"