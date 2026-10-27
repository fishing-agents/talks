<!-- source: https://www.cncf.io/case-studies/sangfor/
     published: 2026-09-09T06:16:08+00:00
     fetched: 2026-10-24 -->

# Sangfor

## How Sangfor Built an Enterprise AI Compute Platform with Kubernetes, Volcano, and HAMi
Sangfor is a leading enterprise cloud computing and cybersecurity vendor in China. With the rapid growth of AI applications, Sangfor is building a unified AI compute platform for its internal R&D teams and enterprise customers, supporting scenarios such as AI coding, digital employees, intelligent customer service, and sales Agents.
As the platform continued to scale, GPU utilization, resource isolation, and scheduling efficiency became the key bottlenecks. Sangfor built a production-grade shared GPU platform on Kubernetes , Volcano , and HAMi , turning Kubernetes into a unified AI resource control plane.
| Metric | Before | After |
| GPU utilization | Baseline | Up more than 3x |
| Models per GPU | 1 | 8+ |
| External model invocation cost | 400K RMB/month | 200K RMB/month |
| Model failure recovery time | ~1 hour | <10 minutes |
| 3x peak traffic success rate | Unstable | 95%+ |
| R&D team size supported | Limited | 2000+ engineers |

### Challenges

#### Underutilized GPUs
Under the traditional model, an inference service exclusively occupies an entire GPU. Many workloads use only a fraction of the memory and compute yet hold a full GPU, causing severe resource fragmentation. GPUs were being scaled out faster than the business itself was growing.

#### Complex Resource Governance in Multi-Tenant Environments
The platform simultaneously serves multiple workloads such as AI Coding, digital employees, intelligent customer service, sales Agents, and enterprise knowledge assistants. Different workloads have very different GPU demands — some require long-resident memory, while others show peak-and-valley patterns. Unified resource pool management and fair allocation became a critical issue.

#### Coexistence of Inference and Batch Workloads
The platform concurrently runs online inference, batch inference, distributed training, and Agent workflows. Native Kubernetes GPU scheduling cannot meet the needs of these complex AI workloads.

### Solution: HAMi
“HAMi’s Kubernetes-native integration means zero migration cost. Transparent device virtualization lets workloads run without any modification.”
— Jia Haojie, Chief Architect of Cloud AI at Sangfor
Kubernetes provides a unified control plane for the AI platform, but native GPU scheduling allocates resources in whole-GPU units, making it hard to meet the needs of inference services, multi-tenancy, and heterogeneous GPU environments. Sangfor introduced Volcano and HAMi to address advanced scheduling and GPU resource virtualization respectively.
Core reasons for choosing HAMi:
- GPU sharing: memory granularity down to 256MB and compute down to 1%, with multiple Pods sharing a single GPU under strong isolation
- Heterogeneous GPU supports: a unified resource abstraction that keeps the scheduling experience consistent across multiple GPU generations
- Open-source ecosystem: one of the most active open-source vGPU projects in the Kubernetes space, continuously integrated with Volcano Queues and vLLM

#### Architecture
The platform has two layers. The Data Plane is the request path: after AI applications pass through the AI Computing Gateway for routing, governance, and security checks, they reach the model service layer (OpenAI / Claude / DeepSeek / local inference). The Component Architecture is the compute foundation: Volcano handles job scheduling, HAMi handles GPU virtualization and sharing/isolation, and Kubernetes manages nodes and device plugins, finally landing on heterogeneous GPUs such as NVIDIA and Ascend for execution. The two layers connect between Model Services and Volcano, completing the end-to-end chain from request to compute.

#### GPU Pooling: Before vs. After
Before the improvement, a dedicated mode was used — one card ran only one model: large models could still fill the memory, but small models used only 15–20%, leaving the rest idle. Large and small models could not coexist, causing severe resource fragmentation.
vGPU slicing delivers two core benefits:
- Large/small model co-location : on a single card the large model takes the lion’s share (e.g. 70%), and the remaining slices are given to multiple small models, soaking up compute that would otherwise sit idle.
- Small-model deployment density : a single card can host 8x or more small-model instances, significantly reducing the need to add more cards.
Overall result: GPU utilization improved by more than 3x, and per-card model density improved by more than 8x.

#### Volcano + HAMi: Coordinated Scheduling
GPU sharing alone is not enough for production. Volcano combined with HAMi enables unified management of device resources and job scheduling.
- Device state maintenance — GPU health monitoring, automatic fault isolation, and automatic resource reclamation
- Resource declaration governance — automatically fills in resource fields, computes quotas uniformly, and rejects invalid requests early
- Scheduling transaction isolation — decouples resource trial computation from actual occupancy, ensuring state consistency
- Gang and LWS support — Volcano orchestrates the job while HAMi allocates GPUs, scheduling the whole group together
Volcano decides when and where a workload runs , while HAMi decides how GPU resources are shared and allocated .

### Impact

#### GPU Utilization Up More Than 3x
With HAMi’s vGPU slicing, multiple inference services share a single GPU, with memory and compute allocated on demand. The shared GPU pool eliminates resource fragmentation, allowing more workloads to run on the same hardware.

#### Per-GPU Model Density Up More Than 8x
Inference workloads that previously needed 3 GPUs can now fit on 1–2 GPUs. With a minimum compute slice of 1% and a minimum memory slice of 1MB, each model gets a precise resource quota.

#### External Model Invocation Cost Down 50%
Combined with smart routing — simple questions routed to low-cost models and complex questions to premium models — the external model invocation cost dropped from 400K RMB/month to 200K RMB/month, while safety guardrails keep cost and quality optimally balanced.

#### Significantly Improved Platform Stability
Model failure recovery time was cut from 1 hour to under 10 minutes. Under 3x traffic stress testing, the success rate stayed above 95%. Device health monitoring and automatic fault isolation keep faulty GPUs out of the scheduling path.

#### Supporting a 2000+ R&D Team
The platform already supports multiple production scenarios including AI Coding, enterprise Agents, intelligent customer service, and digital employees, covering daily use by 2000+ R&D engineers.

# Lessons Learned

#### GPU Sharing Matters More Than Adding GPUs
Most inference workloads cannot fully use an entire GPU. Before buying more hardware, prioritize GPU sharing — the ROI is higher and the payoff is faster.

#### Decouple Scheduling from Resource Virtualization
HAMi handles resource abstraction; Volcano handles scheduling policy. Once decoupled, each layer can evolve independently. GPU sharing without smart scheduling leads to suboptimal placement; scheduling without GPU virtualization leaves nothing to schedule.

#### Kubernetes Is Becoming the AI Resource Control Plane
AI infrastructure is evolving along the cloud-native path rather than as a standalone resource management system. The combination of Kubernetes + Volcano + HAMi lets enterprises gain enterprise-grade GPU management without introducing a new management paradigm.

#### Looking Ahead
Sangfor will continue working with the HAMi community to drive Kubernetes toward becoming the unified control plane for AI workloads:
- Join the HAMi DRA ecosystem to advance Kubernetes-native GPU resource management
- Extend support for heterogeneous GPUs such as Ascend through HAMi’s unified abstraction
- Contribute production-grade scheduling policies and operational best practices back to the Volcano and HAMi communities
Learn more:
- HAMi GitHub Repository
- Volcano GitHub Repository
Projects used
By the numbers
More than 3×
Higher GPU utilization
More than 8×
More models running on each GPU
50%
Lower external model costs
Share
