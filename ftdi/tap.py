#!/usr/bin/env python2.6
# Christian Unhold, DICE GmbH & Co KG
"""
JTAG Test Access Port (TAP) state graph and utilities.
"""

STATES = {
    "RESET" : ("IDLE", "RESET"),
    "IDLE" : ("IDLE", "DRSELECT"),
    "DRSELECT" : ("DRCAPTURE", "IRSELECT"),
    "DRCAPTURE" : ("DRSHIFT", "DREXIT1"),
    "DRSHIFT" : ("DRSHIFT", "DREXIT1"),
    "DREXIT1" : ("DRPAUSE", "DRUPDATE"),
    "DRPAUSE" : ("DRPAUSE", "DREXIT2"),
    "DREXIT2" : ("DRSHIFT", "DRUPDATE"),
    "DRUPDATE" : ("IDLE", "DRSELECT"),
    "IRSELECT" : ("IRCAPTURE", "RESET"),
    "IRCAPTURE" : ("IRSHIFT", "IREXIT1"),
    "IRSHIFT" : ("IRSHIFT", "IREXIT1"),
    "IREXIT1" : ("IRPAUSE", "IRUPDATE"),
    "IRPAUSE" : ("IRPAUSE", "IREXIT2"),
    "IREXIT2" : ("IRSHIFT", "IRUPDATE"),
    "IRUPDATE" : ("IDLE", "DRSELECT"),
}

STABLE_STATES = ("IRPAUSE", "DRPAUSE", "RESET", "IDLE",)

"""
Write a graph to a file in the Graphviz (dot) text language.
"""
def write_dot(graph, file):
    file.write("digraph G {\n")
    for node in graph:
        for i in range(len(graph[node])):
            file.write("\t" + node + " -> " + graph[node][i] + " [label = %d] ;\n" % (i,))
    file.write("}\n")

def find_all_paths(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return [path]
    paths = []
    for node in graph[start]:
        if node not in path:
            newpaths = find_all_paths(graph, node, end, path)
            for newpath in newpaths:
                paths.append(newpath)
    return paths

def find_shortest_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest

def find_shortest_path_and_edges(graph, start, end, path=[], edges=[]):
    path = path + [start]
    if start == end:
        return path, edges
    shortest, shedges = None, None
    for edge in range(len(graph[start])):
        node = graph[start][edge]
        if node not in path:
            newpath, newedges = find_shortest_path_and_edges(graph, node, end, path, edges+[edge])
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest, shedges = newpath, newedges
    return shortest, shedges

def find_shortest_edges(graph, start, end):
    path, edges = find_shortest_path_and_edges(graph, start, end)
    return edges

def test():
    with open("tap.dot", "w") as file: write_dot(STATES, file)
    import os
    for format in ("png", "eps", "pdf"):
        os.system("dot -T %s tap.dot -o tap.%s" % (format, format,))
    find_all_paths(STATES, "IDLE", "IREXIT2")
    find_shortest_path(STATES, "IDLE", "IRUPDATE")
    find_shortest_edges(STATES, "RESET", "SHIFTIR")
    for start in STABLE_STATES:
        for end in STABLE_STATES:
            print("%s -> %s:"%(start, end,))
            path, edges = find_shortest_path_and_edges(STATES, start, end)
            assert len(path) == len(edges) + 1
            print("\t"+", ".join(path))
            print("\t"+", ".join([str(edge) for edge in edges]))

if __name__ == "__main__":
    test()