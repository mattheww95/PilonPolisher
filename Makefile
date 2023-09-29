
IMAGE_NAME=HybridPolisher.sif

# run with sudo
.PHONY: build
build:
	apptainer build $(IMAGE_NAME) ./Singularity.def


# example command
.PHONY: test_sam
test_sam:
	apptainer run $(IMAGE_NAME) samtools version
