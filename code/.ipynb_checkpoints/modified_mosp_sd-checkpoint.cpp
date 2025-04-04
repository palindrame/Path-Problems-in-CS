#include <bits/stdc++.h>
#include <unordered_set>
using namespace std;

class Edge {
public:
    int source, destination;
    int weight_x, weight_y;
    Edge() {}
    Edge(int s, int d, int w) {
        source = s;
        destination = d;
        if (w > 0) {
            weight_x = 0;
            weight_y = w;
        } else {
            weight_x = -w;
            weight_y = 0;
        }
    }
};

class path {
public:
    pair<int, int> cost;
    path *prev;
    Edge *last_edge;
    path() {}
    path(pair<int, int> c, path *p, Edge *e) {
        cost = c;
        prev = p;
        last_edge = e;
    }
};

int operator==(path &p1, path &p2) {
    return (p1.cost == p2.cost && p1.prev == p2.prev && p1.last_edge == p2.last_edge);
}

path empty_c = {make_pair(-1, 1), NULL, NULL};

int pos(path p, float epsilon) {
    return (p.cost.first) / epsilon;
}

vector<path> Extend_Merge(int num_nodes, vector<path> &R, vector<path> &Q, int src, int des, Edge *e, float eps, vector<vector<vector<int>>> &map, unordered_set<int> &nextActiveSet) {
    for (int i = 0; i < Q.size(); i++) {
        if (Q[i] == empty_c || map[des][src][i])
            continue;
        path q;
        q.cost = make_pair(Q[i].cost.first + e->weight_x, Q[i].cost.second + e->weight_y);
        q.prev = &Q[i];
        q.last_edge = e;
        if ((R[pos(q, eps)] == empty_c) || R[pos(q, eps)].cost.second < q.cost.second) {
            R[pos(q, eps)] = q;
            for (int j = 0; j < num_nodes; j++) {
                map[j][des][pos(q, eps)] = map[j][src][i];
            }
            map[des][des][pos(q, eps)] = 1;
            nextActiveSet.insert(des); // Add destination to the next active set
        }
    }
    return R;
}

void SSMOSP(vector<vector<path>> &PI, vector<int> &nodes, vector<Edge> &edge_list, float epsilon, vector<vector<vector<int>>> &map) {
    PI[nodes[0]][0] = {make_pair(0, 0), NULL, NULL};
    map[nodes[0]][nodes[0]][0] = 1;

    unordered_set<int> activeSet; // Set of active nodes
    activeSet.insert(nodes[0]);

    vector<vector<path>> temp = PI;

    while (!activeSet.empty()) {
        unordered_set<int> nextActiveSet; // Nodes to process in the next iteration

        for (int node : activeSet) {
            for (const Edge &e : edge_list) {
                if (e.destination == node) {
                    Edge *edgePtr = const_cast<Edge *>(&e); // Get pointer to the current edge
                    PI[node] = Extend_Merge(nodes.size(), PI[node], temp[e.source], e.source, node, edgePtr, epsilon, map, nextActiveSet);
                }
            }
        }

        temp = PI;
        activeSet = nextActiveSet; // Update active set
    }
}

int longest_path(vector<path> P) {
    int min = INT_MAX;
    for (int i = 0; i < P.size(); i++) {
        if (P[i] == empty_c)
            continue;
        if (P[i].cost.first - P[i].cost.second < min)
            min = P[i].cost.first - P[i].cost.second;
    }
    if (min == INT_MAX)
        return INT_MIN;
    return -min;
}

void readCSV(string filename, vector<Edge> &edge_list, int &c1_max) {
    ifstream file(filename);
    string line, word;
    getline(file, line); 
    while (getline(file, line)) {
        stringstream ss(line);
        vector<int> row;
        while (getline(ss, word, ',')) {
            row.push_back(stoi(word));
        }
        int src = row[0], des = row[1], wt = row[2];
        if (wt < c1_max) c1_max = wt;
        Edge edge(src, des, wt);
        edge_list.push_back(edge);
    }
    file.close();
}

int main() {
    vector<Edge> edge_list;
    int v;
    cout << "Enter the number of nodes\n";
    cin >> v;
    cout << "Enter the source node which is between 0 to " << (v - 1) << "\n";
    vector<int> nodes(v);
    cin >> nodes[0];
    cout << "Enter the destination node which is between 0 to " << (v - 1) << "\n";
    cin >> nodes[v - 1];
    int val = 0;
    for (int i = 1; i < v - 1; i++) {
        if (val == nodes[0])
            val++;
        if (val == nodes[v - 1])
            val++;
        nodes[i] = val++;
    }

    cout << "Enter the filename for the CSV file containing edges:\n";
    string filename = "graph_data.csv";

    int c1_max = 0;
    readCSV(filename, edge_list, c1_max);

    cout << "Edge list size:" << edge_list.size() << "\n";

    float epsilon;
    cout << "Enter the value of error parameter\n";
    cin >> epsilon;
    c1_max *= -1;
    vector<vector<path>> PI;
    int size = (int)((float)(c1_max * v) / ((float)epsilon / (v - 1))) + 1;
    PI.resize(v, vector<path>(size, empty_c));
    vector<vector<vector<int>>> map(v, vector<vector<int>>(v, vector<int>(size, 0)));
    epsilon /= (v - 1);
    SSMOSP(PI, nodes, edge_list, epsilon, map);
    if (longest_path(PI[nodes[v - 1]]) == INT_MIN)
        cout << "No path from " << nodes[0] << " to " << nodes[v - 1] << endl;
    else
        cout << "Longest path from " << nodes[0] << " to " << nodes[v - 1] << " is " << longest_path(PI[nodes[v - 1]]) << endl;
    return 0;
}

