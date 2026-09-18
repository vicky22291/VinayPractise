# Announcing Databricks Support for Amazon EC2 G6 Instances

- Source: https://www.databricks.com/blog/aws-ec2-g6
- Published: 2024-09-23
- Authors: Lu Wang (Databricks)
- Categories: engineering, data-science-machine-learning, databricks-ai, platform-and-products-and-announcements, platform-and-partners
- Images: 1 total, 0 extracted as architecture

We are excited to announce that Databricks now supports [Amazon EC2 G6 instances](https://aws.amazon.com/ec2/instance-types/g6/) powered by NVIDIA L4 Tensor Core GPUs. This addition marks a step forward in enabling more efficient and scalable data processing, machine learning, and AI workloads on the Databricks Data + AI Platform.

## **Why AWS G6 GPU Instances?**

Amazon Web Services (AWS) G6 instances are powered by lower-cost, energy-efficient NVIDIA L4 GPUs. Based on [NVIDIA’s 4th gen tensor core Ada Lovelace architecture](https://www.nvidia.com/en-us/geforce/ada-lovelace-architecture/), these GPUs offer support for the most demanding AI and machine learning workloads:

- G6 instances deliver up to [2x higher performance](https://aws.amazon.com/ec2/instance-types/g6/#:~:text=Why%20Amazon%20EC2%20G6%20Instances,compared%20to%20EC2%20G4dn%20instances) for deep learning inference and graphics workloads compared to G4dn instances that run on  NVIDIA T4 GPUs.
- G6 instances have twice the compute power but require only half the memory bandwidth of G5 instances powered by NVIDIA A10G Tensor Core GPUs. (Note: Most LLM and other autoregressive transformer model inference tends to be memory-bound, meaning that the A10G may still be a better choice for applications such as chat, but the L4 is performance-optimized for inference on compute-bound workloads.

## **Use Cases: Accelerating Your AI and Machine Learning Workflows**

- **Deep Learning inference**: The L4 GPU is optimized for batch inference workloads, providing a balance between high computational power and energy efficiency. It offers excellent support for TensorRT and other inference-optimized libraries, which help reduce latency and boost throughput in applications like computer vision, natural language processing, and recommendation systems.
- **Image and audio preprocessing**:  The L4 GPU excels in parallel processing, which is key for data-intensive tasks like image and audio preprocessing. For example, image or video decoding and transformations will benefit from the GPUs.
- **Training for deep learning models**: L4 GPU is highly efficient for training relatively smaller-sized deep learning models with fewer parameters (less than 1B)

## **How to Get Started**

To start using G6 GPU instances on Databricks, simply create a new compute with a GPU-enabled Databricks Runtime Version and choose G6 as the Worker Type and Driver Type. For details, check the [Databricks documentation](https://docs.databricks.com/en/compute/gpu.html#create-a-gpu-compute). 

G6 instances are available now in the AWS US East (N. Virginia and Ohio) and US West (Oregon) regions. You may check [the AWS documentation](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-regions.html) for more available regions in the future.

## **Looking Ahead**

The addition of G6 GPU support on AWS is one of the many steps we’re taking to ensure that Databricks remains at the forefront of AI and data analytics innovation. We recognize that our customers are eager to take advantage of cutting-edge platform capabilities and gain insights from their proprietary data. We will continue to support more GPU instance types, such as Gr6 and P5e instances, and more GPU types, like AMD. Our goal is to support AI compute innovations as they become available to our customers.

## **Conclusion**

Whether you are a researcher who wants to [train DL models like recommendation systems](https://www.databricks.com/blog/training-deep-recommender-systems-1), a data scientist who wants to run DL batch inferences with your data from UC, or a data engineer who wants to process your video and audio data, this latest integration ensures that Databricks continues to provide a robust, future-ready platform for all your data and AI needs.

Get started today and experience the next level of performance for your data and machine learning workloads on Databricks.
