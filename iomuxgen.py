#!/usr/bin/env python3


# open the csv contraint file: pinmap.csv

# read in all the IOs into a dict: ioconfig, keys = IO number (0-45) and value = dict of pad configuration

# iterate through the io_config dict, and set the appropriate reg values

# iterate through the io_config dict, and set the appropriate FBIO_SEL_1 and FBIO_SEL_2 reg values


import csv
import re
import pprint
from pathlib import Path
import argparse

pp = pprint.PrettyPrinter(indent=4)

# Default configuration of the IOMUX pad (default to FABRIC!)
PAD_DEFAULT = {
    "func_sel": 0,
    "ctrl_sel": 'fabric',
    "mode": "none",
    "pull": "none",
    "drive": 2,
    "slew": "slow",
    "schmitt": 0
}

# Base address of the FBIO_SEL registers
FBIOSEL_BASE = 0x40004D80

# Base address of the IOMUX registers
IOMUX_BASE = 0x40004C00

# CSV File Column Numbers
CSV_COL_NUM_IO_PAD_NUM = 0
CSV_COL_NUM_FUNC_SEL = 7
CSV_COL_NUM_CTRL_SEL = 6
CSV_COL_NUM_MODE = 1
CSV_COL_NUM_PULL = 2
CSV_COL_NUM_DRIVE = 3
CSV_COL_NUM_SLEW = 4
CSV_COL_NUM_SCHMITT = 5

def get_fabric_func_sel_for_io_pad(pad_num):

    # some of the pads need FUNC_SEL to be 1 to select as a FBIO_xx function
    if( (pad_num == 0) or 
        (pad_num == 1) or 
        (pad_num == 15) or 
        (pad_num == 17) or 
        (pad_num == 34) or 
        (pad_num == 38) or 
        (pad_num == 39) or 
        (pad_num == 43) or 
        (pad_num == 44) ):

        return 1
    # rest of the pads need FUNC_SEL to be 0 to select as a FBIO_xx function
    else:

        return 0

def generate_iomux_register_content(io_config):
    """
    Generates the content of IOMUX registers according to the given config.
    """
    iomux_regs = {}

    # Generate content of the IOMUX_PAD_O_CTRL register for each pad
    for pad, pad_cfg in io_config.items():
        pad = int(pad)
        reg = 0

        func_sel = pad_cfg["func_sel"]
        assert func_sel in [0, 1], func_sel
        reg |= func_sel

        ctrl_sel = pad_cfg["ctrl_sel"]
        assert ctrl_sel in ["A0", "others", "fabric"], ctrl_sel
        if ctrl_sel == "A0":
            reg |= (0 << 3)
        elif ctrl_sel == "others":
            reg |= (1 << 3)
        elif ctrl_sel == "fabric":
            reg |= (2 << 3)

        mode = pad_cfg["mode"]
        assert mode in ["none", "input", "output", "inout"], mode
        if mode == "none":
            oen = 0
            ren = 0
        elif mode == "input":
            oen = 0
            ren = 1
        elif mode == "output":
            oen = 1
            ren = 0
        elif mode == "inout":
            oen = 1
            ren = 1
        reg |= (oen << 5) | (ren << 11)

        pull = pad_cfg["pull"]
        assert pull in ["none", "up", "down", "keeper"], pull
        if pull == "none":
            reg |= (0 << 6)
        elif pull == "up":
            reg |= (1 << 6)
        elif pull == "down":
            reg |= (2 << 6)
        elif pull == "keeper":
            reg |= (3 << 6)

        drive = pad_cfg["drive"]
        assert drive in [2, 4, 8, 12], drive
        if drive == 2:
            reg |= (0 << 8)
        elif drive == 4:
            reg |= (1 << 8)
        elif drive == 8:
            reg |= (2 << 8)
        elif drive == 12:
            reg |= (3 << 8)

        slew = pad_cfg["slew"]
        assert slew in ["slow", "fast"], slew
        if slew == "slow":
            reg |= (0 << 10)
        elif slew == "fast":
            reg |= (1 << 10)

        schmitt = pad_cfg["schmitt"]
        assert schmitt in [0, 1], schmitt
        reg |= (schmitt << 12)

        # Register address
        adr = IOMUX_BASE + pad * 4

        # Store the value
        iomux_regs[adr] = reg

    # Generate content of FBIO_SEL_1 and FBIO_SEL_2
    fbio_sel = {0: 0, 1: 0}
    for pad in io_config.keys():
        r = int(pad) // 32
        b = int(pad) % 32
        fbio_sel[r] |= (1 << b)

    iomux_regs[FBIOSEL_BASE + 0x0] = fbio_sel[0]
    iomux_regs[FBIOSEL_BASE + 0x4] = fbio_sel[1]

    return iomux_regs


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="generates iomux binary using iomux csv configuration"
    )

    parser.add_argument(
        "--iomuxcsv",
        type=Path,
        help="IO Mux Configuration CSV File",
        required=True
    )

    parser.add_argument(
        "--iomuxbin",
        type=Path,
        help="output iomux binary file",
        required=True
    )

    args = parser.parse_args()

    # final io_config dict, with key = pad_number and value = pad_config dict
    io_config = {}

    with open(args.iomuxcsv) as iomux_csv_file:    
        
        row_count = 0

        for row in iomux_csv_file:

            # strip out the whitespace
            row = row.strip()

            #print(row)
            # ignore rows starting with #
            if str(row).startswith('#'):
                continue

            iomux_csv_row = row.split(',')

            # process the row list

            pad_num_match = re.match(r"^IO_([0-9]+)$", iomux_csv_row[0])

            if pad_num_match is None:
                print("ERROR: IO PAD Name in Unexpected format", iomux_csv_row[0])
                continue

            pad_num = int(pad_num_match.group(1))

            if pad_num is None or pad_num < 0 or pad_num >= 46:
                print("ERROR: Invalid pad number specified!", iomux_csv_row[0])

            # start with default pad configuration
            pad_config = PAD_DEFAULT.copy()

            # update fields as per csv row:
            # TODO sanitize csv? probably no need as iomux gen function does this
            print(iomux_csv_row)
            print(len(iomux_csv_row))
            if(len(iomux_csv_row) >= (CSV_COL_NUM_CTRL_SEL+1)):
                pad_config['ctrl_sel'] = str(iomux_csv_row[CSV_COL_NUM_CTRL_SEL]).lower()

            if(len(iomux_csv_row) >= (CSV_COL_NUM_FUNC_SEL+1)):
                pad_config['func_sel'] = int(str(iomux_csv_row[CSV_COL_NUM_FUNC_SEL]).lower())
            else:
                # choose func_sel according to CTRL_SEL (if FABRIC, FB_xx number)
                if(pad_config['ctrl_sel'] == 'fabric'):
                    pad_config['func_sel'] = get_fabric_func_sel_for_io_pad(pad_num)

            if(len(iomux_csv_row) >= (CSV_COL_NUM_MODE+1)):
                pad_config['mode'] = str(iomux_csv_row[CSV_COL_NUM_MODE]).lower()

            if(len(iomux_csv_row) >= (CSV_COL_NUM_PULL+1)):
                pad_config['pull'] = str(iomux_csv_row[CSV_COL_NUM_PULL]).lower()

            if(len(iomux_csv_row) >= (CSV_COL_NUM_DRIVE+1)):
                pad_config['drive'] = int(str(iomux_csv_row[CSV_COL_NUM_DRIVE]).lower())

            if(len(iomux_csv_row) >= (CSV_COL_NUM_SLEW+1)):
                pad_config['slew'] = str(iomux_csv_row[CSV_COL_NUM_SLEW]).lower()

            if(len(iomux_csv_row) >= (CSV_COL_NUM_SCHMITT+1)):
                pad_config['schmitt'] = int(str(iomux_csv_row[CSV_COL_NUM_SCHMITT]).lower())

            # add the pad_config to our dict
            io_config[str(pad_num)] = pad_config

            row_count += 1


    print('\nProcessed ' + str(row_count) + ' IO MUX Config Lines')
    #print(iomux_csv_row)

    print('\nFinal IOMUX Configuration Dict:\n')
    pp.pprint(io_config)

    # now use the io_config dictionary to set register values corresponding to each pad:
    iomux_regs = generate_iomux_register_content(io_config)

    # next create a bytearray (with Little Endian order) to represent the iomux binary blob
    # [4B ADDR][4B VAL] x number of registers

    iomux_bin_bytearray = bytearray()

    print('\nFinal IOMUX Register Values:\n')
    for addr in sorted(iomux_regs.keys()):

        print("0x{:08x} 0x{:08x}".format(addr, iomux_regs[addr]))

        # first the address
        addr_bytes = int(addr).to_bytes(4, byteorder='little')
        # store as bytes
        iomux_bin_bytearray.extend(addr_bytes)
        # second the value
        val_bytes = int(iomux_regs[addr]).to_bytes(4, byteorder='little')
        # store as bytes
        iomux_bin_bytearray.extend(val_bytes)


    with open(args.iomuxbin, 'wb') as iomuxbin:
            # write the header bytes
            iomuxbin.write(iomux_bin_bytearray)

    print("iomux bin:", args.iomuxbin, args.iomuxbin.stat().st_size, "bytes")