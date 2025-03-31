# fptas_rrp.py with efficient cycle detection for direct reward-penalty input
import csv
import math
from collections import defaultdict, deque
import argparse

def load_graph_from_csv(filename):
    """Load a graph from a CSV file with reward and penalty columns."""
    graph = defaultdict(dict)
    
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        
        for row in reader:
            source, target, reward, penalty = row
            reward = int(reward)
            penalty = int(penalty)
            graph[source][target] = (reward, penalty)
    
    return graph

class PathLabel:
    """Represents a path using the label structure with efficient cycle detection."""
    def __init__(self, reward, penalty, pred=None, last_edge=None, visited_nodes=None):
        self.reward = reward
        self.penalty = penalty
        self.pred = pred  # Pointer to predecessor label
        self.last_edge = last_edge  # Tuple (u, v) representing the last edge
        
        # Set of nodes visited along this path
        if visited_nodes is None:
            self.visited_nodes = set()
        else:
            self.visited_nodes = visited_nodes.copy()  # Create a copy to avoid shared references
            
        # Add the current edge's nodes to visited_nodes
        if last_edge:
            self.visited_nodes.add(last_edge[0])
            self.visited_nodes.add(last_edge[1])
    
    def get_cost_tuple(self):
        """Return the cost tuple (reward, penalty)."""
        return (self.reward, self.penalty)
    
    def reconstruct_path(self):
        """Reconstruct the full path by following predecessor pointers."""
        if self.pred is None:
            # This is either an empty path or a single node path
            if self.last_edge is None:
                return []
            else:
                return [self.last_edge[0], self.last_edge[1]]
        
        # Recursively build the path
        path = self.pred.reconstruct_path()
        # Avoid adding duplicate nodes
        if not path or path[-1] != self.last_edge[0]:
            path.append(self.last_edge[0])
        path.append(self.last_edge[1])
        return path

class FPTAS_RRP:
    def __init__(self, graph, source, target, constraint_C, epsilon):
        """Initialize the FPTAS algorithm for the RRP problem."""
        self.graph = graph
        self.source = source
        self.target = target
        self.C = constraint_C
        self.epsilon = epsilon
        self.n = len(graph)
        self.delta = epsilon / (self.n - 1)
    
    def get_bucket(self, reward):
        """Determine which bucket a reward value belongs to."""
        if reward <= 0:
            return 0
        return math.floor(math.log(reward, 1 + self.delta))
    
    def run(self):
        """Run the FPTAS algorithm to find the approximate optimal path."""
        # Dictionary to store labels for each node and bucket
        # Format: pareto_sets[node][bucket] = PathLabel
        pareto_sets = {node: {} for node in self.graph}
        
        # Initialize the source node with an empty path
        initial_label = PathLabel(0, 0, None, None)
        initial_label.visited_nodes.add(self.source)  # Add source node to visited set
        pareto_sets[self.source][0] = initial_label
        
        # Queue for nodes to process
        queue = deque([self.source])
        in_queue = {self.source}
        
        while queue:
            node = queue.popleft()
            in_queue.remove(node)
            
            # Process each label at the current node
            for bucket, label in list(pareto_sets[node].items()):
                reward, penalty = label.reward, label.penalty
                
                # Process each neighbor
                for neighbor, (edge_reward, edge_penalty) in self.graph[node].items():
                    # O(1) cycle check using the visited_nodes set
                    if neighbor in label.visited_nodes:
                        continue
                    
                    # Calculate new reward and penalty
                    new_reward = reward + edge_reward
                    new_penalty = penalty + edge_penalty
                    
                    # Skip if the new penalty exceeds the constraint
                    if new_penalty > self.C:
                        continue
                    
                    # Get the bucket for the new reward
                    new_bucket = self.get_bucket(new_reward)
                    
                    # Check if we already have a path for this bucket
                    is_dominated = False
                    
                    if new_bucket in pareto_sets[neighbor]:
                        existing_label = pareto_sets[neighbor][new_bucket]
                        if existing_label.penalty <= new_penalty:
                            is_dominated = True
                    
                    if not is_dominated:
                        # Create a new label for the extended path
                        new_label = PathLabel(new_reward, new_penalty, label, (node, neighbor), label.visited_nodes)
                        pareto_sets[neighbor][new_bucket] = new_label
                        
                        # Add the neighbor to the queue for processing
                        if neighbor not in in_queue:
                            queue.append(neighbor)
                            in_queue.add(neighbor)
        
        # Find the best path to the target that satisfies the constraint
        best_reward = 0
        best_label = None
        best_penalty = float('inf')
        
        for bucket, label in pareto_sets[self.target].items():
            if label.penalty <= self.C and label.reward > best_reward:
                best_reward = label.reward
                best_penalty = label.penalty
                best_label = label
            # Break ties in favor of lower penalty
            elif label.penalty <= self.C and label.reward == best_reward and label.penalty < best_penalty:
                best_penalty = label.penalty
                best_label = label
        
        if best_label:
            best_path = best_label.reconstruct_path()
            return (best_reward, best_penalty, best_path)
        else:
            return None
        
    def print_path_details(self, path):
        """Print detailed information about a path, including edge weights."""
        if not path or len(path) < 2:
            return
            
        print("\nDetailed path information:")
        total_reward = 0
        total_penalty = 0
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            edge_reward, edge_penalty = self.graph[u][v]
            
            print(f"  {u} -> {v}: +{edge_reward} (reward), {edge_penalty} (penalty)")
            total_reward += edge_reward
            total_penalty += edge_penalty
        
        print(f"\nSum of rewards: {total_reward}")
        print(f"Sum of penalties: {total_penalty}")

def main():
    parser = argparse.ArgumentParser(description='FPTAS for the Restricted Rewarding Path problem')
    parser.add_argument('--input', type=str, default='graph_data.csv', help='Input graph CSV file')
    parser.add_argument('--source', type=str, default='n0', help='Source node')
    parser.add_argument('--target', type=str, default=None, help='Target node (defaults to last node)')
    parser.add_argument('--constraint', type=float, default=50, help='Penalty constraint C')
    parser.add_argument('--epsilon', type=float, default=0.1, help='Approximation parameter epsilon')
    
    args = parser.parse_args()
    
    # Load the graph
    graph = load_graph_from_csv(args.input)
    
    # If target is not provided, use the last node
    target_node = args.target
    if target_node is None:
        all_nodes = set([node for node in graph])
        node_numbers = [int(node[1:]) for node in all_nodes if node.startswith('n')]
        if node_numbers:
            target_node = f'n{max(node_numbers)}'
        else:
            print("Error: Could not determine target node automatically.")
            return
    
    print(f"Running FPTAS for RRP from {args.source} to {target_node}")
    print(f"Constraint C = {args.constraint}, Epsilon = {args.epsilon}")
    
    # Run the FPTAS algorithm
    fptas = FPTAS_RRP(graph, args.source, target_node, args.constraint, args.epsilon)
    result = fptas.run()
    
    if result:
        reward, penalty, path = result
        print(f"\nBest path: {' -> '.join(path)}")
        print(f"Total reward: {reward}")
        print(f"Total penalty: {penalty}")
        print(f"Constraint satisfied: {penalty <= args.constraint}")
        
        # Print detailed path information
        fptas.print_path_details(path)
    else:
        print("\nNo path found that satisfies the constraint.")

if __name__ == "__main__":
    main()

