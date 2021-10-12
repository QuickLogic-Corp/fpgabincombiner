#!/usr/bin/env python3


# the memory initialization file contains a simple list of addr:val
# for each memory address that needs to be initialized covering all of
# memory blocks, for example:
# 0x40018000:0x000198dd     <-  memory block 1 start
# 0x40018004:0x000198dd
# ...
# 0x40018ff8:0x00000000
# 0x40018ffc:0x00000000     <-  memory block 1 end
# 0x4001b000:0x00002434     <-  memory block 2 start
# 0x4001b004:0x00002434
# ...
# 0x4001bff8:0x000156cd
# 0x4001bffc:0x000156cd     <-  memory block 2 end
# 0x4001a000:0x000154ff     <-  memory block 3 start
# 0x4001a004:0x000154ff
# ...
# 0x4001aff8:0x00002200
# 0x4001affc:0x00002200     <-  memory block 3 end
# 0x40019000:0x0001feff     <-  memory block 4 start
# 0x40019004:0x00000000
# ...
# 0x40019ff8:0x000000ff
# 0x40019ffc:0x000000ff     <-  memory block 4 end
#
# and so on... for any number of memory blocks.

# open the memory initialization file (conventionally "ram.mem")

# parse the addr:val values, and for each block:

# store the START_ADDR of the block, and the WORDCOUNT in the block
# store the VALUEs of the each WORD in the block in an array sequentially.

# repeat for each block available in the memory initialization file.

# final output of the meminit bin file would look like:
#<BLOCK_START_ADDR 4B><BLOCK_WORDCOUNT 4B><<MEM WORD 4B>xBLOCK_WORDCOUNT>
#<BLOCK_START_ADDR 4B><BLOCK_WORDCOUNT 4B><<MEM WORD 4B>xBLOCK_WORDCOUNT>
# ... for each block in the memory initialization file.


import csv
import re
import pprint
from pathlib import Path
import argparse

pp = pprint.PrettyPrinter(indent=4)

# each memory block as a a dict object
# containing start address, word count, and an array of the init values for each word.
# size of array of init values == word count
MEM_BLOCK_DEFAULT = {
    "start_addr": 0x00000000,
    "word_count": 0x00000000,
    "mem_words": []
}


def generate_meminit_content(memory_initialization_file_path):
    """
    Generates the content of memory blocks according to the given initialization file.
    """
    # create a meminit bytearray, in the same format as the header array.
    # <BLOCK_START_ADDR 4B><BLOCK_WORDCOUNT 4B><<MEM WORD 4B>xBLOCK_WORDCOUNT> x NUM_BLOCKS

    # create a list to hold all the mem_block dict objects
    mem_block_list = []

    # initialize the meminit binary byte array
    #mem_init_bin_bytearray = bytearray()

    line_parser = re.compile(r'(?P<addr>0x4001[89ab])[xX0-9a-f]+:(?P<data>[xX0-9a-f]+).*')

    # RAM initialization is always generated as ram.mem
    #ram_initialization_file_path = Path(args.infile.parent).joinpath("ram.mem")
    
    fp = open(memory_initialization_file_path, 'r')
    
    file_data = fp.readlines()

    wordcount = 0
    prev_addr = None
    curr_addr = ""
    current_block_start_addr = ""
    current_block_memory_words = bytearray()

    for line in file_data:
        linematch = line_parser.match(line)

        if linematch:
            curr_addr = linematch.group('addr')
            curr_data = linematch.group('data')
            #print(curr_addr, curr_data)
        else:
            continue

        # the regex pattern ensures that when we move from one block to the next,
        # the curr_addr will change, as we consider only the block level component of addr:
        # 0x4001X -> 0x4001Y is a block transition
        # for each block, we will have the same addr 0x4001X in each consecutive line.
        # each block always starts at 0x4001X000
        # so, we will have block_start_addr (0x4001X000), followed by number of words of memory (4B)
        # and then followed by the actual memory words that will be written in order, starting from
        # the block_start_addr

        if prev_addr == None:
            # we are going to start the first block
            # initialize the mem_block dict content for the new block
            curr_mem_block = MEM_BLOCK_DEFAULT.copy()
            curr_mem_block["mem_words"] = []

            prev_addr = curr_addr
            # reset memory wordcount
            wordcount = 0
            # set the block start addr
            current_block_start_addr = prev_addr + "000"
            # init the memory block byte array
            #current_block_memory_words = bytearray()

        if prev_addr != curr_addr:
            # we are going to start a new block
            # save the block_start_address, memory wordcount, followed by the current block memory words
            #print("current_block_start_addr", current_block_start_addr)
            #print("wordcount", wordcount)

            curr_mem_block["start_addr"] = int(current_block_start_addr, 16)
            curr_mem_block["word_count"] = (int(wordcount))

            # add the current mem block to the list of mem blocks
            mem_block_list.append(curr_mem_block)

            #mem_init_bin_bytearray.extend(int(current_block_start_addr, 16).to_bytes(4, "little"))
            #mem_init_bin_bytearray.extend(int(wordcount).to_bytes(4, "little"))
            #mem_init_bin_bytearray.extend(current_block_memory_words)
            
            # initialize the mem_block dict content for the new block
            curr_mem_block = MEM_BLOCK_DEFAULT.copy()
            curr_mem_block["mem_words"] = []

            # update the block addr to new one:
            prev_addr = curr_addr
            # reset memory wordcount
            wordcount = 0
            # set the block start addr
            current_block_start_addr = prev_addr + "000"
            # init the memory block byte array
            #current_block_memory_words = bytearray()

        # add the integer data into the memory block bytearray as 4 LE bytes
        curr_mem_block["mem_words"].append(int(curr_data, 16))
        #current_block_memory_words.extend(int(curr_data, 16).to_bytes(4, "little"))

        # increment memory wordcount for current block
        wordcount += 1

    # at the end of the loop, the last memory block remains to be saved:
    if (wordcount != 0):
        #print("current_block_start_addr", current_block_start_addr)
        #print("wordcount", wordcount)
        #mem_init_bin_bytearray.extend(int(current_block_start_addr, 16).to_bytes(4, "little"))
        #mem_init_bin_bytearray.extend(int(wordcount).to_bytes(4, "little"))
        #mem_init_bin_bytearray.extend(current_block_memory_words)

        curr_mem_block["start_addr"] = int(current_block_start_addr, 16)
        curr_mem_block["word_count"] = (int(wordcount))

        # add the current mem block to the list of mem blocks
        mem_block_list.append(curr_mem_block)
 
    #meminit_size = len(mem_init_bin_bytearray)
    # 1024 words x 4B x 4 blocks + 2 words x 4B x 4 blocks (1024 -> mem, 2 -> addr,count)
    #expected_meminit_size = (1024 * 4 * 4) + (2 * 4 * 4)
    #print(meminit_size, expected_meminit_size)

    return mem_block_list



if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="generates meminit binary using memory initialization file"
    )

    parser.add_argument(
        "--meminitfile",
        type=Path,
        help="Memory Initialization File (\"ram.mem typically\")",
        required=True
    )

    parser.add_argument(
        "--meminitbin",
        type=Path,
        help="output meminit binary file",
        required=True
    )

    args = parser.parse_args()

    # now use the io_config dictionary to set register values corresponding to each pad:
    mem_block_list = generate_meminit_content(args.meminitfile)

    # next create a bytearray (with Little Endian order) to represent the meminit binary blob    

    meminit_bin_bytearray = bytearray()

    block_num = 0
    for block in mem_block_list:

        print("-------------------------------------------------------------------------")
        print("block_num:",block_num)
        print("")
        print("[START] 0x{:08x}".format(block["start_addr"]))
        print("[WORDS] 0x{:08x}".format(block["word_count"]))
        print("FIRST 2 WORD Values: 0x{:08x} 0x{:08x}".format(block["mem_words"][0], block["mem_words"][1]))
        print(" LAST 2 WORD Values: 0x{:08x} 0x{:08x}".format(block["mem_words"][-1], block["mem_words"][-2]))
        print("-------------------------------------------------------------------------")
        print("")


        meminit_bin_bytearray.extend(block["start_addr"].to_bytes(4, "little"))
        meminit_bin_bytearray.extend(block["word_count"].to_bytes(4, "little"))
        for word in block["mem_words"]:
            meminit_bin_bytearray.extend(word.to_bytes(4, "little"))

        block_num += 1


    with open(args.meminitbin, 'wb') as meminitbin:
            # write the header bytes
            meminitbin.write(meminit_bin_bytearray)

    print("meminit bin:", args.meminitbin, args.meminitbin.stat().st_size, "bytes")