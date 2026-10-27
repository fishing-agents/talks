<!-- source: https://www.cncf.io/case-studies/china-merchants-bank/
     published: 2026-07-02T17:20:27+00:00
     fetched: 2026-10-24 -->

# China Merchants Bank

## China Merchants Bank Improves AI Compute Scheduling on Kubernetes with HAMi

## Executive Summary
As AI workloads expanded across model training, inference services, R&D, and internal AI applications, China Merchants Bank needed a more efficient way to manage diverse accelerator resources at scale. Using Kubernetes and HAMi, the bank built a unified AI compute scheduling platform that enables heterogeneous resource pooling, topology-aware scheduling, and fine-grained accelerator sharing. The result was improved hardware utilization, reduced distributed training communication overhead, and a more scalable foundation for enterprise AI workloads.
Projects used
By the numbers
100%
Hardware pool utilization through topology-aware scheduling
30%
Reduction in cross-machine scheduling for distributed training workloads
1 GB / 1%
Smallest accelerator partitioning unit for memory and compute allocation

## About China Merchants Bank
China Merchants Bank is one of China’s leading commercial banks, investing heavily in cloud-native, AI, and digital infrastructure. As AI has become central to more financial use cases, the bank needs to run a wide range of training, inference, and internal AI workloads, which puts real pressure on the underlying computing platform.

## The Challenges
Large model training, inference services, and AI applications are growing fast. For most large organizations, the real bottleneck isn’t a lack of compute. It’s getting existing resources to work together efficiently.
China Merchants Bank ran into this exact problem. The bank had built a heterogeneous compute platform using various AI accelerator cards for model training, online inference, R&D, and internal AI tools. As usage grew, the old way of managing resources couldn’t keep up. So the bank built a new unified scheduling platform on Kubernetes with HAMi, bringing heterogeneous resource management, topology-aware scheduling, and fine-grained sharing under one roof.
Building an enterprise AI platform at this scale came down to three problems:

### Fragmented Resource Management
Different AI accelerator vendors ship their own software stacks and management tools. The result: siloed resource pools, inconsistent scheduling policies, and growing operational overhead.

### Training Hardware Not Fully Utilized
Some training nodes use multi-chip high-speed interconnects, where task placement is very sensitive to physical chip topology. If the scheduler doesn’t understand that topology, tasks land on the wrong chips, hurting performance or failing outright.

### Wasted Capacity on Small Tasks
Lots of inference, fine-tuning, and test jobs don’t need a whole accelerator card. But the conventional approach allocates cards in full, leaving a lot of capacity idle.

## Why HAMi
The bank picked HAMi for a few reasons:
- Works natively on Kubernetes. No need to restructure the existing cloud-native stack.
- Unifies heterogeneous resources. Multiple accelerator types share one scheduling framework.
- Supports fine-grained sharing. Memory and compute can be split with quota controls, squeezing more utility out of each card.
- Open-source and extensible. The architecture is open and can be adapted to real business needs.

## The Solution
China Merchants Bank built its unified AI compute platform on Kubernetes and HAMi, then iterated on resource onboarding, shared scheduling, and training efficiency.

### Platform Architecture
The platform has three layers:
- Business Service Layer: Large-scale model training, AI inference services, model fine-tuning, and internal AI applications.
- HAMi Scheduling Layer: Heterogeneous resource pooling, topology-aware scheduling, GPU/NPU sharing, multi-vendor device abstraction
- Infrastructure: Multi-vendor AI accelerator cards, multi-node clusters, high-speed interconnect networks

### Unified Heterogeneous Resource Management
HAMi lets the bank pool many different types of accelerator cards into one unified Kubernetes resource pool. In China Merchants Bank’s environment, this is especially important because the platform includes a wide range of heterogeneous compute resources, including Kunlunxin, multiple Ascend models, NVIDIA GPUs, PPUs, Moore Threads, MetaX, and other accelerator devices. Without HAMi, each hardware delivery would typically come with its own independent Kubernetes cluster, which could require the bank to maintain more than eight separate clusters, each with its own device plugins, scheduling policies, monitoring stack, operational procedures, and troubleshooting model.
With HAMi, these heterogeneous devices can be managed through a single scheduling framework and a consistent set of platform policies. Application teams continue to request resources through standard Kubernetes workflows, while the platform team can abstract away differences in device type, vendor stack, and resource allocation model. HAMi’s value is not limited to device slicing and monitoring. The project also provides vendor-specific best practices and example workloads, allowing the bank to quickly validate newly onboarded devices through HAMi examples before moving them into production use.

### Topology-Aware Scheduling: Fitting the Supernode Architecture
Some training nodes use a supernode (dual-chip module) architecture , where multiple chips are connected via high-speed interconnects to form a single logical unit. The default Kubernetes scheduler doesn’t understand this layout, and that caused real trouble:
- Odd-card allocation breaks things. Allocating an odd number of cards can span two modules, which triggers driver errors.
- Cross-module traffic is slow. Communication between modules has noticeably higher latency than within a module.
- Parts of the cluster sit idle. Bad placement decisions meant some hardware was effectively unusable.
The bank enhanced HAMi’s Device Plugin and scheduler to recognize physical modules and enforce paired allocation. The scheduler now understands the module topology and keeps cards within the same module, avoiding the driver crashes that came from odd-card cross-module placement. Hardware pool utilization went to 100%.
In a ResNet50 inference benchmark (batch size = 32), HAMi’s fine-grained compute partitioning increased total single-card throughput from 64.6 images/s to 94.8 images/s. As partition granularity increased, overall throughput improved by up to 46.7%, demonstrating higher workload density and better accelerator utilization.
Figure 1: Supernode module paired allocation. The scheduler understands the physical module layout and allocates cards within the same module.
The bank also improved how the system handles multi-chip high-speed interconnect nodes. It now understands inter-chip connectivity and prioritizes placing training tasks where the communication paths are shortest, which makes training more stable and faster.

### Fine-Grained Sharing: vNPU-Core Software Partitioning
Inference, small model fine-tuning, and R&D test jobs often don’t need a full card. Handing out whole cards for these workloads wastes a lot of capacity.
The bank used HAMi’s VMPO Core component to do user-space compute partitioning . The two main mechanisms are:
- Token bucket. Each task gets a compute quota. Tasks that exceed their limit queue up and wait their turn.
- User-space memory management. GPU memory allocation happens in user space, making fine-grained partitioning possible.
Figure 2: vNPU-Core user-space compute partitioning. Token bucket controls compute quotas; user-space manages memory allocation.
Partitioning can go as fine as 1 GB memory / 1% compute , and can be mixed and matched per task. That matters a lot in banking. Risk control models and customer service models tend to be small. They don’t need a full card, and fine-grained partitioning lets the bank run many more of them on the same hardware.
For inference, small model training, and R&D testing, the bank also turned on card sharing so multiple tasks can share a single accelerator card. This enabled multiple workloads to share a single accelerator card and reduced idle capacity for smaller inference and testing workloads.

### Network Topology: Three-Layer Abstraction and Anti-Dispersion
For distributed training, the bank designed a multi-level topology-aware scheduling algorithm that treats the physical network as three tiers:
- Level 1: Same Node. Lowest latency, highest scheduling priority.
- Level 2: Same LEAF Switch. Moderate latency, medium priority.
- Level 3: Cross LEAF Switch. Highest latency, lowest priority.
Figure 3: Three-layer network topology scheduling. Tasks are prioritized by same-node, same-LEAF, and cross-LEAF placement.
The scheduler now adds topology scores during its ranking phase, preferring to place high-communication tasks on the same node or within the same switch domain. Cross-machine scheduling dropped by 30% , which cut down a major communication bottleneck in distributed training.
The bank also noticed that the scheduler would sometimes scatter pods from the same job across different nodes. To fix this, it introduced a controller UID-based deterministic hashing mechanism that keeps pods from the same batch grouped together on the same node.

## Key Results
Here’s what the bank got out of these changes:
| Metric | Result |
| Hardware pool utilization | 100% |
| Cross-machine scheduling probability | Down 30% |
| Finest partitioning granularity | 1 GB memory / 1% compute |
| Platform architecture | Unified heterogeneous AI compute scheduling |
Table 1: Key metrics from the China Merchants Bank AI compute platform
These changes let the bank handle growing AI workloads without constantly buying more hardware.
Through HAMi, we built a unified heterogeneous AI compute scheduling platform on Kubernetes, achieving significant improvements in resource utilization, training efficiency, and platform stability.

## Why This Matters
China Merchants Bank’s story shows that the real competitive edge in AI infrastructure isn’t buying more hardware. It’s using software to get more value out of the hardware you already have.
For the cloud-native world, this is a meaningful step for Kubernetes. It’s no longer just orchestrating containers. It’s becoming the control plane for enterprise AI infrastructure.
Open-source projects like HAMi give enterprises heterogeneous scheduling, sharing, and orchestration on top of Kubernetes, making it possible to build AI platforms faster without reinventing the wheel.

## Looking Ahead
The bank plans to continue evolving its AI compute platform. Key priorities include further optimizing the Ascend hami-vnpu-core software partitioning mechanism to reduce performance variability in multi-workload environments, and building comprehensive monitoring capabilities for virtualized NPUs to provide real-time visibility into memory and compute utilization. China Merchants Bank also plans to remain an active contributor to the HAMi open-source community, sharing operational experience and helping advance heterogeneous AI infrastructure technologies.

## Summary
China Merchants Bank’s experience demonstrates how Kubernetes and HAMi can provide a unified foundation for managing heterogeneous AI infrastructure at enterprise scale. By improving resource utilization, optimizing workload placement, and enabling fine-grained resource sharing, the bank has built a more efficient and scalable platform to support growing AI initiatives across the organization.
Share
