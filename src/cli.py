"""Command line options for the Pilon polishing

2023-05-23: Matthew Wells
"""

import argparse
import sys
import os
from Workflows import PolishAssembly, IdxMapReads, PolishWorkflow


class Main:
    """run main polising workflow
    """
    max_iter_default = 4
    default_ram = 4

    def __init__(self, args, **kwargs) -> None:
        self.args = args[1:]
        self.kwargs = kwargs
        self.out_args = self.cmd_parser(self.args)
        self.polish_assembly(self.out_args)

    def polish_assembly(self, params):
        """Run the polishing workflow
            TODO improve outdir usage
        """
        PolishWorkflow(contigs=params.contigs, reads=params.reads, out_dir=os.getcwd(), 
                        Polisher_=PolishAssembly, Mapper_=IdxMapReads, max_iter=params.max_iter, 
                        prefix=params.prefix, ram=params.ram)

    def cmd_parser(self, args):
        """Parse cmd line opts for polishing

        Args:
            args (_type_): _description_
        """
        parser = argparse.ArgumentParser(prog="PilonIterator", description="Iterative of polishing of an assembly using Illumina paired-end reads")
        parser.add_argument("-c", "--contigs", help="Path to assembled contigs", required=False)
        parser.add_argument("-r", "--reads", nargs='+', help="Paired end reads used for generation of the assembly",
                            required=False)
        parser.add_argument("-m", "--max-iter", help=f"Max number of iterations to perform with Pilon. Default: {self.max_iter_default}", type=int,
                            default=self.max_iter_default, required=False)
        parser.add_argument("-a", "--ram", help=f"Memory to be passed to Pilon JVM. Default: {self.default_ram}GB", required=False, type=int)
        parser.add_argument("-p", "--prefix", help="Prefix name to use for outputs", required=False, type=str)
        if not args:
            parser.print_help()
            sys.exit(1)
        return parser.parse_args(args)
        

def main(args = sys.argv):
    Main(args)

if __name__=="__main__":
    Main(sys.argv)
