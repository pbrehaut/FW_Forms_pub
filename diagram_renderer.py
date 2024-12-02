import os
import graphviz


def render_diagrams_in_directory(directory):
    render_dir = os.path.join(directory, "Rendered")
    os.makedirs(render_dir, exist_ok=True)

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            input_path = os.path.join(directory, filename)
            output_filename = os.path.splitext(filename)[0]
            output_path = os.path.join(render_dir, output_filename)

            try:
                with open(input_path, 'r') as f:
                    dot_source = f.read()

                graph = graphviz.Source(dot_source)
                graph.render(output_path, format='png', cleanup=True)
                print(f"Rendered: {output_filename}")
            except Exception as e:
                print(f"Error rendering {filename}: {str(e)}")


def render_diagram(diagram_src, output_image):
    try:
        with open(diagram_src, 'r') as f:
            dot_source = f.read()

        graph = graphviz.Source(dot_source)
        graph.render(output_image.replace('.png', ''), format='png', cleanup=True)
        print(f"Rendered: {output_image}")
    except Exception as e:
        print(f"Error rendering {diagram_src}: {str(e)}")