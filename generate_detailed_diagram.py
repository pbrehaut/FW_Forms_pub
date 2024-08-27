from graphviz import Digraph
from collections import defaultdict


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
        combined_comment = ', '.join(comments)
        result.append((list(key[0]), list(key[1]), combined_comment))

    return result


def create_graphviz_diagram(flow, ip_tuples, image_filename, src_filename):
    dot = Digraph(comment='Network Flow Diagram')
    dot.attr(rankdir='LR')  # Left to Right layout
    dot.attr(bgcolor='#F0F8FF')  # Light blue background

    ip_tuples = process_tuples(ip_tuples)

    # Define different color pairs (fillcolor, color)
    color_pairs = [
        ('#66B3FF', '#004080'),  # Light blue, Dark blue
        # ('#FFB366', '#804000'),  # Light orange, Dark orange
        # ('#99FF99', '#006600'),  # Light green, Dark green
        # ('#FF9999', '#800000'),  # Light red, Dark red
        # ('#E0B0FF', '#4B0082'),  # Light purple, Dark purple
        # ('#FFD700', '#B8860B'),  # Gold, Dark goldenrod
        # ('#98FB98', '#228B22'),  # Pale green, Forest green
        # ('#FFA07A', '#B22222'),  # Light salmon, Firebrick
        ('#87CEFA', '#4682B4'),  # Light sky blue, Steel blue
        # ('#DDA0DD', '#8B008B'),  # Plum, Dark magenta
        # ('#F0E68C', '#BDB76B'),  # Khaki, Dark khaki
        ('#FFDAB9', '#CD853F'),  # Peach puff, Peru
        # ('#98FF98', '#2E8B57'),  # Mint cream, Sea green
        ('#AFEEEE', '#5F9EA0'),  # Pale turquoise, Cadet blue
        # ('#D8BFD8', '#9932CC'),  # Thistle, Dark orchid
        # ('#FFFACD', '#DAA520'),  # Lemon chiffon, Goldenrod
        ('#F0FFF0', '#228B22'),  # Honeydew, Forest green
        # ('#FFF0F5', '#C71585'),  # Lavender blush, Medium violet red
        ('#F0FFFF', '#00CED1'),  # Azure, Dark turquoise
        ('#FAF0E6', '#D2691E')  # Linen, Chocolate
    ]

    # Add nodes (firewalls)
    for fw in flow:
        dot.node(fw, fw, shape='box', style='filled', fillcolor='#FF9933', color='#994C00')  # Orange firewalls

    # Connect firewalls
    for i in range(len(flow) - 1):
        dot.edge(flow[i], flow[i + 1], color='#994C00')

    # Create nodes for each tuple
    for idx, (src_ip, dst_ip, comment) in enumerate(ip_tuples):
        # Get color pair for this iteration
        fillcolor, color = color_pairs[idx % len(color_pairs)]

        # Sort source IP and destination IP lists
        src_ip.sort()
        dst_ip.sort()

        src_label = f"{src_ip[0]}\n...\n{src_ip[-1]}" if len(src_ip) > 1 else src_ip[0]
        dst_label = f"{dst_ip[0]}\n...\n{dst_ip[-1]}" if len(dst_ip) > 1 else dst_ip[0]

        # Create source IP node
        src_node = f"src_{idx}"
        dot.node(src_node, f"{comment.replace(',', '\n')}\\n{src_label}", shape='ellipse', style='filled', fillcolor=fillcolor, color=color)

        # Create destination IP node
        dst_node = f"dst_{idx}"
        dot.node(dst_node, f"{comment.replace(', ', '\n')}\\n{dst_label}", shape='ellipse', style='filled', fillcolor=fillcolor, color=color)

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
