<!-- source: https://www.cncf.io/case-studies/prep-edu/
     published: 2025-08-21T00:36:23+00:00
     fetched: 2026-10-24 -->

# Prep EDU

## Enabling Efficient GPU Orchestration for AI Inference at PREP EDU

### Challenge
PREP EDU operates a Kubernetes-based AI inference platform with a heterogeneous GPU cluster, primarily composed of RTX 4070 and RTX 4090 nodes. This diversity in GPU hardware introduced significant complexity in resource orchestration, as different workloads often required specific GPU types for optimal performance and compatibility.
Static allocation led to chronically low GPU utilization—often as low as 10–20%—with much of the available compute power left idle.
To address this inefficiency, the team explored other GPU-sharing solutions prior to adopting HAMi. However, these alternatives lacked effective resource isolation, resulting in multiple tasks competing for GPU resources. This frequently caused resource conflicts, memory allocation issues, and application crashes, making it difficult to guarantee fair and efficient resource sharing among workloads and impacting overall service stability.
Furthermore, the team had a strong concern for compatibility: any solution adopted needed to seamlessly integrate with their existing production environment, which included the GPU Operator and RKE2 Kubernetes distribution. The team needed a solution that could intelligently orchestrate heterogeneous GPU resources, provide robust isolation to prevent task interference, and significantly improve overall resource utilization and ensure compatibility with their current infrastructure.

### Solution
The team adopted HAMi, a CNCF sandbox project, as their GPU orchestration solution. The decision to use HAMi was influenced by its strong presence in the area of GPU scheduling when searching for GPU-sharing solutions on GitHub. The document of HAMi was clear and well-suited for their Kubernetes (RKE2) environment. HAMi was chosen for its maturity and early leadership in the area of GPU scheduling, as well as its compatibility with a wide range of NVIDIA GPUs. HAMi’s vGPU scheduling capabilities allowed PREP EDU to:
- Virtualization and GPU partition: for multiple inference services, setting specific limits for each workload based on NLP token length and service needs.
- Heterogeneous GPU Management: With HAMi, workloads can be assigned to specific GPU types (e.g., running certain projects only on RTX 4070 or 4090), improving compatibility and efficiency with annotation-based resource selection
- Seamless Application Integration : Enable GPU sharing and isolation without requiring application changes, thanks to HAMi’s transparent device virtualization.
- GPU Specification : The ability to assign applications to specific GPU by UUID (for example, running multiple processes on a certain 4090 24GB card)
- Compatibility: HAMi and NVIDIA GPU Operator could coexist in their environment without conflict, both were configured to use containerd. It also has Leverage advanced features such as monitoring, and alerting with Prometheus, and seamless integration with Kubernetes (RKE2) and containerd.
On top of that, The Devops team of PREP EDU made a lot of optimizations to their workflow which have been adopted in the production environment:
- Engineering a workflow where any new node joining the cluster is automatically managed by HAMi, ensuring consistent orchestration across the fleet.
- Exploring self-hosting HAMi for GPU orchestration in Docker environments to support specialized jobs.
- Finding the best practice to co-operate with NVIDIA GPU operator, that makes the cluster easy to scale.
These contributions lead to the 50% pain points reduction in GPU cluster, and 90% optimization of GPU infrastructure.

### Impact
With the help of HAMi, and all the optimizations by the Devops team, the impact is quite notable:
- Deep Integration: HAMi now efficiently manages 90% of the GPU infrastructure, providing unified orchestration across the cluster.
- Operational Efficiency: Application crashes caused by memory conflicts have been eliminated, resolving 50% of the team’s previous pain points in GPU resource management.
- Scalability: The team can seamlessly add new GPU nodes, with HAMi automatically orchestrating resources across heterogeneous hardware.
- Flexibility: Workloads can be precisely assigned to specific GPU types or UUIDs, and the platform is well-positioned for future expansion to support training and large language model (LLM) workloads.
The DevOps team continues to fine-tune scheduling parameters and algorithms, ensuring the delivery of stable, high-performance, and efficient GPU services as business needs evolve.
Projects used
By the numbers
1 YEAR
using HAMi in production
90%
of GPU infra optimized using HAMi
50%
reduction in GPU management pain points
> “HAMi is a great option for vGPU scheduling, helping us optimize GPU usage for our AI microservices. Its monitoring and alerting features are also very helpful for long-term tracking. The documentation is clear, and the ability to assign workloads to specific GPU types is a huge advantage for us.” Xeus Nguyen, DevOps Engineer, PREP EDU
“HAMi is a great option for vGPU scheduling, helping us optimize GPU usage for our AI microservices. Its monitoring and alerting features are also very helpful for long-term tracking. The documentation is clear, and the ability to assign workloads to specific GPU types is a huge advantage for us.”
> “HAMi allows precise GPU memory and compute allocation for each project, helping optimize overall resource usage. This makes it possible to deploy more AI services on the same limited amount of GPU VRAM, improving efficiency and scalability.” Nhan Phan, AI Engineer, PREP EDU
“HAMi allows precise GPU memory and compute allocation for each project, helping optimize overall resource usage. This makes it possible to deploy more AI services on the same limited amount of GPU VRAM, improving efficiency and scalability.”
> “HAMi helped us overcome challenges in GPU management for our on-premise AI microservices by automating workload allocation and reducing maintenance overhead. It significantly improved resource efficiency with minimal effort from our team.” Phong Nguyen, AI Engineer, PREP EDU
“HAMi helped us overcome challenges in GPU management for our on-premise AI microservices by automating workload allocation and reducing maintenance overhead. It significantly improved resource efficiency with minimal effort from our team.”
> “HAMi has been a game-changer for our AI engineering workflow. By virtualizing and right-sizing GPU resources at the pod level, we can pack lightweight inference services and large batch jobs onto the same hardware without noisy-neighbor issues. Deployment is practically “plug-and-play” a Helm chart and a couple of labels. So we kept our existing manifests intact.” Vu Hoang Tran, AI Engineer, PREP EDU
“HAMi has been a game-changer for our AI engineering workflow. By virtualizing and right-sizing GPU resources at the pod level, we can pack lightweight inference services and large batch jobs onto the same hardware without noisy-neighbor issues. Deployment is practically “plug-and-play” a Helm chart and a couple of labels. So we kept our existing manifests intact.”
Share
