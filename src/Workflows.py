"""Create basic workflows for common proceses

Matthew Wells: 2023-05-18
"""
import os
import sys
import copy
from typing import List, Union
from tools import Executor, Minimap2Settings, FlyeInputs, Minimap2, Pilon, Samtools


class Polisher:
    """Base class to call for polishing of reads

    Returns:
        _type_: _description_
    """
    def __init__(self) -> None:
        pass

class Mapper:
    """Base class for read mapping classes

    Returns:
        _type_: _description_
    """
    def __init__(self) -> None:
        pass


class AssembleLongReads:
    """Assemble long read data using flye
    TODO determine if tempdirs need to be made for different steps to aid in caching results
    TODO Try and generalize the path binding operations to the Program class
    """

    def __init__(self, long_reads: List[str], output_dir: str):
        self.long_reads = [os.path.abspath(i) for i in long_reads]
        self.output_dir = os.path.abspath(output_dir)
        self.bind_mounts = self.create_bind_paths()

    def create_bind_paths(self):
        """Create paths of directories to bind for the singularity image
        """
        absp_in_files = [os.path.dirname(i) for i in self.long_reads]
        absp_in_files.append(self.output_dir)
        return ",".join(absp_in_files)

    def run_flye(self):
        """Run flye on long read data
        """

        flye = Executor("Flye", bind_mounts=self.bind_mounts, mode=FlyeInputs.nano_hq, input_files=self.long_reads, out_dir=self.output_dir)
        #if not os.path.isdir(self.output_dir):
        #    print(f"Creating output directory for flye: {self.output_dir}", flush=True)
        #    os.mkdir(self.output_dir)
        flye.execute()


class IdxMapReads(Mapper):
    """Index assemblies, and map reads to them
        TODO Racon need overlaps of reads, so an the ava-ont option mat be able to be run
        TODO follow up on when to use ava, I dont think it is needed here
    """


    def __init__(self, contigs: str, reads: List[str], output_name, mapping_setting: Minimap2Settings = Minimap2Settings.map_ont) -> None:
        self.contigs = os.path.abspath(contigs)
        self.reads = [os.path.abspath(i) for i in reads]
        self.output_name = output_name
        self.mapping_setting = mapping_setting
        self.bind_paths = [os.path.dirname(i) for i in self.reads]
        self.bind_paths.append(os.path.dirname(self.contigs))   
        self.bind_paths.append(os.getcwd())   
        self.bind_mounts = ",".join(set(self.bind_paths))

    def alignment_dance(self):
        """index contigs, and map reads to the alignment

        TODO index is not needed when running minimap2 unless performance is a major concern
        """
        self.index_reads()
        self.map_reads()
    
    def index_reads(self):
        """Create an index for a new assembly
        """
        mm2_index = Executor("Minimap2", bind_mounts=self.bind_mounts, 
                            setting=Minimap2Settings.create_index, output_name=self.output_name, contigs=self.contigs)
        mm2_index.execute()
    
    def map_reads(self):
        """Map reads to an assembly
        """
        mm2_map = Executor(prog="Minimap2", bind_mounts=self.bind_mounts, setting=Minimap2Settings.map_ont, 
                        reads=self.reads, output_name=self.output_name, contigs=self.contigs)
        mm2_map.execute()

class ContigConsensus:
    """Run Racon on created assemblies

    TODO implement racon later, currently I dont want to deal with the reads as duplicates issue till later
    """

    def __init__(self, contigs: str, sam_file: str, reads: List[str], output_name: str) -> None:
        self.contigs = contigs
        self.sam_file = sam_file
        self.reads = reads
        self.output_name = output_name
    

class PolishAssembly(Polisher):
    """Polish an assemblies with short read data using Pilon
    """

    def __init__(self, contigs: str, bam: str, output_prefix: str, out_dir: str, ram: int, **kwargs):
        self.contigs = os.path.abspath(contigs)
        self.bam = os.path.abspath(bam)
        self.output_prefix = output_prefix
        self.ram = ram
        self.out_dir = os.path.abspath(out_dir)
        if not os.path.isdir(self.out_dir):
            os.mkdir(self.out_dir)
        self.kwargs = kwargs

    def create_bind_mounts(self):
        """Create paths for bind mounts
        """
        return ",".join(set([os.path.dirname(self.bam), os.path.dirname(self.contigs), self.out_dir]))

    def polish_assembly(self):
        """Run pilon on the assembly
        """
        pilon_exc = Executor(prog="Pilon", bind_mounts=self.create_bind_mounts(), 
                            contigs=self.contigs, bam_file=self.bam, out_dir=self.out_dir, 
                            output=self.output_prefix, ram=self.ram, **self.kwargs)
        pilon_exc.execute()


class PolishWorkflow:
    """Call Pilon -> Minimap2 cycle for iterative pilon polishing
    """
    sam_ext = ".sam"
    bam_ext = ".bam"
    assembly_ext = ".fasta"

    def __init__(self, contigs: str, ram: int, reads: List[str], out_dir: str, Polisher_: Polisher, Mapper_: Mapper, prefix: str, max_iter:int = 10):
        self.Iteration = 0
        self.ram = ram
        self.max_iter = max_iter
        self.prefix = prefix
        self.mapping_string = "{prefix}_{iteration}{ext}"
        self.assembly_string = "{prefix}_{iteration}"
        self.contigs = contigs
        self.reads = reads
        self.out_dir = out_dir
        self.Polisher = Polisher_
        self.Mapper = Mapper_
        self.polish_till_endpoint()
    
    def polish_till_endpoint(self):
        """polish the assembly till a specified end point is reached
        """
        bam = self.map_reads(contigs=self.contigs, reads=self.reads, setting=Minimap2Settings.map_illumina, iteration=self.Iteration)
        assembly = self.pilon_polish(contigs=self.contigs, bam=bam, iteration=self.Iteration)
        self.Iteration += 1
        # polish till a specified end point is reached, need to add in support for the vcf and changes from pilon
        while(self.Iteration < self.max_iter):
            bam = self.map_reads(contigs=assembly, reads=self.reads, setting=Minimap2Settings.map_illumina, iteration=self.Iteration)
            assembly = self.pilon_polish(contigs=assembly, bam=bam, iteration=self.Iteration)
            if os.path.isfile(assembly):
                print(f"{assembly} exists")
            else:
                print(f"Assembly ({assembly}) does not exist")
                sys.exit(-1)
            self.Iteration += 1

    def pilon_polish(self, contigs, bam, iteration):
        """Run pilon to polish assemblies
        """
        prefix = self.assembly_string.format(prefix=self.prefix, iteration=iteration)
        polish_data = PolishAssembly(contigs=contigs, bam=bam, output_prefix=prefix, out_dir=os.getcwd(), ram=self.ram)
        polish_data.polish_assembly()
        return f"{prefix}{self.assembly_ext}"

    def map_reads(self, contigs, reads, setting: Minimap2Settings, iteration):
        """_summary_

        Args:
            contigs (_type_): _description_
            reads (_type_): _description_
            setting (_type_): _description_
            output_name (_type_): _description_
        """
        mapping_sam = self.mapping_string.format(prefix=self.prefix, iteration=iteration, ext=self.sam_ext)
        mapping = self.Mapper(contigs=contigs, reads=reads, output_name=mapping_sam, mapping_setting=setting)
        mapping.map_reads()
        mapping_bam = self.mapping_string.format(prefix=self.prefix, iteration=iteration, ext=self.bam_ext)
        samtools_bind_paths = ",".join([os.path.dirname(os.path.abspath(mapping_sam))])
        convert_to_bam = Executor("Samtools", samtools_bind_paths, "view", "-bu", "-o", mapping_bam, mapping_sam)
        convert_to_bam.execute()
        #sort
        sort_bam = Executor("Samtools", samtools_bind_paths, "sort", "-o", mapping_bam, mapping_bam)
        sort_bam.execute()
        #index
        index_bam = Executor("Samtools", samtools_bind_paths, "index", mapping_bam)
        index_bam.execute()
        return mapping_bam


if __name__ == "__main__":
    #TODO need to add in BWA-MEM
    workflow_start = PolishWorkflow(contigs=sys.argv[1], reads=[sys.argv[2], sys.argv[3]], out_dir=os.getcwd(), 
                                    Polisher_=PolishAssembly, Mapper_=IdxMapReads, max_iter=4, prefix="test")

