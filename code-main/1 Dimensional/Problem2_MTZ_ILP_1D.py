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
            edges[(u, v)] = (max(weight, 0), -min(weight, 0))  # Convert to (reward, loss)
            nodes.add(u)
            nodes.add(v)
    return edges, sorted(nodes, key=lambda x: int(x[1:]))

def solve_ilp(edges, nodes, C):
    
    source_node = nodes[0]
    target_node = nodes[-1]
    print(f"The source node is: {source_node}")
    print(f"The destination node is: {target_node}")
    num_nodes = len(nodes)
    
    m = gp.Model()
    
    x = {}
    for u, v in edges:
        x[u, v] = m.addVar(vtype=GRB.BINARY, name=f"x_{u}_{v}")
    
    # MTZ position variables (for subtour elimination)
    u_pos = {i: m.addVar(lb=0, ub=len(nodes)-1, vtype=GRB.INTEGER, name=f"u_pos_{i}") for i in nodes if i != source_node}
    
    # Objective function: Maximize reward
    m.setObjective(gp.quicksum(x[u, v] * edges[u, v][0] for u, v in edges), GRB.MAXIMIZE)

    # Constraint 1: Exactly one outgoing edge from the source
    m.addConstr(gp.quicksum(x[source_node, v] for v in nodes if (source_node, v) in edges) == 1, "c1")

    # Constraint 2: Exactly one incoming edge to the target
    m.addConstr(gp.quicksum(x[u, target_node] for u in nodes if (u, target_node) in edges) == 1, "c2")

    # Constraint 3: Flow conservation for intermediate nodes
    for p in nodes:
        if p not in [source_node, target_node]:
            m.addConstr(
                gp.quicksum(x[p, q] for q in nodes if (p, q) in edges) -
                gp.quicksum(x[r, p] for r in nodes if (r, p) in edges) == 0,
                f"flow_{p}"
            )

    # Constraint: Total loss should be at most C
    m.addConstr(gp.quicksum(x[u, v] * edges[u, v][1] for u, v in edges) <= C, "loss_constraint")
    
    # MTZ subtour elimination constraints
    for i in nodes:
        for j in nodes:
            if i != source_node and j != source_node and i != j and (i, j) in edges:
                m.addConstr(u_pos[i] - u_pos[j] + len(nodes) * x[i, j] <= len(nodes) - 1, f"mtz_{i}_{j}")
    
    
    m.addConstr(u_pos[target_node] == num_nodes - 1, "terminal_position")
    
    m.optimize()
    
    # Extract the solution path in the correct order
    solution_edges = {}
    total_reward = 0
    total_negative_weight = 0

    if m.status == GRB.OPTIMAL:
        for u, v in edges:
            if x[u, v].X > 0.5:
                solution_edges[u] = v  # Store the next node in sequence
                reward, loss = edges[u, v]
                if reward > 0:
                    total_reward += reward
                if loss > 0:
                    total_negative_weight += loss

   
        ordered_path = []
        current_node = source_node
        while current_node in solution_edges:
            ordered_path.append(current_node)
            current_node = solution_edges[current_node]

        # Add the final node
        ordered_path.append(target_node)

        # Print the best path in order
        print("Best Path (ILP Optimal Solution):")
        print(" -> ".join(ordered_path))
        print(f"Total Reward: {total_reward}")
        print(f"Total Negative Weight: {total_negative_weight}")
    else:
        print("No valid path found.")

if __name__ == "__main__":
    edges, nodes = read_graph()
    #C = int(input("Enter constraint value C: "))
    solve_ilp(edges, nodes, 50)

