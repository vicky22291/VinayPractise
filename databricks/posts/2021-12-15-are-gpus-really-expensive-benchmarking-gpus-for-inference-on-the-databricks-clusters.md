# Are GPUs Really Expensive? Benchmarking GPUs for Inference on Databricks Clusters

- Source: https://www.databricks.com/blog/2021/12/15/are-gpus-really-expensive-benchmarking-gpus-for-inference-on-the-databricks-clusters.html
- Published: 2021-12-15
- Authors: Srijith Rajamohan, Ph.D.
- Categories: engineering, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

It is no secret that GPUs are critical for artificial intelligence and deep learning applications since their highly-efficient architectures make them ideal for compute-intensive use cases. However, almost everyone who has used them is also aware of the fact they tend to be expensive! In this article, we hope to show that while the per-hour cost of a GPU might be greater, it might in fact be cheaper from a total cost-to-solution perspective. Additionally, your time-to-insight is going to be substantially lower, potentially leading to additional savings. In this benchmark, we compare the runtimes and the cost-to-solution for 8 high-performance GPUs with 2 CPU-only cluster configurations that are available on the Databricks platform, for an NLP application.

## Why are GPUs beneficial?

GPUs are ideally suited to this task since they have a substantial number of compute units with an architecture designed for number crunching. For example, the A100 Nvidia GPU has been shown to be about 237 times faster than CPUs on the MLPerf benchmark ([https://blogs.nvidia.com/blog/2020/10/21/inference-mlperf-benchmarks/](https://blogs.nvidia.com/blog/2020/10/21/inference-mlperf-benchmarks/)). Specifically, for deep learning applications, there has been quite a bit of work done to create mature frameworks such as Tensorflow and Pytorch that allows the end-users to take advantage of these architectures. Not only are the GPUs designed for these compute-intensive tasks, but the infrastructure surrounding it, such as [NVlink](https://www.nvidia.com/en-us/design-visualization/nvlink-bridges/) interconnects for high-speed data transfers between GPU memories. The [NCCL library](https://developer.nvidia.com/nccl)allows one to perform multi-GPU operations over the high-speed interconnects so that these deep learning experiments can scale over thousands of GPUs. Additionally, NCCL is tightly integrated into the most popular deep learning frameworks.

While GPUs are almost indispensable for deep learning, the cost-per-hour associated with them tends to deter customers. However, with the help of the benchmarks used in this article  I hope to illustrate two key points:

- **Cost-of-solution** - While the cost-per-hour of a GPU instance might be higher, the total cost-of-solution might, in fact, be lower.
- **Time-to-insight** - With GPUs being faster, the time-to-insight, is usually much lower due to the iterative nature of deep learning or data science. This in turn can result in lower infrastructure costs such as the cost of storage.

## The benchmark

In this study, GPUs are used to perform inference in a NLP task, or more specifically sentiment analysis over a text set of documents. Specifically, the benchmark consists of inference performed on three datasets

1. A small set of 3 JSON files
2. A larger Parquet
3. The larger Parquet file partitioned into 10 files

The goal here is to assess the total runtimes of the inference tasks along with variations in the batch size to account for the differences in the GPU memory available. The GPU memory utilization is also monitored to account for runtime disparities. The key to obtaining the most performance from GPUs is to ensure that all the GPU compute units and memory are sufficiently occupied with work at all times.

The cost-per-hour of each of the instances tested are listed and we calculate the total inference cost in order to make meaningful business cost comparisons. The code used for the benchmark is provided below.

## The infrastructure -  GPUs & CPUs

The benchmarks were run on 8 GPU clusters and 2 CPU clusters. The GPU clusters consisted of the K80s (Kepler), T4s (Turing) and the V100s (Volta) GPUs in various configurations that are available on Databricks through the AWS cloud backend.  The instances were chosen with different configurations of compute and memory configurations. In terms of pure throughput, the Kepler architecture is the oldest and the least powerful while the Volta is the most powerful.

### The GPUs

1. G4dn

These instances have the NVIDIA T4 GPUs (Turing) and Intel Cascade Lake CPUs. According to AWS ‘They are optimized for machine learning inference and small scale training’. The following instances were used:

| Name | GPUs | Memory | Price |
|---|---|---|---|
| g4dn.xlarge | 1 | 16GB | $0.071 |
| g4dn.12xlarge | 4 | 192GB | $0.856 |
| G4db.16xlarge | 1 | 256GB | $1.141 |

1. P2

These have the K80s (Kepler) and are used for general purpose computing.

| Name | GPUs | Memory | Price |
|---|---|---|---|
| p2.xlarge | 1 | 12GB | $0.122 |
| p2.8xlarge | 8 | 96GB | $0.976 |

1. P3

P3 instances offer up to 8 NVIDIA® V100 Tensor Core GPUs on a single instance and are ideal for machine learning applications. These instances can offer up to one petaflop of mixed-precision performance per instance. The P3dn.24xlarge instance, for example, offers [4x the network bandwidth](https://aws.amazon.com/blogs/aws/new-ec2-p3dn-gpu-instances-with-100-gbps-networking-local-nvme-storage-for-faster-machine-learning-p3-price-reduction/) of P3.16xlarge instances and can support NCCL for distributed machine learning.

| Name | GPUs | GPU Memory | Price |
|---|---|---|---|
| p3.2xlarge | 1 | 16GB | $0.415 |
| p3.8xlarge | 4 | 64GB | $1.66 |
| p3dn.24xlarge | 8 | 256GB | $4.233 |

### CPU instances

C5

The C5 instances feature the Intel Xeon Platinum 8000 series processor (Skylake-SP or Cascade Lake) with clock speeds of up to 3.6 GHz. The clusters selected here have either 48 or 96 vcpus and either 96GB or 192GB of RAM. The larger memory allows us to use larger batch sizes for the inference.

| Name | CPUs | CPU Memory | Price |
|---|---|---|---|
| c5.12x | 48 | 96GB | $0.728 |
| c5.24xlarge | 96 | 192GB | $1.456 |

## Benchmarks

### Test 1

Batch size is set to be 40 times the total number of GPUs in order to scale the workload to the cluster. Here, we use the single large file as is and without any partitioning. Obviously, this approach will fail where the file is too big to fit on the cluster.

| Instance | Small dataset (s) | Larger dataset (s) | Number of GPUs | Cost per hour | Cost of inference (small dataset) | Cost of inference (large dataset) |
|---|---|---|---|---|---|---|
| G4dn.x | 19.3887 | NA | 1 | $0.071 | 0.0003 | NA |
| G4dn.12x | 11.9705 | 857.6637 | 4 | $0.856 | 0.003 | 0.204 |
| G4dn.16x | 20.0317 | 2134.0858 | 1 | $1.141 | 0.006 | 0.676 |
| P2.x | 36.1057 | 3449.9012 | 1 | $0.122 | 0.001 | 0.117 |
| P2.8x | 11.1389 | 772.0695 | 8 | $0.976 | 0.003 | 0.209 |
| P3.2x | 10.2323 | 622.4061 | 1 | $0.415 | 0.001 | 0.072 |
| P3.8x | 7.1598 | 308.2410 | 4 | $1.66 | 0.003 | 0.142 |
| P3.24x | 6.7305 | 328.6602 | 8 | $4.233 | 0.008 | 0.386 |

As expected, the Voltas perform the best followed by the Turings and the Kepler architectures. The runtimes also scale with the number of GPUs with the exception of the last two rows. The P3.8x cluster is faster than the P3.24x in spite of having half as many GPUs. This is due to the fact that the per-GPU memory utilization is at 17% on the P3.24x compared to 33% on the P3.8x.

### Test 2

Batch size is set to be 40 times the number of GPUs available in order to scale the workload for larger clusters. The larger file is now partitioned into 10 smaller files. The only difference from the previous result table are the highlighted columns corresponding to the larger file.

| Instance | Small dataset (s) | Larger dataset (s) | Number of GPUs | Cost per hour | Cost of inference (small) | Cost of inference(large) |
|---|---|---|---|---|---|---|
| G4dn.x | 19.3887 | 2349.5816 | 1 | $0.071 | 0.0003 | 0.046 |
| G4dn.12x | 11.9705 | 979.2081 | 4 | $0.856 | 0.003 | 0.233 |
| G4dn.16x | 20.0317 | 2043.2231 | 1 | $1.141 | 0.006 | 0.648 |
| P2.x | 36.1057 | 3465.6696 | 1 | $0.122 | 0.001 | 0.117 |
| P2.8x | 11.1389 | 831.7865 | 8 | $0.976 | 0.003 | 0.226 |
| P3.2x | 10.2323 | 644.3109 | 1 | $0.415 | 0.001 | 0.074 |
| P3.8x | 7.1598 | 350.5021 | 4 | $1.66 | 0.003 | 0.162 |
| P3.24x | 6.7305 | 395.6856 | 8 | $4.233 | 0.008 | 0.465 |

### Test 3

In this case, the batch size increased to 70 and the large file is partitioned into 10 smaller files. In this case, you would notice that the P3.24x cluster is faster than the P3.8x cluster because the per-GPU utilization is much higher on the P3.24x compared to the previous experiment.

| Instance | Small dataset (s) | Larger dataset (s) | Number of GPUs | Cost per hour | Cost of inference (small dataset) | Cost of inference (large dataset) |
|---|---|---|---|---|---|---|
| G4dn.x | 18.6905 | 1702.3943 | 1 | $0.071 | 0.0004 | 0.034 |
| G4dn.12x | 9.8503 | 697.9399 | 4 | $0.856 | 0.002 | 0.166 |
| G4dn.16x | 19.0683 | 1783.3361 | 1 | $1.141 | 0.006 | 0.565 |
| P2.x | 35.8419 | OOM | 1 | $0.122 | 0.001 | NA |
| P2.8x | 10.3589 | 716.1538 | 8 | $0.976 | 0.003 | 0.194 |
| P3.2x | 9.6603 | 647.3808 | 1 | $0.415 | 0.001 | 0.075 |
| P3.8x | 7.5605 | 305.8879 | 4 | $1.66 | 0.003 | 0.141 |
| P3.24x | 6.0897 | 258.259 | 8 | $4.233 | 0.007 | 0.304 |

### Inference on CPU-only clusters

Here we run the same inference problem, but only using the smaller dataset this time on cpu-only clusters. Batch size is selected as 100 times the number of vcpus.

| Instance | Small dataset (s) | Number of vcpus | RAM | Cost per hour | Cost of inference |
|---|---|---|---|---|---|
| C5.12x | 42.491 | 48 | 96 | $0.728 | $0.009 |
| C5.24x | 40.771 | 96 | 192 | $1.456 | $0.016 |

You would notice that for both clusters, the runtimes are slower on the CPUs but the cost of inference tends to be more compared to the GPU clusters. In fact, not only is the most expensive GPU cluster in the benchmark (P3.24x) about 6x faster than both the CPU clusters, but the total inference cost ($0.007) is less than even the smaller CPU cluster (C5.12x, $0.009).

## Conclusion

There is a general hesitation to adopt GPUs for workloads due to the premiums associated with their pricing, however, in this benchmark we have been able to illustrate that there could potentially be cost savings to the user from replacing CPUs with GPUs. The time-to-insight is also greatly reduced, resulting in faster iterations and solutions which can be critical for GTM strategies.

Check out the[repository with the notebooks and the notebook runners](https://github.com/srijith-rajamohan/nlp-inference-benchmarking) on Github.
