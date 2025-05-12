from plot_dfa import *
import argparse
import sys
import os

def build_file_dfa(output_name):
    os.makedirs("output",exist_ok=True)

    dfa = [[0] * 256 for _ in range(18)]

    other = range(256)
    d = list(map(ord,['1','2','3','4','5','6','7','8','9','0']))
    w = list(map(ord,['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']))
    W = list(map(ord,['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']))
    s = list(map(ord,[' ','\t']))
    n = list(map(ord,['\n']))
    m = list(map(ord,['$']))
    _ = list(map(ord,['_']))
    z = [0]

    for c in other:
        dfa[0x00][c] = 0x00
        dfa[0x01][c] = 0x00
        dfa[0x02][c] = 0x00

        dfa[0x03][c] = 0x06
        dfa[0x04][c] = 0x06
        dfa[0x05][c] = 0x06
        dfa[0x06][c] = 0x06
        dfa[0x07][c] = 0x06
        dfa[0x08][c] = 0x06
        dfa[0x09][c] = 0x06
        dfa[0x0A][c] = 0x06
        dfa[0x0B][c] = 0x11 #
        dfa[0x0C][c] = 0x06
        dfa[0x0D][c] = 0x06

        dfa[0x0E][c] = 0x0E
        dfa[0x0F][c] = 0x0F
        dfa[0x10][c] = 0x10
        dfa[0x11][c] = 0x11

    for c in z:
        dfa[0x00][c] = 0x0F
        dfa[0x01][c] = 0x0F
        dfa[0x02][c] = 0x0F

        dfa[0x03][c] = 0x0F
        dfa[0x04][c] = 0x0F
        dfa[0x05][c] = 0x0F
        dfa[0x06][c] = 0x0F
        dfa[0x07][c] = 0x0F
        dfa[0x08][c] = 0x0F
        dfa[0x09][c] = 0x0F
        dfa[0x0A][c] = 0x0F
        dfa[0x0B][c] = 0x0F
        dfa[0x0C][c] = 0x0F
        dfa[0x0D][c] = 0x0F

        dfa[0x0E][c] = 0x0F
        dfa[0x0F][c] = 0x0F
        dfa[0x10][c] = 0x0F
        dfa[0x11][c] = 0x0F

    for c in n:
        dfa[0x00][c] = 0x01
        dfa[0x01][c] = 0x01
        dfa[0x02][c] = 0x01

        dfa[0x03][c] = 0x05
        dfa[0x04][c] = 0x05
        dfa[0x05][c] = 0x05
        dfa[0x06][c] = 0x05
        dfa[0x07][c] = 0x05
        dfa[0x08][c] = 0x05
        dfa[0x09][c] = 0x05
        dfa[0x0A][c] = 0x05
        dfa[0x0B][c] = 0x10 #
        dfa[0x0C][c] = 0x05
        dfa[0x0D][c] = 0x05

    for c in m:
        dfa[0x00][c] = 0x02
        dfa[0x01][c] = 0x02
        dfa[0x02][c] = 0x03
        dfa[0x03][c] = 0x0D
        dfa[0x04][c] = 0x0D
        dfa[0x05][c] = 0x0D
        dfa[0x06][c] = 0x0D
        dfa[0x07][c] = 0x0D
        dfa[0x08][c] = 0x0D
        dfa[0x09][c] = 0x0D
        dfa[0x0A][c] = 0x0D
        dfa[0x0C][c] = 0x0D
        dfa[0x0D][c] = 0x00

    for c in s:
        dfa[0x03][c] = 0x04
        dfa[0x04][c] = 0x04

    for c in w+W:
        dfa[0x0B][c] = 0x0C
        dfa[0x0C][c] = 0x0C

    for c in d:
        dfa[0x0C][c] = 0x0C

    for c in _:
        dfa[0x09][c] = 0x0B
        dfa[0x0A][c] = 0x0B
        dfa[0x0C][c] = 0x0C

    for c in [ord('#')]:
        dfa[0x03][c] = 0x0E
        dfa[0x0D][c] = 0x11

    for c in [ord('v')]:
        dfa[0x03][c] = 0x07
        dfa[0x04][c] = 0x07
        dfa[0x05][c] = 0x07
        dfa[0x06][c] = 0x07

    for c in [ord('a')]:
        dfa[0x07][c] = 0x08

    for c in [ord('l')]:
        dfa[0x08][c] = 0x09

    for c in [ord('r')]:
        dfa[0x08][c] = 0x0A


    max_width = max(len(str(item)) for row in dfa for item in row)

    formatted_rows = []
    for row in dfa:
        formatted_row = ','.join(f"{item:>{max_width}}" for item in row)
        formatted_rows.append(f"\t{{{formatted_row}}}")

    num_rows = len(dfa)
    result = f"static constexpr uint8_t name_rgx[{num_rows}][256] = {{\n"
    result += ",\n".join(formatted_rows)
    result += "\n};"

    with open(f"output/{output_name}.h",'w') as f:
        f.write(result)
    plot_dfa(result, output_name)

def build_name_dfa(output_name):
    os.makedirs("output",exist_ok=True)

    dfa = [[0] * 256 for _ in range(6)]

    for c in range(256):
        dfa[0][c] = 0
        dfa[1][c] = 0
        dfa[2][c] = 0
        dfa[3][c] = 5
        dfa[4][c] = 5
        dfa[5][c] = 5

    for c in map(ord,['.']):
        dfa[1][c] = 2
        dfa[3][c] = 4

    for c in map(ord,['1','2','3','4','5','6','7','8','9','0']):
        dfa[0][c] = 1
        dfa[1][c] = 1
        dfa[2][c] = 3
        dfa[3][c] = 3
        dfa[4][c] = 3


    max_width = max(len(str(item)) for row in dfa for item in row)

    formatted_rows = []
    for row in dfa:
        formatted_row = ','.join(f"{item:>{max_width}}" for item in row)
        formatted_rows.append(f"\t{{{formatted_row}}}")

    num_rows = len(dfa)
    result = f"static constexpr uint8_t name_rgx[{num_rows}][256] = {{\n"
    result += ",\n".join(formatted_rows)
    result += "\n};"

    with open(f"output/{output_name}.h",'w') as f:
        f.write(result)
    plot_dfa(result, output_name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('string', nargs='?')

    args = parser.parse_args()

    if args.string is not None:
        if args.string == "name":
            build_name_dfa("name_dfa")
        elif args.string == "file":
            build_file_dfa("file_dfa")
    else:
        build_name_dfa("name_dfa")
        build_file_dfa("file_dfa")

if __name__=="__main__":
    main()