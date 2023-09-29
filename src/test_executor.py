"""Verify that executor class globals element still works
"""

from tools import Executor, Minimap2Settings, FlyeInputs



if __name__ == "__main__":
    Executor("BCFTools", "view", "in.vcf.gz")
    Executor("Samtools", "view", "infile")
    Executor("Minimap2", Minimap2Settings.map_ont, reads=["reads.fq.1", "reads.fq.2"], index="test.idx", output_name="out_test")
    Executor("Minimap2", Minimap2Settings.create_index, output_name="test.idx", contigs="contigs")
    Executor("Pilon", "contigs", "bam_file", "test", "test")
    Executor("Flye", FlyeInputs.pacbio_raw, ["t1", "t2"], "test")
