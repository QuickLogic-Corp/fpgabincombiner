# fpgabincombiner
Utility toolset to generate iomux bin and combine bitstream/meminit/iomux bins into fpgabin for EOSS3

## Usage

1. Prepare the IO Configuration CSV file:
   - Each row contains a configuration for an IO
   - If the line begins with a '#' it is ignored, can be used for adding comments
   - The order of the configuration columns is as below:

     (0)IO_NUM,(1)MODE,(2)PULL,(3)DRIVE,(4)SLEW,(5)SCHMITT,(6)CTRL_SEL,(7)FUNC_SEL
   - Other than Column 0 (IO_NUM), all others are optional, and will take default values if unspecified

2. Generate the IOMUX binary from the IO Configuration CSV file:

   `python3 ./iomuxgen.py --iomuxcsv=/path/to/io/configuration/csv --iomuxbin=/path/to/write/iomux/binary`

3. Generate the combined FPGA binary from the BITSTREAM and IOMUX binary:

   `python3 ./fpgabincombiner.py --bitstream=/path/to/bitstream --iomuxbin=/path/to/generated/iomux/binary --fpgabin=/path/to/write/fpga/binary`

The generated FPGA binary file contains the necessary `HEADER + BITSTREAM + IOMUX` structure that the QORC Bootloader can understand, and execute on the EOSS3.

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

## NOTES

1. meminit generation section is commented out in code, can be revived if needed.
2. csv format is flexible, and defaults are mentioned in the example_breathe/iomux.csv, as well as various forms of declaring the IOs
3. all of the IO options are supported, and the register values should be seen changing according to them (drive, pull etc.)
