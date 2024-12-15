from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import uuid

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Create a static folder to store generated images
if not os.path.exists('static'):
    os.makedirs('static')

# Prim's algorithm function
def primlist(WList, x):
    # Initialization
    infinity = 1 + max([d for u in WList.keys() for (v, d) in WList[u]])
    (visited, distance, TreeEdges) = ({}, {}, [])
    for v in WList.keys():
        (visited[v], distance[v]) = (False, infinity)

    # Start from the starting node x
    visited[x] = True
    for (v, d) in WList[x]:
        distance[v] = d

    # Build MST
    for i in range(1, len(WList.keys())):
        mindist = infinity
        nextv = None
        # Find the minimum weight edge (u,v)
        for u in WList.keys():
            for (v, d) in WList[u]:
                if visited[u] and (not visited[v]) and d < mindist:
                    mindist = d
                    nextv = v
                    nexte = (u, v)

        # Mark nextv as visited and add edge to MST
        visited[nextv] = True
        TreeEdges.append(nexte)

        # Update the distance of unvisited neighbors
        for (v, d) in WList[nextv]:
            if not visited[v]:
                if d < distance[v]:
                    distance[v] = d
    return TreeEdges

@app.route('/generate', methods=['POST'])
def generate_graph():
    try:
        # Read JSON data from the request
        data = request.json

        # Parse the input data
        dedges = [(item[0], item[1], int(item[2])) for item in data]

        # Build adjacency list for Prim's algorithm
        WL = {}
        x = "Null"
        for (i, j, w) in dedges:
            if i not in WL.keys():
                WL[i] = []
                if x == "Null":
                    x = i
            if j not in WL.keys():
                WL[j] = []
            WL[i].append((j, w))

        # Create a NetworkX graph
        G = nx.Graph()
        for i in dedges:
            G.add_edge(i[0], i[1], weight=i[2])

        elarge = [(u, v) for (u, v, d) in G.edges(data=True) if (u, v) not in primlist(WL, x)]
        esmall = [(u, v) for (u, v, d) in G.edges(data=True) if (u, v) in primlist(WL, x)]

        pos = nx.spring_layout(G, seed=7)  # positions for all nodes

        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=700)

        # Draw edges
        nx.draw_networkx_edges(G, pos, edgelist=elarge, width=6)
        nx.draw_networkx_edges(
            G, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
        )

        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=20, font_family="sans-serif")

        # Draw edge weight labels
        edge_labels = nx.get_edge_attributes(G, "weight")
        nx.draw_networkx_edge_labels(G, pos, edge_labels)

        # Save the output graph as an image with a unique filename
        unique_filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join('static', unique_filename)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.clf()  # Clear the plot for future requests

        # Return the image URL in the response
        return jsonify({"success": True, "image_url": f"/static/{unique_filename}"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/static/<filename>')
def get_output_image(filename):
    # Serve the generated image
    return send_file(os.path.join('static', filename), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)