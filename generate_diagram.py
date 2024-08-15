from graphviz import Digraph


def create_graphviz_diagram(flow, src_ips, dst_ips, comments, image_filename, src_filename):
    comments = [x.replace('\n', '; ') for x in comments]
    comments_str = '\n// '.join(comments)
    label_str = '\\n'.join(comments)
    dot = Digraph(comment=comments_str)
    dot.attr(label=label_str, labelloc='t', fontsize='12')
    dot.attr(rankdir='LR')  # Left to Right layout

    # Set background color
    dot.attr(bgcolor='#F0F8FF')  # Light blue background

    # Add nodes (firewalls)
    for fw in flow:
        dot.node(fw, fw, shape='box', style='filled', fillcolor='#FF9933', color='#994C00')  # Orange firewalls

    # Create source IP node
    src_ips.sort()
    src_label = f"{src_ips[0]}\n...\n{src_ips[-1]}" if len(src_ips) > 1 else src_ips[0]
    src_node = f"src_{flow[0]}"
    dot.node(src_node, src_label, shape='ellipse', style='filled', fillcolor='#66B3FF',
             color='#004080')  # Light blue source

    # Create destination IP node
    dst_ips.sort()
    dst_label = f"{dst_ips[0]}\n...\n{dst_ips[-1]}" if len(dst_ips) > 1 else dst_ips[0]
    dst_node = f"dst_{flow[-1]}"
    dot.node(dst_node, dst_label, shape='ellipse', style='filled', fillcolor='#66B3FF',
             color='#004080')  # Light blue destination

    # Connect source IP to first firewall
    dot.edge(src_node, flow[0], label='src', color='#004080')

    # Connect firewalls
    for i in range(len(flow) - 1):
        dot.edge(flow[i], flow[i + 1], color='#994C00')

    # Connect last firewall to destination IP
    dot.edge(flow[-1], dst_node, label='dst', color='#004080')

    diagram_file = dot.render(filename=image_filename, view=False, cleanup=True, format="png")

    # Write a copy of the diagram text as well to a file
    with open(src_filename + '.txt', "w") as f:
        f.write(dot.source)

    return diagram_file