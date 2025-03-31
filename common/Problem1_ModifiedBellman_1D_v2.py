import csv
import math
import argparse
from collections import defaultdict

def load_graph_from_csv(filename):
    """Load a graph from a CSV file"""
    graph = defaultdict(dict)
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) != 3:
                continue
            source, target, weight = row
            try:
                graph[source][target] = int(weight)
            except ValueError:
                continue
    return graph

class PathLabel:
    """Represents a path using the label structure"""
    def __init__(self, reward, penalty, pred=None, last_edge=None, visited_nodes=None):
        self.reward = reward
        self.penalty = penalty
        self.pred = pred
        self.last_edge = last_edge
        self.visited_nodes = visited_nodes.copy() if visited_nodes else set()
        if last_edge:
            self.visited_nodes.update(last_edge)

    def get_value(self):
        return self.reward - self.penalty
    
    def reconstruct_path(self):
        edges = []
        current = self
        while current:
            if current.last_edge:
                edges.append(current.last_edge)
            current = current.pred
        path = []
        for u, v in reversed(edges):
            if not path:
                path.append(u)
            path.append(v)
        return path

class FPTAS_BiObjectiveSP:
    def __init__(self, graph, source, target, epsilon):
        self.graph = graph
        self.source = source
        self.target = target
        self.epsilon = epsilon
        
        # Collect all nodes
        self.nodes = set()
        for u in graph:
            self.nodes.add(u)
            self.nodes.update(graph[u].keys())
        self.n = len(self.nodes)
        self.delta = epsilon / (self.n - 1) if self.n > 1 else 0
        
        # Transform graph
        self.bi_graph = self.transform_graph()
        self.max_reward, self.max_penalty = self.find_max_values()
        
        self.Wx = self.max_reward * (self.n - 1)
        self.Wy = self.max_penalty * (self.n - 1)
        self.num_buckets = math.ceil(self.Wx / self.delta) + 1 if self.delta > 0 else 1

    def transform_graph(self):
        bi_graph = defaultdict(dict)
        for u in self.graph:
            for v, weight in self.graph[u].items():
                bi_graph[u][v] = (weight, 0) if weight >= 0 else (0, abs(weight))
        return bi_graph

    def find_max_values(self):
        max_reward = 0
        max_penalty = 0
        for u in self.bi_graph:
            for v, (r, p) in self.bi_graph[u].items():
                max_reward = max(max_reward, r)
                max_penalty = max(max_penalty, p)
        return max_reward, max_penalty

    def get_bucket(self, reward):
        if self.delta == 0:
            return 0
        return min(int((reward + 1e-9) / self.delta), self.num_buckets - 1)

    def solve(self):
        Pi = [defaultdict(dict) for _ in range(self.n)]
        source_label = PathLabel(0, 0)
        Pi[0][self.source][0] = source_label

        for i in range(1, self.n):
            Pi[i] = defaultdict(dict)
            for v in Pi[i-1]:
                Pi[i][v].update(Pi[i-1][v])
            
            for u in self.bi_graph:
                for v, (r_edge, p_edge) in self.bi_graph[u].items():
                    if u not in Pi[i-1]:
                        continue
                    for bucket, label in Pi[i-1][u].items():
                        if v in label.visited_nodes:
                            continue
                        new_reward = label.reward + r_edge
                        new_penalty = label.penalty + p_edge
                        if new_reward > self.Wx or new_penalty > self.Wy:
                            continue
                        new_label = PathLabel(
                            new_reward, new_penalty,
                            label, (u, v), label.visited_nodes
                        )
                        new_bucket = self.get_bucket(new_reward)
                        if (new_bucket not in Pi[i][v] or 
                            Pi[i][v][new_bucket].penalty < new_penalty):
                            Pi[i][v][new_bucket] = new_label

        if self.target not in Pi[self.n-1] or not Pi[self.n-1][self.target]:
            return None, float('inf')
        
        min_value = float('inf')
        best_label = None
        for bucket, label in Pi[self.n-1][self.target].items():
            if label.get_value() < min_value:
                min_value = label.get_value()
                best_label = label

        if best_label:
            try:
                return best_label.reconstruct_path(), min_value
            except:
                return None, float('inf')
        return None, float('inf')

def main():
    parser = argparse.ArgumentParser(description='FPTAS for Shortest Path in General Digraphs')
    parser.add_argument('--source', type=str, default='n0', help='Source vertex')
    parser.add_argument('--target', type=str, default=None, help='Target vertex')
    parser.add_argument('--epsilon', type=float, default=2.0, help='Error tolerance parameter')
    parser.add_argument('--file', type=str, default='graph_data.csv', help='Input graph file')
    
    args = parser.parse_args()
    graph = load_graph_from_csv(args.file)
    
    if args.target is None:
        all_nodes = set()
        for u in graph:
            all_nodes.add(u)
            all_nodes.update(graph[u].keys())
        args.target = max(all_nodes, key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)

    fptas = FPTAS_BiObjectiveSP(graph, args.source, args.target, args.epsilon)
    path, value = fptas.solve()
    
    if path:
        print(f"Path from {args.source} to {args.target}:")
        print(" -> ".join(path))
        print(f"Path value: {value:.2f}")
    else:
        print("No path found")

if __name__ == "__main__":
    main()

