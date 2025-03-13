import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np
from ipaddress import IPv4Interface
from typing import Dict, List, Tuple, Any, Set
import matplotlib.colors as mcolors


def draw_ip_group(ax, x, y, title, ip_list, is_source=True):
    """
    Draw a group of IPs as a single entity with a title.

    Args:
        ax: Matplotlib axes
        x, y: Coordinates (0-1 range) for the center of the IP group
        title: Title for the IP group
        ip_list: List of IP addresses
        is_source: Whether this is a source IP group (green) or destination (red)
    """
    # Create the IP list text
    ip_text = "\n".join(ip_list)

    # Determine styling based on type
    if is_source:
        bg_color = '#e6ffe6'  # Light green
        border_color = 'green'
    else:
        bg_color = '#ffe6e6'  # Light red
        border_color = 'red'

    # Draw the text box
    text_obj = ax.text(x, y, f"{title}:\n{ip_text}",
                       ha='center' if not is_source else 'left',
                       va='center',
                       fontsize=8,
                       bbox=dict(boxstyle="round,pad=0.5",
                                 facecolor=bg_color,
                                 edgecolor=border_color,
                                 linewidth=1.5,
                                 alpha=0.8))

    # Create a visual node for arrow connection
    radius = 0.02
    if is_source:
        node = patches.Circle((x + 0.05, y), radius,
                              facecolor=bg_color,
                              edgecolor=border_color,
                              linewidth=1.5)
    else:
        node = patches.Circle((x - 0.05, y), radius,
                              facecolor=bg_color,
                              edgecolor=border_color,
                              linewidth=1.5)

    ax.add_patch(node)

    # Return the connection point for drawing arrows
    connection_point = (x + 0.05, y) if is_source else (x - 0.05, y)
    return text_obj, connection_point


def create_firewall_flow_diagram(params: Dict[str, Any], output_file: str = None,
                                 figsize: Tuple[int, int] = (10, 18)):
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

    # Use vertical layout with single column
    grid_cols = 1
    grid_rows = num_paths

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

        # Create the path title including topology
        path_name = ' → '.join(path_tuple)
        topology = path_data.get('topology', '')
        ax.set_title(f"Path: {path_name}\nTopology: {topology}", fontsize=10)

        # Draw the flow diagram
        draw_flow_path(ax, path_tuple, path_data, topology_mappers, node_colors)

    # Adjust layout with increased vertical spacing
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    # Add more vertical spacing between subplots
    fig.subplots_adjust(hspace=0.4)

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

    # Position source end nodes on the left side, vertically distributed
    # If there's a first core node, align with it; otherwise use center
    first_core_y = 0.5
    if core_path_nodes:
        first_core_y = node_positions[core_path_nodes[0]][1]

    num_source_end = len(source_end_nodes)
    for i, node_id in enumerate(source_end_nodes):
        # Use vertical spacing with the first core node as the reference point
        if num_source_end > 1:
            # Space them out, starting slightly above the core node
            vertical_offset = (i - (num_source_end - 1) / 2) * 0.15
            vertical_pos = first_core_y + vertical_offset
        else:
            vertical_pos = first_core_y

        # Place to the left of the first core node
        horizontal_pos = 0.0  # Far left
        node_positions[node_id] = (horizontal_pos, vertical_pos)

    # Position destination end nodes on the right, vertically distributed
    # If there's a last core node, align with it; otherwise use center
    last_core_y = 0.5
    if core_path_nodes:
        last_core_y = node_positions[core_path_nodes[-1]][1]

    num_dest_end = len(dest_end_nodes)
    for i, node_id in enumerate(dest_end_nodes):
        # Use vertical spacing with the last core node as the reference point
        if num_dest_end > 1:
            # Space them out, starting slightly above the core node
            vertical_offset = (i - (num_dest_end - 1) / 2) * 0.15
            vertical_pos = last_core_y + vertical_offset
        else:
            vertical_pos = last_core_y

        # Place to the right of the last core node
        horizontal_pos = 1.0  # Far right
        node_positions[node_id] = (horizontal_pos, vertical_pos)

    # Draw nodes and save their connection points
    node_shapes = {}
    node_connection_points = {}

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
        node_shape, connection_points = draw_node(ax, x, y, node_id, node_name, node_type,
                                                  is_source, is_destination, is_end, node_colors, node_ips)
        node_shapes[node_id] = node_shape
        node_connection_points[node_id] = connection_points

    # Draw connections between nodes in the original path
    for i in range(len(core_path_nodes) - 1):
        src_node = core_path_nodes[i]
        dst_node = core_path_nodes[i + 1]

        # Calculate which connection points to use
        src_points = node_connection_points[src_node]
        dst_points = node_connection_points[dst_node]

        # Use the right point of source and left point of destination
        src_pos = src_points['right']
        dst_pos = dst_points['left']

        # Draw arrow connecting nodes
        draw_arrow(ax, src_pos, dst_pos)

    # Connect source end nodes to the first core node if applicable
    if core_path_nodes and source_end_nodes:
        first_core_node = core_path_nodes[0]
        first_core_points = node_connection_points[first_core_node]
        first_core_pos = first_core_points['left']  # Connect to the left side

        for src_node in source_end_nodes:
            src_points = node_connection_points[src_node]
            src_pos = src_points['right']  # Connect from the right side
            # Draw arrow from source end node to first core node
            draw_arrow(ax, src_pos, first_core_pos)

    # Connect last core node to destination end nodes if applicable
    if core_path_nodes and dest_end_nodes:
        last_core_node = core_path_nodes[-1]
        last_core_points = node_connection_points[last_core_node]
        last_core_pos = last_core_points['right']  # Connect from the right side

        for dst_node in dest_end_nodes:
            dst_points = node_connection_points[dst_node]
            dst_pos = dst_points['left']  # Connect to the left side
            # Draw arrow from last core node to destination end node
            draw_arrow(ax, last_core_pos, dst_pos)

    # Extract all unique source and destination IPs (excluding those already on nodes)
    displayed_ips = set()
    for node_id, ips in node_ip_map.items():
        for ip in ips:
            displayed_ips.add(str(ip.ip))

    unique_src_ips = set()
    unique_dst_ips = set()

    for src_ip, dst_ip in ip_pairs:
        # Only add source IPs that aren't already displayed on nodes
        if str(src_ip.ip) not in displayed_ips:
            unique_src_ips.add(str(src_ip.ip))

        # Only add destination IPs that aren't already displayed on nodes
        if str(dst_ip.ip) not in displayed_ips:
            unique_dst_ips.add(str(dst_ip.ip))

    # Draw IP groups at the left and right ends of the diagram (only if they have IPs)
    src_connection_point = None
    dst_connection_point = None

    # Position source IPs at the left side at the same height as the first core node
    if unique_src_ips and core_path_nodes:
        first_core_y = node_positions[core_path_nodes[0]][1]
        _, src_connection_point = draw_ip_group(ax, 0.05, first_core_y, "Source IPs", list(unique_src_ips),
                                                is_source=True)

        # Draw arrows from source IP group to first core node
        first_core_points = node_connection_points[core_path_nodes[0]]
        first_core_pos = first_core_points['left']
        draw_arrow(ax, src_connection_point, first_core_pos)

    # Position destination IPs at the right side at the same height as the last core node
    if unique_dst_ips and core_path_nodes:
        last_core_y = node_positions[core_path_nodes[-1]][1]
        _, dst_connection_point = draw_ip_group(ax, 0.95, last_core_y, "Destination IPs", list(unique_dst_ips),
                                                is_source=False)

        # Draw arrow from last core node to destination IP group
        last_core_points = node_connection_points[core_path_nodes[-1]]
        last_core_pos = last_core_points['right']
        draw_arrow(ax, last_core_pos, dst_connection_point)


def draw_node(ax, x, y, node_id, node_name, node_type, is_source, is_destination, is_end, node_colors, node_ips=None):
    """
    Draw a node in the diagram with dynamic sizing based on text content.

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
        Tuple of (node shape object, connection points dictionary)
    """
    # Determine node appearance based on type
    color = node_colors.get(node_type, node_colors[''])

    # Create the display name
    if node_name:
        display_name = node_name
    else:
        display_name = node_id

    # Add node type if available
    if node_type:
        display_name += f"\n({node_type})"

    # Create IP text if available
    ip_text = ""
    if node_ips and len(node_ips) > 0:
        ip_text = "\n".join([str(ip.ip) for ip in node_ips])

    # Measure the text to determine shape size
    # We'll use a temporary text object to measure
    temp_text = ax.text(0, 0, display_name + ("\n" + ip_text if ip_text else ""), fontsize=9)
    bbox = temp_text.get_window_extent(renderer=ax.figure.canvas.get_renderer())
    temp_text.remove()

    # Convert to axis coordinates
    bbox_axis = bbox.transformed(ax.transData.inverted())
    text_width = bbox_axis.width * 1.5  # Add padding
    text_height = bbox_axis.height * 1.5  # Add padding

    # Set minimum size
    min_width, min_height = 0.12, 0.12
    width = max(text_width, min_width)
    height = max(text_height, min_height)

    # Apply scaling factors based on node roles
    if is_end:
        width *= 1.1
        height *= 1.1

    if is_source or is_destination:
        width *= 1.1
        height *= 1.1

    # Create shapes based on node type
    if node_type == 'firewall':
        shape = patches.Rectangle((x - width / 2, y - height / 2), width, height,
                                  facecolor=color, edgecolor='black', linewidth=1.5)
    elif node_type == 'router':
        # Create a diamond shape for routers
        diamond_points = [
            (x, y - height / 2),  # bottom
            (x + width / 2, y),  # right
            (x, y + height / 2),  # top
            (x - width / 2, y)  # left
        ]
        shape = patches.Polygon(diamond_points, facecolor=color, edgecolor='black', linewidth=1.5)
    elif node_type == 'cloud':
        # Create a cloud-like shape using an ellipse
        shape = patches.Ellipse((x, y), width * 1.2, height,
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

    # Add node name
    ax.text(x, y - height / 5 if ip_text else y, display_name, ha='center', va='center',
            fontsize=9, fontweight='bold')

    # Add IP addresses if available
    if ip_text:
        ax.text(x, y + height / 4, ip_text, ha='center', va='center',
                fontsize=7, color='darkblue')

    # Define connection points for edges
    connection_points = {
        'left': (x - width / 2, y),
        'right': (x + width / 2, y),
        'top': (x, y + height / 2),
        'bottom': (x, y - height / 2)
    }

    # Adjust connection points for special shapes
    if node_type == 'router':
        # Diamond shape has different connection points
        connection_points = {
            'left': (x - width / 2, y),
            'right': (x + width / 2, y),
            'top': (x, y + height / 2),
            'bottom': (x, y - height / 2)
        }
    elif node_type == 'cloud':
        # Ellipse shape has different connection points
        connection_points = {
            'left': (x - width * 0.6, y),
            'right': (x + width * 0.6, y),
            'top': (x, y + height / 2),
            'bottom': (x, y - height / 2)
        }

    return shape, connection_points


def draw_arrow(ax, start_pos, end_pos):
    """
    Draw an arrow between two connection points.

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
                "ROUTER1": "Router 1",
                "PERIMETER": "Perimeter Zone",
                "AWS": "AWS Cloud",
                "AZURE": "Azure Cloud"
            }
            self.node_types = {
                "FW1": "firewall",
                "MGMT_FW": "firewall",
                "TRANSIT_FW": "firewall",
                "ROUTER1": "router",
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
            ('FW1', 'ROUTER1', 'MGMT_FW', 'AWS'): {
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