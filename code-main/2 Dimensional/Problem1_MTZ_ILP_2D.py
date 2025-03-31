import gurobipy as gp
from gurobipy import GRB
import csv
import argparse

def read_graph(filename="graph_data.csv"):
    """Read 2D graph with reward and penalty"""
    edges = {}
    nodes = set()
    with open(filename, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) != 4:
                raise ValueError("Invalid CSV format. Expected: source,target,reward,penalty")
            u, v, reward, penalty = row[0], row[1], int(row[2]), int(row[3])
            edges[(u, v)] = (reward, penalty)
            nodes.update([u, v])
            
    # Sort nodes by numeric suffix or lex order
    try:
        nodes = sorted(nodes, key=lambda x: int(x[1:]))
    except ValueError:
        nodes = sorted(nodes)
    return edges, nodes

def solve_rrp_ilp(edges, nodes, source, target, constraint_C):
    """Solve Restricted Rewarding Path problem using ILP"""
    m = gp.Model("RRP_ILP")
    
    # Decision variables
    x = {(u, v): m.addVar(vtype=GRB.BINARY, name=f"x_{u}_{v}") for u, v in edges}
    
    # MTZ position variables (exclude source)
    u_pos = {n: m.addVar(lb=0, ub=len(nodes)-1, vtype=GRB.INTEGER, name=f"pos_{n}") 
             for n in nodes if n != source}

    # Objective: Maximize total reward
    m.setObjective(gp.quicksum(x[u,v] * reward for (u,v), (reward, _) in edges.items()), GRB.MAXIMIZE)

    # Constraints
    # 1. Source has exactly one outgoing edge
    m.addConstr(gp.quicksum(x[source,v] for u,v in edges if u == source) == 1, "source_out")
    
    # 2. Target has exactly one incoming edge
    m.addConstr(gp.quicksum(x[u,target] for u,v in edges if v == target) == 1, "target_in")
    
    # 3. Flow conservation for intermediate nodes
    for node in nodes:
        if node not in [source, target]:
            outgoing = gp.quicksum(x[node,v] for v in nodes if (node,v) in edges)
            incoming = gp.quicksum(x[u,node] for u in nodes if (u,node) in edges)
            m.addConstr(outgoing == incoming, f"flow_conservation_{node}")
            m.addConstr(outgoing <= 1, f"out_degree_{node}")

    # 4. Penalty constraint
    m.addConstr(gp.quicksum(x[u,v] * penalty for (u,v), (_, penalty) in edges.items()) <= constraint_C, 
               "penalty_limit")

    # 5. MTZ subtour elimination constraints
    for (u, v) in edges:
        if u != source and v != source and u != v:
            m.addConstr(u_pos[u] - u_pos[v] + len(nodes)*x[u,v] <= len(nodes)-1, f"mtz_{u}_{v}")

    # Set target position
    if target in u_pos:
        m.addConstr(u_pos[target] == len(nodes)-1, "target_position")

    m.optimize()

    # Process results
    if m.status == GRB.OPTIMAL:
        path = [source]
        current = source
        total_reward = 0
        total_penalty = 0
        
        while current != target:
            next_nodes = [v for u,v in edges if u == current and x[u,v].X > 0.5]
            if not next_nodes:
                break
            current = next_nodes[0]
            path.append(current)
            total_reward += edges[(path[-2], current)][0]
            total_penalty += edges[(path[-2], current)][1]

        return {
            'path': path,
            'total_reward': total_reward,
            'total_penalty': total_penalty,
            'constraint_satisfied': total_penalty <= constraint_C
        }
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ILP Solver for 2D RRP Problem")
    parser.add_argument('--input', default='graph_data.csv', help='Input CSV file')
    parser.add_argument('--source', default='n0', help='Source node')
    parser.add_argument('--target', help='Target node (default: last node)')
    parser.add_argument('--constraint', type=int, default=50, help='Maximum allowed penalty')
    
    args = parser.parse_args()
    
    try:
        edges, nodes = read_graph(args.input)
        target = args.target or nodes[-1]
        
        if args.source not in nodes:
            raise ValueError(f"Source node {args.source} not found in graph")
        if target not in nodes:
            raise ValueError(f"Target node {target} not found in graph")

        print(f"Solving RRP from {args.source} to {target}")
        print(f"Maximum allowed penalty: {args.constraint}")
        
        result = solve_rrp_ilp(edges, nodes, args.source, target, args.constraint)
        
        if result:
            print("\nOptimal Solution:")
            print(" -> ".join(result['path']))
            print(f"Total Reward: {result['total_reward']}")
            print(f"Total Penalty: {result['total_penalty']}")
            print(f"Constraint Satisfied: {result['constraint_satisfied']}")
        else:
            print("No feasible solution found")
            
    except Exception as e:
        print(f"Error: {str(e)}")

