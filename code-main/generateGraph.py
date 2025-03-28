import random
import csv

def generate_graph(num_nodes, num_edges, filename="graph_data.csv"):
    nodes = [f'n{i}' for i in range(num_nodes)]
    edges = []
    
    while len(edges) < num_edges:
        u = random.choice(nodes)
        v = random.choice(nodes)
        if u != v and (u, v) not in [(e[0], e[1]) for e in edges]:
            weight = random.randint(-10, 10)
            edges.append((u, v, weight))
    
    destination_node = nodes[-1]  # The last node is the destination
    
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "weight"])
        writer.writerows(edges)
    
    print(f"Graph data saved to {filename} with source: n0 and destination: {destination_node}")
    
    return filename, destination_node

if __name__ == "__main__":
    num_nodes = 50
    num_edges = 400
    generate_graph(num_nodes, num_edges)

