import networkx as nx
import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB
import csv

def read_graph(filename="graph_data.csv"):
    edges = {}
    nodes = set()
    with open(filename, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            u, v, weight = row[0], row[1], int(row[2])
            edges[(u, v)] = weight
            nodes.add(u)
            nodes.add(v)
    # Sort nodes by numeric suffix (compatible with program2's sorting)
    try:
        nodes = sorted(nodes, key=lambda x: int(x[1:]))
    except ValueError:
        # Fallback to lexicographical order if numeric sorting fails
        nodes = sorted(nodes)
    return edges, nodes

# Read graph from CSV
edges, nodes = read_graph()
source = nodes[0]
target = nodes[-1]

# Create ILP model
m = gp.Model()

# Variables: x[u,v] indicates if edge (u,v) is used
x = {(u, v): m.addVar(vtype=GRB.BINARY, name=f"x_{u}_{v}") for u, v in edges}

# MTZ position variables (exclude source)
u_pos = {i: m.addVar(lb=0, ub=len(nodes)-1, vtype=GRB.INTEGER, name=f"u_pos_{i}") 
          for i in nodes if i != source}

# Objective: Minimize total weight
m.setObjective(gp.quicksum(x[u, v] * edges[(u, v)] for u, v in edges), GRB.MINIMIZE)

# Constraints
# 1. Source has one outgoing edge
m.addConstr(gp.quicksum(x[source, v] for v in nodes if (source, v) in edges) == 1, "c1")

# 2. Target has one incoming edge
m.addConstr(gp.quicksum(x[u, target] for u in nodes if (u, target) in edges) == 1, "c2")

# 3. Flow conservation and degree constraints for intermediate nodes
for p in nodes:
    if p not in [source, target]:
        m.addConstr(
            gp.quicksum(x[p, q] for q in nodes if (p, q) in edges) -
            gp.quicksum(x[r, p] for r in nodes if (r, p) in edges) == 0,
            f"flow_{p}"
        )
        m.addConstr(gp.quicksum(x[p, q] for q in nodes if (p, q) in edges) <= 1, f"out_deg_{p}")
        m.addConstr(gp.quicksum(x[r, p] for r in nodes if (r, p) in edges) <= 1, f"in_deg_{p}")

# MTZ constraints to prevent subtours
for i in nodes:
    for j in nodes:
        if i != source and j != source and i != j and (i, j) in edges:
            m.addConstr(u_pos[i] - u_pos[j] + len(nodes)*x[i, j] <= len(nodes)-1, f"mtz_{i}_{j}")

# Set target's position to last
m.addConstr(u_pos[target] == len(nodes) - 1, "pos_target")

# Solve the model
m.optimize()

# Process and print results
if m.status == GRB.OPTIMAL:
    path_edges = [(u, v) for u, v in edges if x[u, v].X > 0.5]
    solution_edges = {u: v for u, v in path_edges}
    
    # Reconstruct the ordered path
    current_node = source
    ordered_path = [current_node]
    while current_node in solution_edges:
        current_node = solution_edges[current_node]
        ordered_path.append(current_node)
    
    print("Best Path (ILP Optimal Solution):")
    print(" -> ".join(ordered_path))
    print(f"Total Weight: {m.objVal}")
    
    # Optional: Plot the graph with the path highlighted
    # G = nx.DiGraph()
    # G.add_weighted_edges_from((u, v, w) for (u, v), w in edges.items())
    # pos = nx.spring_layout(G)
    # nx.draw(G, pos, with_labels=True, node_size=700, node_color="lightblue", arrowsize=20)
    # nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='r', width=2)
    # edge_labels = {(u, v): w for (u, v), w in edges.items()}
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    #plt.title(f"Optimal Path: Total Weight = {m.objVal}")
    #plt.show()
else:
    print("No optimal solution found.")
