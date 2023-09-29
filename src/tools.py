"""Wrappers to prepare each subprocess for each tool to call

    TODO a secondary wrapper will be needed to wrap up each tool so that the command is executed \ 
    using the singularity image

Matthew Wells: 2023-05-18
"""
import sys
import os
import shutil
import time
from subprocess import Popen
from typing import List
#StrEnum is 3.11 specific, and it may be better to implement it myself
from enum import StrEnum # python3.11 feature only?
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Program(ABC):
    """Abstract base class for implementation of each tool
    """

    @abstractmethod
    def create_command(self) -> List[str]:
        pass

    def __repr__(self) -> str:
        return " ".join(self.create_command())


class Racon(Program):
    """wrapper for racon commands

    Args:
        Program (_type_): _description_

    Returns:
        _type_: _description_
    """

    binary = "racon"
    def __init__(self, reads: List[str], sam, contigs, output_name, *args, **kwargs) -> None:
        self.reads = reads
        self.contigs = contigs
        self.sam = sam
        self.output_name = output_name
        self.args = args
        self.kwargs = kwargs

    def create_command(self) -> List[str]:
        return [self.binary, *self.reads, self.sam, self.contigs, *self.args, ">", self.output_name]

class FlyeInputs(StrEnum):
    pacbio_raw = "--pacbio-raw"
    pacbio_corr =  "--pacbio-corr"
    pacbio_hifi = "--pacbio-hifi"
    nano_raw = "--nano-raw"
    nano_corr = "--nano-corr"
    nano_hq = "--nano-hq"

@dataclass(frozen=True)
class FlyeOpts:
    threads: str = "--threads"

class Flye(Program):
    """Class to run the Flye program
    """
    binary = "flye"
    
    def __init__(self, mode: FlyeInputs, input_files: List[str], out_dir: str, *args, **kwargs) -> None:
        self.mode = mode
        self.input_files = input_files
        self.out_dir = out_dir
        self.args = args
        self.kwargs = kwargs
        if self.kwargs.get(FlyeOpts.threads) is not None:
            self.args.append(FlyeOpts.threads)
            self.args.append(self.kwargs[FlyeOpts.threads])

    
    def create_command(self):
        """Create the flye command to be passed to a subprocess
        """
        return [self.binary, self.mode, *self.input_files, "--out-dir", self.out_dir, *self.args, ]


class Pilon(Program):
    """Class to wrap up the pilon command options
        #TODO add in BWA as pilon wants that not minimap2
        TODO need to track number of changes pilon outputs each time
    """

    __ram = str(16) # default GB of ram to hand pilon
    __default_args = ["--changes", "--vcf", "--vcfqe"]
    binary = "pilon"
    def __init__(self, contigs: str, bam_file: str, output: str, out_dir: str, 
                 ram: int = __ram, *args, **kwargs):
        self.contigs = contigs
        self.bam_file = bam_file
        self.output = output
        self.out_dir = out_dir
        self.__ram = str(ram)
        self._binary = ["java", f"-Xmx{self.__ram}G", "-jar", "/usr/bin/pilon.jar"]
    
    def create_command(self):
        """Create command for each parameter
        """
        return [*self._binary, "--genome", self.contigs, "--bam", self.bam_file, "--output", self.output, "--outdir", self.out_dir, *self.__default_args]


class Minimap2Settings(StrEnum):
    """Settings for passing minimap2, for either index generation or read mapping
    """
    map_illumina = "sr"
    map_pac = "map-pb"
    map_ont = "map-ont"
    create_index = "-d"


class Minimap2(Program):
    """wrapper for minimap2

    Args:
        Program (_type_): _description_
    """

    binary = "minimap2"
    __pipe_direction = ">"
    idx_suffix = ".idx"

    def __init__(self, setting: Minimap2Settings, reads: List[str] = None, index: str = None, output_name: str = None, contigs: str = None, *args, **kwargs):
        self.setting = setting.value
        self.args = list(args)
        if self.setting == Minimap2Settings.create_index:
            self.index_name = output_name
            self.contigs = contigs
            self.commands = [self.setting, self.index_name, *self.args, self.contigs]
        else:
            if index is None and contigs is not None:
                self.index = contigs
            else:     
                self.index = index
            self.reads = reads
            self.output_name = output_name
            # direction operator added as minimap2 pipes to stdout
            # -ax flag for mapping with minimap2
            self.commands = ["-ax", self.setting, *self.args, self.index, *self.reads, "-o", self.output_name]

    def create_command(self):
        return [self.binary, *self.commands]


class Samtools(Program):
    """Wrapper for samtools, as samtools has many functions this definition will intially be very simple
    until the expected functionality is more fleshed out
    """

    binary = "samtools"
    def __init__(self, *args):
        self.args = args
    
    def create_command(self) -> List[str]:
        return [self.binary, *self.args]

class BCFTools(Program):
    """_summary_

    Args:
        Program (_type_): _description_
    """
    binary = "bcftools"
    def __init__(self, *args, **kwargs):
        self.args = args
    
    def create_command(self) -> List[str]:
        return [self.binary, *self.args]


class ExecutorOptions(StrEnum):
    apptainer = "apptainer"
    singularity = "singularity"
    local = "local"


class Executor:
    """Execute a given program based on passed args

    TODO allow executor to specify slurm, singularity or apptainer for wrapping class to be passed to executor
    TODO add in logic to check if apptainer is installed then singularity
    #TODO TODO need to make it check for tool in path first before apptainer or atleast have it check if the binary exists in the abscence of a container
    """
    __singularity_image_name = "HybridPolisher.sif" 
    __singularity_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), __singularity_image_name) #TODO clean this up with pathlib
    __wait_time = 0
    __local_execution = True
    
    def __init__(self, prog: Program, bind_mounts:str = None, *args, **kwargs):
        self.program = globals().get(prog) # TODO need to use AST module to create a StrEnum of all programs to use
        self.bind_mounts = bind_mounts
        if self.program is None:
            #TODO implement logging
            print(f"Program {prog} is not implemented.", flush=True)
            sys.exit(-1)
        if not os.path.isfile(self.__singularity_path) and not self.__local_execution:
            print(f"Singularity image {self.__singularity_image_name} at {self.__singularity_path} not found", flush=True)
            print(f"Nor is program {prog} in path.", flush=True)
            sys.exit(-1)

        self.allowed = [i.__name__ for i in Program.__subclasses__()]
        self.kwargs = kwargs
        self.initialized = self.program(*args, **kwargs)

    def check_executor(self):
        """Check if a given executor e.g. apptainer or singularity exists in the user path
            or if the binary for the file is in the path
        """

        if self.__local_execution:
            return ExecutorOptions.local
        elif shutil.which(ExecutorOptions.apptainer):
            return ExecutorOptions.apptainer
        elif shutil.which(ExecutorOptions.singularity):
            return ExecutorOptions.singularity
        print("No valid executor specified")
        sys.exit(-1)

    def create_cmd(self):
        """Execute command in relation to whichever executor is too be used
        """
        # run apptainer
        executor = self.check_executor()
        if self.bind_mounts is not None and executor != ExecutorOptions.local:
            return [executor.value, "run", "--bind", self.bind_mounts, self.__singularity_path, *self.initialized.create_command()]
        elif executor == ExecutorOptions.local:
            return [*self.initialized.create_command()]
        else:
            print(f"No bind mounts specified when executing singularity image, data will not be copied to and from container.", flush=True)
            return [executor.value, "run", self.__singularity_path, *self.initialized.create_command()]
    
    def execute(self):
        """Execute passed commands
        """
        user_env = os.environ.copy()
        proc = Popen(self.create_cmd(), env=user_env)
        print(f"Executing {self.program.__name__}", flush=True)
        proc.wait()
        time.sleep(self.__wait_time) # added a wait as the next process may have been executed a bit too quick
        


if __name__ == "__main__":

    print(Flye(FlyeInputs.pacbio_raw, ["t1", "t2"], "test"))
    print(Pilon("contigs", "bam_file", "test", "test"))
    print(Minimap2(Minimap2Settings.create_index, output_name="test.idx", contigs="contigs"))
    print(Minimap2(Minimap2Settings.map_ont, reads=["reads.fq.1", "reads.fq.2"], index="test.idx", output_name="out_test"))
    print(Samtools("view", "infile"))
    print(BCFTools("view", "in.vcf.gz"))

    Executor("BCFTools", "view", "in.vcf.gz")
    Executor("Samtools", "view", "infile")
    Executor("Minimap2", setting=Minimap2Settings.map_ont, reads=["reads.fq.1", "reads.fq.2"], index="test.idx", output_name="out_test")
    Executor("Minimap2", setting=Minimap2Settings.create_index, output_name="test.idx", contigs="contigs")
    Executor("Pilon", contigs="contigs", bam_file="bam_file", output="test", out_dir="test")
    Executor("Flye", mode=FlyeInputs.pacbio_raw, input_files=["t1", "t2"], out_dir="test")
    test_sam = Executor("Samtools", "help")
    print(test_sam.create_cmd())
    #test_sam.execute()