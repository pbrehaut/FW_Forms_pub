import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, List, Tuple, Any, Set


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
    Draw a single flow path in the diagram with enforced left-to-right flow.
    Source nodes on left, destination nodes on right.

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

    # COMPLETELY NEW APPROACH TO NODE LAYOUT
    # =====================================

    # 1. Classify all nodes by their role (source-only, destination-only, both, or transit)
    all_nodes = set(path_tuple) | set(source_nodes) | set(destination_nodes)

    pure_source_nodes = [n for n in all_nodes if n in source_nodes and n not in destination_nodes]
    pure_dest_nodes = [n for n in all_nodes if n in destination_nodes and n not in source_nodes]
    both_nodes = [n for n in all_nodes if n in source_nodes and n in destination_nodes]
    transit_nodes = [n for n in all_nodes if n not in source_nodes and n not in destination_nodes]

    # 2. Create layout sections from left to right
    left_nodes = pure_source_nodes  # Pure source nodes go on the far left
    middle_left_nodes = both_nodes  # Dual-role nodes (both source and dest) go center-left
    middle_nodes = transit_nodes  # Transit nodes (neither source nor dest) go center
    right_nodes = pure_dest_nodes  # Pure destination nodes go on the far right

    # 3. Remove nodes that aren't in the path from middle sections (they'll be positioned separately)
    path_set = set(path_tuple)
    middle_left_nodes = [n for n in middle_left_nodes if n in path_set]
    middle_nodes = [n for n in middle_nodes if n in path_set]

    # 4. Separate path nodes from non-path nodes (pure endpoints)
    path_left_nodes = [n for n in left_nodes if n in path_set]
    path_right_nodes = [n for n in right_nodes if n in path_set]

    pure_left_endpoints = [n for n in left_nodes if n not in path_set]
    pure_right_endpoints = [n for n in right_nodes if n not in path_set]

    # 5. Construct a new layout order for the main path
    # This maintains the same node visitation order as path_tuple but ensures proper left-to-right role flow
    ordered_path = []
    path_lookup = {node: i for i, node in enumerate(path_tuple)}

    # Add all path nodes by their original ordering in path_tuple
    path_nodes_ordered = []
    for node_type in [path_left_nodes, middle_left_nodes, middle_nodes, path_right_nodes]:
        # Sort each section by the original path order
        node_type_ordered = sorted(node_type, key=lambda n: path_lookup.get(n, float('inf')))
        path_nodes_ordered.extend(node_type_ordered)

    # Replace path_tuple with our new ordered path (preserves proper drawing order)
    ordered_path = path_nodes_ordered

    # Map nodes to their IPs
    all_nodes_list = ordered_path + pure_left_endpoints + pure_right_endpoints

    for node_id in all_nodes_list:
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

    # Calculate positions for nodes with new layout approach
    node_positions = {}

    # Position main path nodes horizontally with proper spacing
    num_path_nodes = len(ordered_path)
    if num_path_nodes > 0:
        for i, node_id in enumerate(ordered_path):
            # Calculate a position that reflects the node's role
            # We'll use the full width (0.2 to 0.8) for the main path
            node_positions[node_id] = (0.2 + (i / (num_path_nodes - 1 or 1)) * 0.6, 0.5)

    # Position pure source endpoints on the far left
    num_pure_left = len(pure_left_endpoints)
    for i, node_id in enumerate(pure_left_endpoints):
        if num_pure_left > 1:
            # Stack them vertically if there are multiple
            vertical_pos = 0.3 + (i / (num_pure_left - 1 or 1)) * 0.4
        else:
            vertical_pos = 0.5
        node_positions[node_id] = (0.05, vertical_pos)  # Far left (x=0.05)

    # Position pure destination endpoints on the far right
    num_pure_right = len(pure_right_endpoints)
    for i, node_id in enumerate(pure_right_endpoints):
        if num_pure_right > 1:
            # Stack them vertically if there are multiple
            vertical_pos = 0.3 + (i / (num_pure_right - 1 or 1)) * 0.4
        else:
            vertical_pos = 0.5
        node_positions[node_id] = (0.95, vertical_pos)  # Far right (x=0.95)

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

    # Draw connections between nodes in the path
    for i in range(len(path_tuple) - 1):
        src_node = path_tuple[i]
        dst_node = path_tuple[i + 1]

        # Skip if nodes aren't in our positions (shouldn't happen but just in case)
        if src_node not in node_positions or dst_node not in node_positions:
            continue

        # Calculate which connection points to use
        src_points = node_connection_points[src_node]
        dst_points = node_connection_points[dst_node]

        # Use the right point of source and left point of destination
        src_pos = src_points['right']
        dst_pos = dst_points['left']

        # Draw arrow connecting nodes
        draw_arrow(ax, src_pos, dst_pos)

    # Connect pure source endpoints to related source nodes in the path
    for left_node in pure_left_endpoints:
        # Find a source node in the path to connect to
        # Prefer the leftmost one
        target_node = None
        for path_node in ordered_path:
            if path_node in source_nodes:
                target_node = path_node
                break

        if target_node:
            # Draw arrow from pure source to path source
            left_points = node_connection_points[left_node]
            target_points = node_connection_points[target_node]
            draw_arrow(ax, left_points['right'], target_points['left'])

    # Connect path destination nodes to pure destination endpoints
    for right_node in pure_right_endpoints:
        # Find a destination node in the path to connect from
        # Prefer the rightmost one
        source_node = None
        for path_node in reversed(ordered_path):
            if path_node in destination_nodes:
                source_node = path_node
                break

        if source_node:
            # Draw arrow from path destination to pure destination
            source_points = node_connection_points[source_node]
            right_points = node_connection_points[right_node]
            draw_arrow(ax, source_points['right'], right_points['left'])

    # Handle loose IP addresses not attached to nodes
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

    # Position source IPs at the far left
    if unique_src_ips:
        # Find position based on left-side nodes if any
        if ordered_path:
            leftmost_y = node_positions[ordered_path[0]][1]
        elif pure_left_endpoints:
            leftmost_y = node_positions[pure_left_endpoints[0]][1]
        else:
            leftmost_y = 0.5

        _, src_connection_point = draw_ip_group(ax, 0.02, leftmost_y, "Source IPs", list(unique_src_ips),
                                                is_source=True)

        # Draw arrows to first path node or first source node
        if ordered_path:
            first_node = ordered_path[0]
            first_points = node_connection_points[first_node]
            first_pos = first_points['left']
            draw_arrow(ax, src_connection_point, first_pos)
        elif pure_left_endpoints:
            # Connect to a pure source endpoint instead
            end_node = pure_left_endpoints[0]
            end_points = node_connection_points[end_node]
            end_pos = end_points['left']
            draw_arrow(ax, src_connection_point, end_pos)

    # Position destination IPs at the far right
    if unique_dst_ips:
        # Find position based on right-side nodes if any
        if ordered_path:
            rightmost_y = node_positions[ordered_path[-1]][1]
        elif pure_right_endpoints:
            rightmost_y = node_positions[pure_right_endpoints[0]][1]
        else:
            rightmost_y = 0.5

        _, dst_connection_point = draw_ip_group(ax, 0.98, rightmost_y, "Destination IPs", list(unique_dst_ips),
                                                is_source=False)

        # Draw arrows from last path node or last destination node
        if ordered_path:
            last_node = ordered_path[-1]
            last_points = node_connection_points[last_node]
            last_pos = last_points['right']
            draw_arrow(ax, last_pos, dst_connection_point)
        elif pure_right_endpoints:
            # Connect from a pure destination endpoint instead
            end_node = pure_right_endpoints[0]
            end_points = node_connection_points[end_node]
            end_pos = end_points['right']
            draw_arrow(ax, end_pos, dst_connection_point)


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
