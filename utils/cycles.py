import pickle
import networkx as nx
from amm import AMM
import os
from typing import List


def load_available_cycles(platform):
    with open(f'input_data/dynamic/{platform}/cycles.pkl', 'rb') as f:
        cycles = pickle.load(f)
    return cycles


def save_available_cycles(platform, amm: AMM, priorities: List[str]):
    G = nx.DiGraph()

    for p in amm.pools.values():

        G.add_edge(p.symbol_1, p.symbol_2)
        G.add_edge(p.symbol_2, p.symbol_1)

    cycles = list(nx.simple_cycles(G))

    filtered_cycles = []
    for cycle in cycles:
        cycle, from_asset = rotate_cycle(cycle, priorities=priorities)
        if from_asset in priorities:
            filtered_cycles.append(cycle)

    os.makedirs(f'input_data/dynamic/{platform}/', exist_ok=True)

    with open(f'input_data/dynamic/{platform}/cycles.pkl', 'wb') as f:
        pickle.dump(filtered_cycles, f)

    return filtered_cycles


def rotate_cycle(cycle: List[str], priorities):
    """ Rotate a cycle and it's corresponding list of pools so that
    the first asset is one of the list of priorities"""

    if not any([p in cycle for p in priorities]):
        return cycle, cycle[0]

    from_asset = None
    for priority in priorities:
        if priority in cycle:
            from_asset = priority
            break

    break_index = cycle.index(from_asset)

    cycle = cycle[break_index:] + cycle[:break_index]
    return cycle, from_asset
