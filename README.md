# fpgabincombiner
Utility toolset to generate iomux bin and combine bitstream/meminit/iomux bins into fpgabin for EOSS3

## Usage

1. Prepare the IO Configuration CSV file:
   - Each row contains a configuration for an IO
   - If the line begins with a '#' it is ignored, can be used for adding comments
   - The order of the configuration columns is as below:

     (0)IO_NUM,(1)MODE,(2)PULL,(3)DRIVE,(4)SLEW,(5)SCHMITT,(6)CTRL_SEL,(7)FUNC_SEL
   - Other than Column 0 (IO_NUM), all others are optional, and will take default values if unspecified

2. Generate the MEMINIT binary from the memory initialization (ram.mem) file [if applicable]:

   `python3 ./meminitgen.py --meminitfile=/path/to/ram.mem --meminitbin=/path/to/write/meminit/binary`

3. Generate the IOMUX binary from the IO Configuration CSV file:

   `python3 ./iomuxgen.py --iomuxcsv=/path/to/io/configuration/csv --iomuxbin=/path/to/write/iomux/binary`

4. Generate the combined FPGA binary :

    [A] With only the BITSTREAM and IOMUX binary (no MEMINIT section):

   `python3 ./fpgabincombiner.py --bitstream=/path/to/bitstream --iomuxbin=/path/to/generated/iomux/binary --fpgabin=/path/to/write/fpga/binary`

   [B] With BITSTREAM, MEMINIT and IOMUX binary:

   `python3 ./fpgabincombiner.py --bitstream=/path/to/bitstream --meminitbin=path/to/generated/meminit/binary --iomuxbin=/path/to/generated/iomux/binary --fpgabin=/path/to/write/fpga/binary`

The generated FPGA binary file contains the necessary `HEADER + BITSTREAM + (MEMINIT) + IOMUX` structure that the QORC Bootloader can understand, and execute on the EOSS3.

## Using The Example (BREATHE FPGA DESIGN)

The `example_breathe` directory contains the necessary files (and generated bins are also present, they will be overwritten as needed).

The `iomux.csv` contains IO configuration spec as well as some example declarations.

The original fpga bin generated using the Symbiflow toolchain is `AL4S3B_FPGA_Top_BREATHE_REFERENCE.bin` for comparison.
This includes the header, and iomux binary needed for the bootloader to recognize it correctly, meminit is zero size in this example.

1. Generate the iomux binary from the iomux csv file using:

   `python3 ./iomuxgen.py --iomuxcsv=./example_breathe/iomux.csv --iomuxbin=./example_breathe/iomux.bin `

   This generates iomux.bin in the `example_breathe` directory

2. Generate a combined bin using the bitstream (example_breathe/AL4S3B_FPGA_Top_BREATHE.bit) and the generated iomux binary(example_breathe/iomux.bin)

   `python3 ./fpgabincombiner.py --bitstream=./example_breathe/AL4S3B_FPGA_Top_BREATHE.bit --iomuxbin=./example_breathe/iomux.bin --fpgabin=./example_breathe/breathefpga.bin`

   This generates breathefpga.bin in the `example_breathe` directory.

   This can be compared with original fpga bin generated from the Symbiflow toolchain, they should match as the same bitstream, iomux is used.


## Using The Example (MEMINIT TEST FPGA DESIGN)

The `example_meminit` directory contains the necessary files.

`reference_outputs` contains the build files generated when the fpga design is built with the qorc-sdk Symbiflow toolchain (v1.3.1).

If you want to build the fpga design yourself, use the qorc-sdk fpga toolchain (setup using `envsetup.sh` as usual) and then, from the root of the repo:

`ql_symbiflow -compile -src example_meminit/fpga/rtl -d ql-eos-s3 -t top -v AL4S3B_FPGA_IP.v AL4S3B_FPGA_QL_Reserved.v AL4S3B_FPGA_RAMs.v AL4S3B_FPGA_Registers.v AL4S3B_FPGA_Top.v r1024x16_1024x16.v r1024x8_1024x8.v r2048x8_2048x8.v r512x16_512x16.v r512x32_512x32.v  -p quickfeather.pcf -P PU64 -dump binary`

This will generate iomuxbin, meminitbin, ram.mem in the `fpga/rtl/build` directory, and top.bin in the `fpga/rtl` directory (combined fpga binary)


1. Prepare the IO Configuration CSV file:
   
   This is already done, the example_meminit/iomux.csv file is derived from pcf file at example_meminit/fpga/rtl/chandalar.pcf

   It would be good to verify that this is correct.

2. Generate the MEMINIT binary from the memory initialization (ram.mem) file:

   `python3 ./meminitgen.py --meminitfile=example_meminit/reference_outputs/build/ram.mem --meminitbin=example_meminit/meminit.bin`

3. Generate the IOMUX binary from the IO Configuration CSV file:

   `python3 ./iomuxgen.py --iomuxcsv=example_meminit/iomux.csv --iomuxbin=example_meminit/iomux.bin`

4. Generate the combined FPGA binary :

    BITSTREAM is taken from the reference build here, can be substituted with custom built one if needed.

   With BITSTREAM, MEMINIT and IOMUX binary
   `python3 ./fpgabincombiner.py --bitstream=example_meminit/reference_outputs/build/top.bit --iomuxbin=example_meminit/iomux.bin --meminitbin=example_meminit/meminit.bin --fpgabin=example_meminit/meminitfpga.bin`


## NOTES

1. csv format is flexible, and defaults are mentioned in the example_breathe/iomux.csv, as well as various forms of declaring the IOs
2. all of the IO options are supported, and the register values should be seen changing according to them (drive, pull etc.)
3. `example_meminit` will not compile with latest Symbiflow package. 
   
   It is only compatible with the qorc-sdk Symbiflow (tested at v1.3.1)
4. `example_meminit_latest` cannot be used yet.

   It can compile with latest Symbiflow package (dailybuild), however it does not currently compile because it has some problems with the pin constraints. 
