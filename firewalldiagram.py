import networkx as nx
from collections import OrderedDict


class OrderedSet(OrderedDict):
    def __init__(self, iterable=None):
        super().__init__()
        if iterable is not None:
            for item in iterable:
                self[item] = None

    def add(self, item):
        self[item] = None

    def update(self, iterable):
        for item in iterable:
            self[item] = None


class FirewallDiagram:
    def __init__(self, diagram_file):
        with open(diagram_file) as f:
            self.diagram_text = f.read()
        self.graph = self._parse_diagram()

    def _parse_diagram(self):
        edges = [line.strip().split(" <--> ") for line in self.diagram_text.strip().split('\n')[1:]]
        graph = nx.Graph()
        graph.add_edges_from(edges)
        return graph

    def find_all_paths(self, start_node, end_node):
        return list(nx.all_simple_paths(self.graph, start_node, end_node))

    def get_all_unique_paths(self):
        nodes = list(self.graph.nodes)
        unique_paths = set()
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                paths = self.find_all_paths(nodes[i], nodes[j])
                for path in paths:
                    unique_paths.add(tuple(path))
        return unique_paths

    def find_flows_with_firewalls(self, fw1, fw2):
        paths = self.find_all_paths(fw1, fw2)
        matching_paths = []
        for path in paths:
            if path[0] == fw1 and path[-1] == fw2:
                matching_paths.append(path)
            elif path[0] == fw2 and path[-1] == fw1:
                matching_paths.append(list(reversed(path)))
        return matching_paths

    def get_unique_firewalls(self):
        firewalls = set()
        for node in self.graph.nodes:
            firewalls.add(node)
        return firewalls
