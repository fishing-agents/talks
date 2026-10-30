---
theme: kcd_vietnam
title: HAMi Introduction
footer: HAMi - Heterogeneous AI Computing Virtualization Middleware
paginate: true
---

@variant dark
@kicker CNCF Sandbox Project

# HAMi

@subtitle Heterogeneous AI Computing Virtualization Middleware<br>Unified Management, Efficient Scheduling, Maximizing GPU Utilization

---

## The GPU Challenge

@subtitle Supply and demand are polarized

::: grid {cols=2}
::: card {tag=red}
### Supply Side

- Many GPU manufacturers (NVIDIA, AMD, Intel, Huawei Ascend)
- Specifications vary widely
- Centralized management is difficult
- Resource scheduling is rough
:::
::: card {tag=yellow}
### Demand Side

- GPU resources are scarce
- Users are cost-sensitive
- Inference demands are fragmented
- Utilization is often low
:::
:::

---

## GPU Management Pain Points

- {icon:server cls=accent-secondary} No resource pool, no overall scheduling, no management plane
- {icon:layers cls=accent-secondary} GPUs scattered, difficult to manage centrally
- {icon:lock cls=accent-secondary} No GPU sharing - 1 GPU per task minimum
- {icon:chart-bar cls=accent-secondary} Resource allocation is inflexible, cannot specify size/type
- {icon:triangle-alert cls=accent-secondary} No GPU over-division, wasted capacity

---

## What is HAMi

Heterogeneous AI Computing Virtualization Middleware

- {icon:zap cls=accent-primary} Pluggable, lightweight, deploys in any Kubernetes environment
- {icon:layers cls=accent-primary} Virtualizes heterogeneous AI chips (NVIDIA, Ascend, Cambricon, Hygon, Iluvatar)
- {icon:share cls=accent-primary} GPU sharing - multiple tasks share one GPU
- {icon:settings-2 cls=accent-primary} Rich scheduling strategies: binpack, spread, priority, topology-aware
- {icon:shield-check cls=accent-primary} CNCF Sandbox project, 80+ contributors, 100+ enterprise adopters

---

## HAMi Community

| Metric | Value |
|--------|-------|
| Contributors | 80+ |
| Enterprise adopters | 100+ |
| CNCF Status | Sandbox + CNAI Landscape |
| Focus | AI Infra + Heterogeneous AI Management |

The only open-source project focused on AI Infrastructure and heterogeneous AI management in CNCF.

---

## GPU Sharing

@subtitle Dynamic fine-grained device slicing

- **All NVIDIA series** supported
- **Fine-grained:** as small as 1MB device memory, 1% computing cores
- **Transparent to tasks** - no code changes required
- **Hard resource isolation** inside containers

HAMi provides device sharing by dynamic device slicing. A task allocates a portion of GPU, leaving the rest for other tasks.

---

## How GPU Sharing Works

HAMi-Core uses **symbolic hijacking** inside containers:

| Requirement | Specification |
|-------------|---------------|
| NVIDIA driver | >= 440 |
| CUDA | >= 10.2 |
| Device Memory isolation | Yes |
| Core utilization limit | Yes |
| Fault isolation | Yes |
| Transparent to GPU tasks | Yes |


---

## GPU Utilization Impact

By enabling GPU sharing, tasks that once idled at 30% now combine with other workloads:

```pdg
graph layout=row gap=0
used "70% Utilized" fill=#22c55e stroke=#166534 color=#ffffff width=420 height=56 font-weight=bold
idle "30% Idle" fill=#ef4444 stroke=#991b1b color=#ffffff width=180 height=56 font-weight=bold
```


---

## GPU Utilization Impact (Seaborn)

```seaborn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 1.2), dpi=100)
fig.patch.set_alpha(0)

green = "#22c55e"
red = "#ef4444"
dark = "#1e293b"

ax.barh(0, 70, color=green, height=0.6)
ax.barh(0, 30, left=70, color=red, height=0.6)

ax.axvline(x=70, color=dark, linewidth=2)
ax.annotate("▼", xy=(70, 0.42), fontsize=14, color=dark, ha="center", va="bottom")

ax.text(35, -0.02, "70% Utilized", ha="center", fontsize=12, color="#166534", fontweight="bold")
ax.text(85, -0.02, "30% Idle", ha="center", fontsize=12, color="#991b1b", fontweight="bold")

ax.set_xlim(0, 100)
ax.set_ylim(-0.6, 0.6)
ax.axis("off")
```


---

## GPU Sharing Parameters



- : memory size per GPU. Defaults to all available if not set
- : compute percentage per GPU. 0-100 range.

---

## Specify Device Type

HAMi supports targeting or avoiding specific GPU models:



Schedule tasks to specific GPU models or avoid certain types entirely.

---

## Scheduling Policies

::: grid {cols=2}
::: card {tag=cyan}
### {icon:arrow-up cls=accent-primary} Priority-based

High-priority pods pause lower-priority tasks. Set via  env var.
:::
::: card {tag=green}
### {icon:gauge cls=accent-contrast} Binpack & Spread

Binpack minimizes fragments. Spread distributes evenly across nodes/devices.

![Binpack vs Spread scheduling](assets/hami_intro/binpack_spread.png)
:::
:::

::: grid {cols=2}
::: card {tag=yellow}
### {icon:git-branch cls=accent-contrast} Topology-aware

NVLink-aware scheduling for multi-GPU efficiency. 25GB/s-1800GB/s vs PCIe 16GB/s.

![NUMA topology-aware scheduling](assets/hami_intro/topology_numa.png)
:::
::: card {tag=cyan}
### {icon:crosshair cls=accent-primary} Device-specific

Specify exact GPU models or specific device UUIDs for task placement.
:::
:::

---

## Memory Oversubscription

@layout compare

::: card {tag=compare}
### Before

23GB Device Memory hosts **1** 13B inference model
:::

::: arrow

{icon:arrow-right cls=accent-primary size=48}
:::

::: card {tag=compare}
### After

23GB Device + 46GB virtual memory hosts **3** 13B inference models
:::

GPU memory automatically swapped to host RAM for idle tasks. Typical scenario: model loading and inference serving.

---

## Observability

HAMi provides built-in monitoring dashboards (Grafana + Prometheus):

- **K8s scheduling dimension:** vGPU task bindings, task-to-GPU relationships
- **GPU device dimension:** real computing power and memory usage during runtime
- Community best-practice monitoring dashboard included

---

## HAMi vs Other Projects

| Feature | HAMi | NVIDIA device-plugin | NVIDIA DRA driver |
|---------|:---:|:---:|:---:|
| Multi-vendor GPUs | {icon:check cls=accent-primary} | {icon:x cls=accent-secondary} | {icon:x cls=accent-secondary} |
| GPU sharing | {icon:check cls=accent-primary} | {icon:check cls=accent-primary} | {icon:check cls=accent-primary} |
| Flexible scheduling | {icon:check cls=accent-primary} | {icon:x cls=accent-secondary} | {icon:x cls=accent-secondary} |
| Dynamic MIG | {icon:check cls=accent-primary} | {icon:x cls=accent-secondary} | {icon:x cls=accent-secondary} |
| Memory oversubscription | {icon:check cls=accent-primary} | {icon:x cls=accent-secondary} | {icon:x cls=accent-secondary} |
| Topology-aware | {icon:check cls=accent-primary} | {icon:x cls=accent-secondary} | {icon:x cls=accent-secondary} |
| Heterogeneous devices | {icon:check cls=accent-primary} | {icon:x cls=accent-secondary} | {icon:x cls=accent-secondary} |

---

## GPU Sharing Methods Compared

| Method | Multi-vendor | Isolation | Fragmentation | Overhead |
|--------|:---:|:---:|:---:|:---:|
| HAMi vGPU | {icon:check cls=accent-primary} | Strong | Low | Low |
| CUDA Streams | {icon:x cls=accent-secondary} | Weak | High | Low |
| MPS | {icon:x cls=accent-secondary} | Medium | Low | Medium |
| Time-slicing | {icon:x cls=accent-secondary} | Weak | High | Low |
| MIG | {icon:x cls=accent-secondary} | Strong | High | N/A |
| NVIDIA vGPU | {icon:x cls=accent-secondary} | Strong | Low | High |

---

## Applicable Scenarios

::: grid {cols=2}
::: card {tag=green}
### {icon:globe cls=accent-primary} Online Inference

10 services share one GPU. Activate on-demand, low-frequency services share resources. Significantly reduces GPU costs.
:::
::: card {tag=cyan}
### {icon:git-compare-arrows cls=accent-contrast} A/B Testing

Virtual GPU memory reduces hardware requirements. Original + experimental models share a single GPU.
:::
:::

::: grid {cols=2}
::: card {tag=yellow}
### {icon:refresh-cw cls=accent-contrast} Mixed Train/Infer

Inference gets priority, training fills gaps. When inference idle, cached training runs. Flexible queue-based scheduling.
:::
::: card {tag=cyan}
### {icon:zap cls=accent-primary} LLM Optimization

Multiple small models (embedding, reranker, generator) share GPUs. 4 threads → 8 threads on same hardware.
:::
:::

---

## Ecosystem Integrations

| Project | Integration |
|---------|-------------|
| Volcano | Batch scheduling for HPC/AI workloads (CNCF) |
| Koordinator | Colocation of microservices, AI, big data |
| KEDA | Event-driven autoscaling |
| Prometheus + Grafana | Monitoring and observability |
| Helm | One-command deployment |

---

## About HAMi

- {icon:git-fork cls=accent-primary} github.com/Project-HAMi/HAMi
- {icon:globe cls=accent-primary} project-hami.io
- {icon:users cls=accent-primary} 80+ contributors, 100+ enterprise adopters
- {icon:shield-check cls=accent-primary} CNCF Sandbox Project

Community edition is free and open-source. Enterprise edition available with additional features and support.

---

@kicker Thank You

# Questions?

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI  -  Makers of HAMi" github=github.com/fishman twitter=@rezajelveh
@speaker name="Anh Nguyen" role="Solutions Engineer, Viettel"
