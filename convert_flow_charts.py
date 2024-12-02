def convert_mermaid_to_dot(mermaid_input, format_endnodes=False, title=None):
    """
    Convert Mermaid flowchart syntax to DOT format for Graphviz

    Args:
        mermaid_input (str): Input string in Mermaid flowchart format
        format_endnodes (bool): If True, format end nodes differently
        title (str, optional): Title to be displayed on the graph. Defaults to None.

    Returns:
        str: Converted flowchart in DOT format
    """
    # Split input into lines and remove empty lines
    lines = [line.strip() for line in mermaid_input.split('\n') if line.strip()]

    # Skip the first line (flowchart LR)
    connection_lines = lines[1:]

    # Track node connections to identify end nodes
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

    # Identify end nodes (nodes with only one connection)
    end_nodes = {node for node, count in node_connections.items() if count == 1}

    # Build DOT format output
    dot_output = ['digraph network_diagram {', '    rankdir=LR;  // Left to right layout']

    # Add title if provided
    if title:
        dot_output.append(f'    label="{title}";')
        dot_output.append('    labelloc="t";  // Place title at top')
        dot_output.append('    fontsize=16;')

    # Add node definitions
    dot_output.append('    // Define nodes with appropriate formatting')
    for node in sorted(node_connections.keys()):
        if format_endnodes and node in end_nodes:
            # End node format
            dot_output.append(f'    {node} [label="{node}", shape=ellipse, style=filled, fillcolor=lightblue];')
        else:
            # Default format
            dot_output.append(f'    {node} [label="{node}", shape=rectangle, style=filled, fillcolor=orange];')

    # Add connections
    dot_output.append('    // Define bidirectional connections')
    for node1, node2 in connections:
        dot_output.append(f'    {node1} -> {node2} [dir=both];')

    dot_output.append('}')

    return '\n'.join(dot_output)