
import gurobipy as gp
from gurobipy import GRB
import csv
import argparse

def read_graph(filename="graph_data.csv"):
    edges = {}
    nodes = set()
    with open(filename, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            u, v, reward, penalty = row[0], row[1], int(row[2]), int(row[3])
            edges[(u, v)] = (reward, penalty)  # Directly use (reward, penalty)
            nodes.add(u)
            nodes.add(v)
    return edges, sorted(nodes, key=lambda x: int(x[1:]))

def solve_ilp(edges, nodes, C, source, target):
    num_nodes = len(nodes)
    
    m = gp.Model()
    
    # Decision variables for edge selection
    x = {}
    for u, v in edges:
        x[u, v] = m.addVar(vtype=GRB.BINARY, name=f"x_{u}_{v}")
    
    # MTZ position variables for subtour elimination
    u_pos = {i: m.addVar(lb=0, ub=num_nodes-1, vtype=GRB.INTEGER, name=f"u_pos_{i}") 
             for i in nodes if i != source}
    
    # Objective function: Maximize total reward
    m.setObjective(gp.quicksum(x[u, v] * edges[u, v][0] for u, v in edges), GRB.MAXIMIZE)

    # Constraint 1: Exactly one outgoing edge from source
    m.addConstr(gp.quicksum(x[source, v] for v in nodes if (source, v) in edges) == 1, "source_out")

    # Constraint 2: Exactly one incoming edge to target
    m.addConstr(gp.quicksum(x[u, target] for u in nodes if (u, target) in edges) == 1, "target_in")

    # Constraint 3: Flow conservation for intermediate nodes
    for node in nodes:
        if node not in [source, target]:
            outgoing = gp.quicksum(x[node, v] for v in nodes if (node, v) in edges)
            incoming = gp.quicksum(x[u, node] for u in nodes if (u, node) in edges)
            m.addConstr(outgoing - incoming == 0, f"flow_{node}")

    # Constraint 4: Total penalty <= C
    m.addConstr(gp.quicksum(x[u, v] * edges[u, v][1] for u, v in edges) <= C, "penalty_limit")
    
    # MTZ subtour elimination constraints
    for u, v in edges:
        if u != source and v != source and u != v:
            m.addConstr(u_pos[u] - u_pos[v] + num_nodes * x[u, v] <= num_nodes - 1, f"mtz_{u}_{v}")
    
    # Set target position constraint
    if target in u_pos:
        m.addConstr(u_pos[target] == num_nodes - 1, "target_position")
    
    m.optimize()
    
    # Extract and display solution
    if m.status == GRB.OPTIMAL:
        solution_path = []
        current = source
        total_reward = 0
        total_penalty = 0
        
        while True:
            solution_path.append(current)
            next_node = None
            for v in nodes:
                if (current, v) in x and x[current, v].X > 0.5:
                    next_node = v
                    break
            if next_node is None or current == target:
                break
            total_reward += edges[current, next_node][0]
            total_penalty += edges[current, next_node][1]
            current = next_node

        print("\nOptimal Path:")
        print(" -> ".join(solution_path))
        print(f"Total Reward: {total_reward}")
        print(f"Total Penalty: {total_penalty}")
        print(f"Constraint Satisfaction: {total_penalty <= C}")
    else:
        print("No feasible solution found")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ILP Solver for RRP Problem')
    parser.add_argument('--input', default='graph_data.csv', help='Input CSV file')
    parser.add_argument('--constraint', type=int, default=50, help='Penalty constraint C')
    parser.add_argument('--source', default='n0', help='Source node')
    parser.add_argument('--target', default=None, help='Target node')
    
    args = parser.parse_args()
    
    edges, nodes = read_graph(args.input)
    
    # Set default target to last node if not specified
    target = args.target if args.target else sorted(nodes, key=lambda x: int(x[1:]))[-1]
    
    # Validate nodes exist in graph
    if args.source not in nodes:
        raise ValueError(f"Source node {args.source} not found in graph")
    if target not in nodes:
        raise ValueError(f"Target node {target} not found in graph")
    
    print(f"Solving RRP problem from {args.source} to {target}")
    print(f"With penalty constraint C = {args.constraint}")
    
    solve_ilp(edges, nodes, args.constraint, args.source, target)


