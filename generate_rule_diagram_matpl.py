import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np
from ipaddress import IPv4Interface
from typing import Dict, List, Tuple, Any, Set


def create_firewall_flow_diagram(params: Dict[str, Any], output_file: str = None,
                                 figsize: Tuple[int, int] = (12, 10)):
    """
    Generate a diagram illustrating the flows in a firewall rule.

    Args:
        params (Dict): Dictionary containing all parameters
            - rule_num: Rule number
            - comment: Rule comment text
            - service: Services or ports
            - data: Dictionary of flow data
            - topology_mappers: Dictionary mapping topology names to mapper objects
        output_file (str, optional): Path to save the diagram. If None, displays the diagram.
        figsize (Tuple[int, int], optional): Figure size (width, height)

    Returns:
        matplotlib.figure.Figure: The figure object
    """
    # Extract parameters
    rule_num = params.get('rule_num', '')
    comment = params.get('comment', '')
    service = params.get('service', '')
    flow_data = params.get('data', {})
    topology_mappers = params.get('topology_mappers', {})

    # Create figure and main title
    fig, axes = plt.subplots(figsize=figsize)

    # Set the title with rule number, comment and service
    title = f"Rule {rule_num}: {comment}\nServices: {service}"
    fig.suptitle(title, fontsize=16, fontweight='bold')

    # Set up colors by node type
    node_colors = {
        'firewall': '#ff9900',  # Orange
        'router': '#3366cc',  # Blue
        'server': '#33cc33',  # Green
        'zone': '#cc99ff',  # Light Purple
        'cloud': '#99ccff',  # Light Blue
        '': '#cccccc'  # Gray (default)
    }

    # Set up colors for different topologies
    topology_colors = {
        'MGMT': '#ffd699',  # Light Orange
        'COR': '#d9e6ff',  # Light Blue
        'PERIMETER': '#e6fff2'  # Light Green
    }

    # Hide the axes
    axes.axis('off')

    # Calculate flows per path to determine layout
    num_paths = len(flow_data)
    if num_paths == 0:
        return fig

    # Create a separate subplot for each path
    fig.clear()

    # Determine grid layout based on number of paths
    grid_cols = min(2, num_paths)
    grid_rows = (num_paths + (grid_cols - 1)) // grid_cols

    # Re-add the title to the figure
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)

    # Add each flow path as a separate subplot
    for idx, (path_tuple, path_data) in enumerate(flow_data.items()):
        # Create subplot
        ax = fig.add_subplot(grid_rows, grid_cols, idx + 1)
        ax.axis('off')

        # Get topology for background color
        topology = path_data.get('topology', '')

        # Set background color based on topology
        ax.set_facecolor(topology_colors.get(topology, '#ffffff'))

        # Add border around the subplot
        ax.spines['top'].set_visible(True)
        ax.spines['bottom'].set_visible(True)
        ax.spines['left'].set_visible(True)
        ax.spines['right'].set_visible(True)

        # Create the path title
        path_name = ' → '.join(path_tuple)
        ax.set_title(f"Path: {path_name}", fontsize=10)

        # Draw the flow diagram
        draw_flow_path(ax, path_tuple, path_data, topology_mappers, node_colors)

    # Adjust layout
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    # Save or display the figure
    if output_file:
        fig.savefig(output_file, bbox_inches='tight')

    return fig


def draw_flow_path(ax, path_tuple, path_data, topology_mappers, node_colors):
    """
    Draw a single flow path in the diagram.

    Args:
        ax: Matplotlib axes
        path_tuple: Tuple of node names forming the path
        path_data: Dictionary with source_nodes, destination_nodes, ip_pairs
        topology_mappers: Dictionary mapping topology names to mapper objects
        node_colors: Dictionary mapping node types to colors
    """
    # Get the appropriate topology mapper for this flow
    topology = path_data.get('topology', '')
    mapper = topology_mappers.get(topology)

    # If no mapper found for this topology, try to use a default if available
    if mapper is None:
        mapper = next(iter(topology_mappers.values()), None)
        if mapper is None:
            # No mappers available, can't draw this path properly
            ax.text(0.5, 0.5, f"No mapper found for topology: {topology}",
                    ha='center', va='center', color='red')
            return

    # Extract data
    ip_pairs = path_data.get('ip_pairs', [])
    source_nodes = path_data.get('source_nodes', [])
    destination_nodes = path_data.get('destination_nodes', [])

    # Find IP mappings for source and destination nodes
    node_ip_map = {}

    # Organize nodes by type for better placement
    core_path_nodes = list(path_tuple)  # Main path nodes (horizontal flow)
    source_end_nodes = []  # Source nodes that aren't in the main path
    dest_end_nodes = []  # Destination nodes that aren't in the main path

    # Separate source nodes that aren't in the main path
    for node in source_nodes:
        if node not in core_path_nodes:
            source_end_nodes.append(node)

    # Separate destination nodes that aren't in the main path
    for node in destination_nodes:
        if node not in core_path_nodes:
            dest_end_nodes.append(node)

    # Combine all nodes for IP mapping
    all_nodes = core_path_nodes + source_end_nodes + dest_end_nodes

    # Map nodes to their IPs
    for node_id in all_nodes:
        for src_ip, dst_ip in ip_pairs:
            # Check if this node has this source IP
            if node_id in source_nodes and mapper.is_ip_on_node(node_id, str(src_ip.ip)):
                if node_id not in node_ip_map:
                    node_ip_map[node_id] = []
                if src_ip not in node_ip_map[node_id]:
                    node_ip_map[node_id].append(src_ip)

            # Check if this node has this destination IP
            if node_id in destination_nodes and mapper.is_ip_on_node(node_id, str(dst_ip.ip)):
                if node_id not in node_ip_map:
                    node_ip_map[node_id] = []
                if dst_ip not in node_ip_map[node_id]:
                    node_ip_map[node_id].append(dst_ip)

    # Calculate positions for nodes
    node_positions = {}

    # Position main path nodes horizontally in the center
    num_core_nodes = len(core_path_nodes)
    for i, node_id in enumerate(core_path_nodes):
        node_positions[node_id] = (i / (num_core_nodes - 1 or 1), 0.5)

    # Position source end nodes on the left, vertically distributed
    num_source_end = len(source_end_nodes)
    for i, node_id in enumerate(source_end_nodes):
        # Determine vertical spacing
        if num_source_end > 1:
            vertical_pos = 0.2 + (i * 0.6 / (num_source_end - 1))
        else:
            vertical_pos = 0.5

        # Place to the left of the first core node
        horizontal_pos = 0.0  # Far left
        node_positions[node_id] = (horizontal_pos, vertical_pos)

    # Position destination end nodes on the right, vertically distributed
    num_dest_end = len(dest_end_nodes)
    for i, node_id in enumerate(dest_end_nodes):
        # Determine vertical spacing
        if num_dest_end > 1:
            vertical_pos = 0.2 + (i * 0.6 / (num_dest_end - 1))
        else:
            vertical_pos = 0.5

        # Place to the right of the last core node
        horizontal_pos = 1.0  # Far right
        node_positions[node_id] = (horizontal_pos, vertical_pos)

    # Draw nodes
    node_shapes = {}
    for node_id, (x, y) in node_positions.items():
        node_name = mapper.get_node_name(node_id)
        node_type = mapper.get_node_type(node_id)

        # Determine if this is a special node
        is_source = node_id in source_nodes
        is_destination = node_id in destination_nodes
        is_end = mapper.is_end_node(node_id)

        # Get associated IPs for this node
        node_ips = node_ip_map.get(node_id, [])

        # Draw the node
        node_shape = draw_node(ax, x, y, node_id, node_name, node_type,
                               is_source, is_destination, is_end, node_colors, node_ips)
        node_shapes[node_id] = node_shape

    # Draw connections between nodes in the original path
    for i in range(len(core_path_nodes) - 1):
        src_node = core_path_nodes[i]
        dst_node = core_path_nodes[i + 1]
        src_pos = node_positions[src_node]
        dst_pos = node_positions[dst_node]

        # Draw arrow connecting nodes
        draw_arrow(ax, src_pos, dst_pos)

    # Connect source end nodes to the first core node if applicable
    if core_path_nodes and source_end_nodes:
        first_core_node = core_path_nodes[0]
        first_core_pos = node_positions[first_core_node]

        for src_node in source_end_nodes:
            src_pos = node_positions[src_node]
            # Draw arrow from source end node to first core node
            draw_arrow(ax, src_pos, first_core_pos)

    # Connect last core node to destination end nodes if applicable
    if core_path_nodes and dest_end_nodes:
        last_core_node = core_path_nodes[-1]
        last_core_pos = node_positions[last_core_node]

        for dst_node in dest_end_nodes:
            dst_pos = node_positions[dst_node]
            # Draw arrow from last core node to destination end node
            draw_arrow(ax, last_core_pos, dst_pos)

    # We'll rely on the directly displayed node IPs rather than separate boxes
    # to avoid cluttering the diagram now that we have a more distributed layout

    # Draw IP pairs info
    if ip_pairs:
        # Create a text box for all IP information
        ip_text = "Flow IPs:\n"
        for src_ip, dst_ip in ip_pairs:
            ip_text += f"{src_ip.ip} → {dst_ip.ip}\n"

        # Add text at the bottom
        ax.text(0.5, 0.05, ip_text, ha='center', va='bottom',
                fontsize=8, bbox=dict(boxstyle="round,pad=0.5",
                                      facecolor='white', alpha=0.7))


def draw_node(ax, x, y, node_id, node_name, node_type, is_source, is_destination, is_end, node_colors, node_ips=None):
    """
    Draw a node in the diagram.

    Args:
        ax: Matplotlib axes
        x, y: Coordinates (0-1 range)
        node_id: ID of the node
        node_name: Display name of the node
        node_type: Type of the node (firewall, router, etc.)
        is_source: Whether this is a source node
        is_destination: Whether this is a destination node
        is_end: Whether this is an end node
        node_colors: Dictionary mapping node types to colors
        node_ips: List of IP addresses associated with this node

    Returns:
        The node shape object
    """
    # Determine node appearance based on type
    color = node_colors.get(node_type, node_colors[''])

    # Adjust size based on node type and role
    width, height = 0.12, 0.12  # Make base size a bit smaller

    # Special formatting for end nodes
    if is_end:
        width, height = 0.14, 0.18

    # Special formatting for source or destination nodes
    if is_source or is_destination:
        width, height = 0.16, 0.20  # Make them slightly larger

    # Create shapes based on node type
    if node_type == 'firewall':
        shape = patches.Rectangle((x - width / 2, y - height / 2), width, height,
                                  facecolor=color, edgecolor='black', linewidth=1.5)
    elif node_type == 'cloud':
        # Create a cloud-like shape using an ellipse
        shape = patches.Ellipse((x, y), width * 1.5, height,
                                facecolor=color, edgecolor='black', linewidth=1.5)
    elif node_type == 'server':
        # Create a server-like shape
        shape = patches.FancyBboxPatch((x - width / 2, y - height / 2), width, height,
                                       boxstyle=patches.BoxStyle("Round", pad=0.02),
                                       facecolor=color, edgecolor='black', linewidth=1.5)
    elif node_type == 'zone':
        # Create a zone-like shape (rounded rectangle but smaller)
        shape = patches.FancyBboxPatch((x - width / 2, y - height / 2), width, height,
                                       boxstyle=patches.BoxStyle("Round4", pad=0.2),
                                       facecolor=color, edgecolor='black', linewidth=1.5)
    else:
        # Default shape
        shape = patches.Rectangle((x - width / 2, y - height / 2), width, height,
                                  facecolor=color, edgecolor='black', linewidth=1.5)

    # Add the shape to the axes
    ax.add_patch(shape)

    # Add special border styling for source and destination nodes
    if is_source:
        # Add green border for source
        border = patches.Rectangle((x - width / 2 - 0.01, y - height / 2 - 0.01),
                                   width + 0.02, height + 0.02,
                                   facecolor='none', edgecolor='green', linewidth=2,
                                   linestyle='-')
        ax.add_patch(border)

    if is_destination:
        # Add red border for destination
        border = patches.Rectangle((x - width / 2 - 0.01, y - height / 2 - 0.01),
                                   width + 0.02, height + 0.02,
                                   facecolor='none', edgecolor='red', linewidth=2,
                                   linestyle='-')
        ax.add_patch(border)

    # Create the display name
    if node_name:
        display_name = node_name
    else:
        display_name = node_id

    # Add node type if available
    if node_type:
        display_name += f"\n({node_type})"

    # Add node name
    ax.text(x, y - height / 4, display_name, ha='center', va='center',
            fontsize=9, fontweight='bold')

    # Add IP addresses if available
    if node_ips and len(node_ips) > 0:
        ip_text = "\n".join([str(ip.ip) for ip in node_ips])
        ax.text(x, y + height / 3, ip_text, ha='center', va='center',
                fontsize=7, color='darkblue')

    return shape


def draw_arrow(ax, start_pos, end_pos):
    """
    Draw an arrow between two nodes.

    Args:
        ax: Matplotlib axes
        start_pos: (x, y) starting position
        end_pos: (x, y) ending position
    """
    # Extract coordinates
    x1, y1 = start_pos
    x2, y2 = end_pos

    # Draw the arrow
    ax.arrow(x1, y1, x2 - x1, y2 - y1, head_width=0.02, head_length=0.03,
             fc='black', ec='black', length_includes_head=True)


# Example usage
if __name__ == "__main__":
    # Mock topology mapper for testing
    class MockTopologyMapper:
        def __init__(self):
            self.node_names = {
                "FW1": "Firewall 1",
                "MGMT_FW": "Management FW",
                "TRANSIT_FW": "Transit FW",
                "PERIMETER": "Perimeter Zone",
                "AWS": "AWS Cloud",
                "AZURE": "Azure Cloud"
            }
            self.node_types = {
                "FW1": "firewall",
                "MGMT_FW": "firewall",
                "TRANSIT_FW": "firewall",
                "PERIMETER": "zone",
                "AWS": "cloud",
                "AZURE": "cloud"
            }

        def get_node_name(self, node_id):
            return self.node_names.get(node_id, "")

        def get_node_type(self, node_id):
            return self.node_types.get(node_id, "")

        def is_end_node(self, node_name):
            return self.get_node_type(node_name) in ["server", "cloud"]

        def is_ip_on_node(self, node_name, ip_address):
            # Mock implementation
            return True


    # Create a dictionary of topology mappers for testing
    mappers = {
        'MGMT': MockTopologyMapper(),
        'COR': MockTopologyMapper(),
        'PERIMETER': MockTopologyMapper()
    }

    # Sample rule data (simplified from the provided example)
    params = {
        'rule_num': 1,
        'comment': 'Management traffic \nto MGMT Server',
        'service': 'Syslog, NTP, DNS\nSNMP Trap',
        'data': {
            ('FW1', 'MGMT_FW', 'AWS'): {
                'destination_nodes': ['AWS'],
                'ip_pairs': [
                    (IPv4Interface('192.168.1.10/32'), IPv4Interface('10.200.1.20/32')),
                    (IPv4Interface('192.168.1.20/32'), IPv4Interface('10.200.1.20/32'))
                ],
                'source_nodes': ['FW1'],
                'topology': 'MGMT'
            },
            ('FW1', 'MGMT_FW', 'AZURE'): {
                'destination_nodes': ['AZURE'],
                'ip_pairs': [
                    (IPv4Interface('192.168.1.10/32'), IPv4Interface('10.100.1.10/32')),
                    (IPv4Interface('192.168.1.20/32'), IPv4Interface('10.100.1.10/32'))
                ],
                'source_nodes': ['FW1'],
                'topology': 'MGMT'
            },
            ('FW1', 'TRANSIT_FW', 'PERIMETER', 'AWS'): {
                'destination_nodes': ['AWS'],
                'ip_pairs': [
                    (IPv4Interface('10.1.1.10/32'), IPv4Interface('10.200.1.20/32')),
                    (IPv4Interface('10.1.1.20/32'), IPv4Interface('10.200.1.20/32'))
                ],
                'source_nodes': [],
                'topology': 'COR'
            }
        },
        'topology_mappers': mappers
    }

    fig = create_firewall_flow_diagram(params)
    plt.show()