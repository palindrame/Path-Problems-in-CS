import argparse
import random
import csv

def generate_graph(num_nodes, num_edges, filename="graph_data.csv", weight_range = 10):
    nodes = [f'n{i}' for i in range(num_nodes)]
    edges = []
    
    while len(edges) < num_edges:
        u = random.choice(nodes)
        v = random.choice(nodes)
        if u != v and (u, v) not in [(e[0], e[1]) for e in edges]:
            # Generate non-negative reward and penalty values
            reward = random.randint(0, 10)  # Reward between 0-10
            penalty = random.randint(0, 10)  # Penalty between 0-10
            edges.append((u, v, reward, penalty))
    
    destination_node = nodes[-1]  # The last node is the destination
    
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "reward", "penalty"])
        writer.writerows(edges)
    
    print(f"Graph data saved to {filename} with source: n0 and destination: {destination_node}")
    print("Edges contain (reward, penalty) pairs with non-negative values")
    return filename, destination_node

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a random graph with specified parameters')
    parser.add_argument('--nodes', type=int, default=20, 
                       help='Number of nodes in the graph (default: 20)')
    parser.add_argument('--edges', type=int, default=100,
                       help='Number of edges in the graph (default: 100)')
    parser.add_argument('--range', type=int, default=10,
                       help='Range of edge weights from -N to +N (default: 10)')
    
    args = parser.parse_args()
    
    generate_graph(args.nodes, args.edges, weight_range=args.range)
