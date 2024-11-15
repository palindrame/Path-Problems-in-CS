import networkx as nx
import random
import pandas as pd

# Parameters
num_edges = 350
num_nodes = 30

# Generate a directed graph
G = nx.DiGraph()

# Add edges with random weights (positive, negative, or zero)
for _ in range(num_edges):
    src = random.randint(0, num_nodes - 1)
    dest = random.randint(0, num_nodes - 1)
    weight = random.choice([-1, 0, 1]) * random.randint(1, 10)  # Random weight: positive, negative, or zero
    G.add_edge(src, dest, weight=weight)

# Extract edge data into a DataFrame
edges_data = [{"src": u, "dest": v, "weight": d["weight"]} for u, v, d in G.edges(data=True)]
edges_df = pd.DataFrame(edges_data)

# Display the first few rows of the edges data
print(edges_df.head())
# Save the edges to a CSV file
edges_df.to_csv("graph_data.csv", index=False)
print("Graph saved to graph_data.csv")
