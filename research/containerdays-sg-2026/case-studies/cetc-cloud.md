<!-- source: https://www.cncf.io/case-studies/cetc-cloud/
     published: 2026-09-08T09:09:15+00:00
     fetched: 2026-10-24 -->

# CETC Cloud

## CETC Cloud Builds a Heterogeneous GPU Shared Resource Foundation for a Portable Knowledge Base with HAMi
CETC Cloud (Beijing) Technology needed to bring its intelligent knowledge base to project sites, running text generation, embedding, rerank, knowledge processing, and R&D debugging workloads together on a single set of portable devices equipped with heterogeneous GPUs. The team adopted Kubernetes and HAMi to turn these limited heterogeneous GPUs, previously bound long-term to individual services, into resources that production models and Kubernetes development environments can request, share, and schedule on demand.
On top of this resource foundation, text generation, vector embedding, and rerank models form a complete knowledge base pipeline; a single heterogeneous GPU can also be shared by multiple Kubernetes dev Pods/containers through HAMi’s virtualization capability.
Projects used
By the numbers
15X dev capacity
increased from 2 to 30 concurrent dev Pods on the same 8-GPU portable device.
87.5% VRAM Reclaimed
Embedding went from occupying an entire 64 GB GPU to an 8 GB allocation , leaving 56 GB reusable.
80% Compute Reclaimed
Embedding was allocated 20% of GPU compute , leaving the remaining 80% schedulable for other workloads.

### Case Information
| Item | Detail |
| User | CETC Cloud technical team |
| Business scenario | An intelligent knowledge base appliance that can be carried to project sites and run independently |
| Deployment environment | Kubernetes and on-premises heterogeneous GPUs |
| Projects used | Kubernetes, HAMi |
| Core challenges | Multi-model coordination, shared production and development |

## Scope of Practice
| Knowledge base production pipeline | Kubernetes dev environment |
| Text generation, Embedding, Rerank | Multiple dev Pods/containers share a single heterogeneous GPU |
This practice covers two GPU usage paths: knowledge base production models primarily use local stable resources, while Kubernetes dev Pods/containers share the local heterogeneous GPU through HAMi.
Figure 1: Production models and the Kubernetes dev environment each use the local heterogeneous GPU through HAMi. One portable device must serve both production and R&D
The knowledge base’s online Q&A depends on text generation, vector retrieval, and rerank; once data enters the system it must also go through parsing, chunking, vectorization, knowledge extraction, and index building. R&D engineers also need to debug models, validate dependencies, and run experiments inside Kubernetes dev Pods/containers. These workloads use GPUs in very different ways:
- Text generation models must stay online long-term, with a high VRAM baseline and sensitivity to response latency;
- Embedding creates periodic peaks during bulk document import and is more throughput-oriented;
- Rerank sits on the online retrieval path: short per-call compute, but invoked frequently;
- Knowledge processing and index rebuilds are batch jobs that must be isolated from online services;
- Dev Pods/containers are periodic and interactive by nature, well suited to sharing GPUs within clear resource boundaries.
If each service or dev environment continues to bind a whole card long-term, the limited devices are quickly exhausted logically; if the team only pursues the finest possible partitioning, it amplifies VRAM shortages, scheduling jitter, and fault propagation. The team needed a way for each workload type to describe its own needs, then let the platform complete resource placement based on device state and service tier.
Figure 2: Business documents enter the knowledge base through parsing, embedding, and index building; an online question goes through retrieval, rerank, and text generation to produce an answer, citation, or report.

## Why HAMi
CETC Cloud wanted to keep the Kubernetes application delivery model while letting the platform further understand whether heterogeneous GPU devices can satisfy workload requests, and letting dev environments suited to sharing reuse the same physical GPU. The Kubernetes-native resource declaration, device-aware placement, device sharing, and runtime observation provided by HAMi map directly onto these three requirements.
The value of HAMi is not merely representing one physical card as multiple resource shares; more importantly, it establishes a common resource contract:
- Model services and dev Pods/containers describe the device resources they need, instead of relying on long-term manual card binding;
- Scheduling does not merely check whether a GPU exists on a node; it selects based on available device state;
- Within what the actual device backend supports, multiple dev Pods/containers can share a single heterogeneous GPU, each with its own resource boundary;
- Pods, containers, devices, and scheduling results can be correlated back together, providing a basis for capacity observation and resource configuration correction.

## From resource profiling to sharing the heterogeneous GPU
The team built resource profiles around workload characteristics, focusing on model loading, peak usage, concurrency, latency, and long-running behavior, then translated the validated requirements into Kubernetes resource requests. Production models and dev environments follow different strategies:
- Stable boundaries for the online path. Text generation, online vector retrieval, and rerank receive stable resources first.
- Periodic tasks may queue and run off-peak. Document vectorization, knowledge extraction, and index rebuilding run when online load is low.
- Dev environments share a single heterogeneous GPU. Multiple Kubernetes dev Pods/containers reuse a heterogeneous GPU through HAMi’s virtualization, instead of each dev environment holding a device exclusively long-term.
- Configuration is corrected by real load. Partitioning granularity comes from baseline validation and runtime observation, not from a preset ratio assumed universal across models.
This resource governance approach delivers four product capabilities:
- Text generation, embedding, and rerank are brought under one Kubernetes GPU resource governance process;
- Knowledge ingestion, retrieval, Q&A, and report generation form a complete running pipeline;
- Online services, batch tasks, and R&D debugging follow different resource rules;
- A single heterogeneous GPU can simultaneously serve multiple Kubernetes dev Pods/containers.

## Quantified result: per-device dev environment capacity rises from 2 to 30
On the same portable device equipped with 8 heterogeneous GPUs, the team compared resource capacity before and after introducing HAMi on a consistent basis:
| Comparison item | Without HAMi | With HAMi |
| Text generation models | Exclusively occupies 4 heterogeneous GPUs | Still exclusively occupies 4 heterogeneous GPUs |
| Embedding and Rerank | Each exclusively occupies 1 heterogeneous GPU | Each requests an 8GB GPU VRAM quota |
| Capacity available to dev environments | Remaining 2 GPUs, hosting only 2 dev Pods | Verified to host 30 dev Pods concurrently |
| Dev environment capacity | Baseline | Increased to 15× the original |
The VRAM quota for a dev Pod is requested by users according to their task needs; the platform does not set a unified fixed value. Under the current model quotas and dev load, the team completed the validation of 30 dev Pods running simultaneously.

### Single-card resource comparison for the Embedding model
The Embedding model actually needs about 8GB of VRAM on a single 64GB heterogeneous GPU. Under whole-card exclusive use, the model consumes only ~12.5% of the VRAM, but the remaining resources cannot be claimed by other workloads; after introducing HAMi, the team allocated 8GB of VRAM and 20% compute to the model as required and brought the remaining resources back into scheduling. Using the same model image, request set, and concurrency configuration, the team compared whole-card exclusive use against HAMi partitioning.
| Metric | Without HAMi | With HAMi |
| Embedding VRAM allocation | Exclusively occupies the whole 64GB GPU | 8GB allocated on demand |
| Actual model VRAM requirement | ~8GB | ~8GB |
| VRAM reusable by other tasks | 0GB | 56GB, i.e. 87.5% of the whole card |
| Embedding compute allocation | Exclusively occupies the whole card | 20% allocated, the remaining 80% schedulable |
| Token throughput (tokens/s) | Baseline | Within 5% of whole-card exclusive use |
| Model load time | Baseline | Essentially identical to whole-card exclusive use; no notable change observed |
| P95 request latency | Baseline | Essentially identical to whole-card exclusive use; no notable change observed |
This same-card, same-model comparison shows that HAMi moved Embedding from whole-card exclusive use to on-demand allocation, releasing VRAM and compute while keeping the Token throughput change within 5% and model load time and P95 request latency essentially stable, letting the same heterogeneous GPU continue to host dev environments or other sharing-friendly tasks.

## Lessons learned
First, heterogeneous GPU sharing should start from workload profiles, not from a preset uniform partitioning ratio. Production models, batch tasks, and dev environments differ in their requirements for latency, VRAM, throughput, and isolation, so their resource policies should differ too.
Second, R&D environments are an important consumer of shared GPUs. Running dev environments in Kubernetes Pods/containers reuses the same resource declarations and scheduling method as production services, while avoiding each dev environment holding a device exclusively long-term.
In the next phase, CETC Cloud will keep refining the capacity and health views for production and R&D workloads, and add reproducible experimental data across different models, networks, and calling patterns.

## About HAMi
HAMi is an open source project for heterogeneous compute virtualization and unified scheduling, co-founded by Li Mengxuan and Zhang Xiao, and now a CNCF Incubating project. With the mission of “making heterogeneous compute easy to use through open source,” it is dedicated to improving heterogeneous compute utilization and providing a unified reuse interface for heterogeneous GPUs. HAMi today supports a wide range of heterogeneous accelerators, including NVIDIA, Ascend, Cambricon, Hygon, Iluvatar CoreX, Moore Threads, MetaX, Enflame, Kunlunxin, AWS Neuron, and Vastai. It integrates broadly with projects such as Volcano, Kueue, Koordinator, vLLM, and KAI Scheduler, has drawn more than 500 contributors from over 20 countries and regions, and is already running in production at hundreds of enterprises.

## About the CETC Cloud technical team
The CETC Cloud technical team in this case is responsible for the product development and engineering delivery of the portable intelligent knowledge base, building product capabilities around on-site local operation, knowledge processing, model serving, and dev environments.
You are welcome to exchange practical questions about shared GPUs and portable AI through the HAMi community.
Share
