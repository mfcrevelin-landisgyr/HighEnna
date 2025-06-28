import re
import string
import random
from collections import defaultdict
from graphviz import Digraph


SPECIAL_GROUPS = {
    '\\\\w': set(ord(c) for c in string.ascii_lowercase),
    '\\\\W': set(ord(c) for c in string.ascii_uppercase),
    '\\\\d': set(ord(c) for c in string.digits),
    '\\\\s': {ord(' '), ord('\t')},
    '\\\\n': {ord('\n')},
}

def get_state_name(state):
    return f"{state:02x}".upper()

def is_printable(c):
    return 32 <= c <= 126

def format_byte(b):
    return f'"{chr(b)}"' if is_printable(b) else f'0x{b:02X}'

def format_range(start, end):
    start_str = format_byte(start)
    end_str = format_byte(end)
    return f'[{start_str},{end_str}]' if start != end else start_str

def extract_ranges(sorted_bytes):
    ranges = []
    i = 0
    while i < len(sorted_bytes):
        start = sorted_bytes[i]
        end = start
        while i + 1 < len(sorted_bytes) and sorted_bytes[i + 1] == end + 1:
            end += 1
            i += 1
        ranges.append((start, end))
        i += 1
    return ranges

def label_bytes(byte_set):
    remaining = set(byte_set)
    labels = []

    for label, group in SPECIAL_GROUPS.items():
        if group.issubset(remaining):
            labels.append(label)
            remaining -= group

    if remaining:
        sorted_bytes = sorted(remaining)
        for start, end in extract_ranges(sorted_bytes):
            labels.append(format_range(start, end))

    return labels

def label_bytes(byte_set):
    byte_set = set(byte_set)
    if byte_set == set(range(256)):
        return ['*']

    sorted_bytes = sorted(byte_set)
    range_tuples = extract_ranges(sorted_bytes)
    range_sets = [set(range(start, end + 1)) for start, end in range_tuples]
    range_labels = [format_range(start, end) for start, end in range_tuples]

    special_labels = []
    for label, group in SPECIAL_GROUPS.items():
        if group <= byte_set:
            special_labels.append((label, group))

    final_labels = []

    consumed_ranges = [False] * len(range_sets)
    for label, group in special_labels:
        keep_special = True
        for i, rset in enumerate(range_sets):
            if group < rset:
                # Rule 2: special label is subset of range → discard special label
                keep_special = False
                break
            elif rset < group:
                # Rule 3: range is subset of special label → discard range
                consumed_ranges[i] = True
            elif group == rset:
                # Rule 4: equal → prefer special label
                consumed_ranges[i] = True
        if keep_special:
            final_labels.append(label)

    # Add remaining (unused) range labels
    for consumed, label in zip(consumed_ranges, range_labels):
        if not consumed:
            final_labels.append(label)

    return final_labels

def parse_dfa(cpp_code: str):
    cpp_code = re.sub(r'//.*?\n', '', cpp_code)
    cpp_code = re.sub(r'\s+', '', cpp_code)
    pattern = r'\{((?:\d+,?)+)\}'
    rows = re.findall(pattern, cpp_code)

    dfa = []
    for row in rows:
        values = list(map(int, row.strip(',').split(',')))
        if len(values) != 256:
            raise ValueError(f"Expected 256 entries per state, got {len(values)}")
        dfa.append(values)
    return dfa

def make_labelled_edges(dfa):
    num_states = len(dfa)
    transitions_per_state = defaultdict(lambda: defaultdict(set))

    for state in range(num_states):
        for byte in range(256):
            dst = dfa[state][byte]
            transitions_per_state[state][dst].add(byte)

    edges = []
    for state, targets in transitions_per_state.items():
        labeled = []
        for dst, bytes_set in targets.items():
            labels = label_bytes(bytes_set)
            labeled.append((dst, labels, len(bytes_set)))

        if labeled:
            if len(labeled)>1:
                # Sort by number of bytes to determine which gets the '*'
                labeled.sort(key=lambda x: -x[2])

                dst, _, _ = labeled[0]
                labeled = labeled[1:]
                edges.append((state, dst, '*'))

            for dst, labels, _ in labeled:
                edges.append((state, dst, ','.join(labels)))

    return edges

def random_pastel_color():
    r = lambda: random.randint(100, 200)
    return f"#{r():02x}{r():02x}{r():02x}"

def draw_dfa(edges, num_states, filename='dfa_graph'):
    dot = Digraph(format='jpg')
    dot.attr(rankdir='LR')
    dot.graph_attr.update({ 'dpi': "400" })

    # Add states
    for state in range(num_states):
        dot.node(get_state_name(state), shape='circle')

    # Group edges by (src, dst)
    label_map = defaultdict(list)
    for src, dst, label in edges:
        label_map[(src, dst)].append(label)

    for (src, dst), labels in label_map.items():
        dot.edge(
            get_state_name(src),
            get_state_name(dst),
            label='\n'.join(labels),
            color=random_pastel_color(),
            fontcolor='red',
            labelfloat='true',
            minlen='5'
        )

    output_path = dot.render(f"output/{filename}", cleanup=True)
    print(f'DFA diagram saved to {output_path}')

def plot_dfa(cpp_code, filename):
    dfa = parse_dfa(cpp_code)
    edges = make_labelled_edges(dfa)
    draw_dfa(edges, len(dfa), filename)
