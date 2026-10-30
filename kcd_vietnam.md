---
theme: kcd_vietnam
title: "From Project to Production: HAMi and Viettel Cloud"
footer: HAMi x Viettel Cloud - KCD Vietnam 2026
paginate: true
transition: fade
style: |
  img[alt="Certified Kubernetes - AI Platform"] { max-height: 56vh; width: auto; display: block; margin: 0 auto 0.4em; }
  img[alt="badge"] { display: inline-block !important; height: 3em; width: auto; margin: 0 0.5em 0 0 !important; vertical-align: middle; }
  .slide-body:has(img[alt="Certified Kubernetes - AI Platform"]) { position: relative; }
  .slide-body:has(img[alt="Certified Kubernetes - AI Platform"]) p:last-child { position: absolute; bottom: 1.2em; left: 13.5em; margin: 0; }
---

@variant dark
@kicker A CNCF Incubation Project

# HAMi and Viettel Cloud: From Project to Production

@subtitle Fractional GPU Virtualization for Multi-tenant AI Workloads
@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI  -  Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh
@speaker name="The Anh Nguyen" role="Software Engineer, Viettel Networks  -  CNCF Kubestronaut" github=github.com/ntheanh201 linkedin=linkedin.com/in/ntheanh201

---

# Part 1: The Problem

@subtitle GPU underutilization, atomic allocation, multi-tenant contention

---

@layout image-right

## The Problem

@subtitle Atomic GPU allocation wastes silicon

Kubernetes allocates GPUs atomically. DRA + HAMi fix this.

- 1 GB task blocks an 80 GB device
- Over-provisioning is the default: idle silicon
- DRA can request GPUs but requires MIG to slice
- Why HAMi if DRA slices? We'll get to that

![Device Plugin vs DRA](assets/hami/device-plugin-vs-dra.png)

---

## What is HAMi

@subtitle Static allocation, one GPU per task

<!--
GPUs are expensive and often underutilized. HAMi is a heterogeneous GPU sharing framework for Kubernetes. It lets you slice and share GPUs across workloads, maximizing utilization without rewriting your entire stack.
-->

![Before HAMi](assets/hami_intro/before-hami.png)

---

## What is HAMi
@transition none

@subtitle Fractional vGPUs, multiple tasks per device

![After HAMi](assets/hami_intro/after-hami.png)

---

@layout compare

## The GPU Challenge

@subtitle What breaks, what we need

::: card {tag=compare}
### Problem

- GPUs are scarce, allocated whole
- Vendors locked in, supply tight
- Utilization stuck at 10%
- No central observability
- Fragmented inference workloads
:::

::: arrow

{icon:arrow-right cls=accent-primary size=48}
:::

::: card {tag=compare}
### Requirements

- Hardware agnostic: one API, any accelerator
- Fractional GPU: fine-grained slices, multiple tasks per device
- Advanced scheduling: binpack, spread, topology-aware
- Unified observability across vendors
:::

<!--
Heterogeneous GPU sharing means you can run NVIDIA A100s, H100s, Ascend or other devices on the same cluster without manual partitioning. HAMi handles the scheduling logic. The real work is memory isolation.
-->

::: notes{ tag="green" }
Unified observability, 50% GPU utilization, 10x workloads running, 10x GPU availability. AMD MI355X: 80% of B200 perf at ~1/3 the cost. Not everyone needs Vera Rubin.
:::

---

# Part 2: The Solution

@subtitle Fractional GPU allocation and scheduling

---

## DRA Feature Timeline

@subtitle KEPs and their development status: we won't cover this today

<!--
Backup slide. Shows all DRA KEPs and their dev status. Mention that DRA is moving fast -- 1.34 stable. We will skip this but it is here for questions.
-->

![DRA Feature Timeline](assets/hami/dra-feature-timeline.png)

---

@layout image-right

## DRA: ResourceSlice

@subtitle Per-node device inventory

<!--
DRA drivers run on each node and publish available devices. The scheduler reads ResourceSlices to find nodes that can satisfy a claim. This is how the scheduler knows what hardware is free.
-->

![ResourceSlice](assets/hami/dra-resource-slice.png)

- **ResourceSlice:** lists all available devices on a node with their attributes
- DRA drivers publish slices; scheduler reads them to match claims to devices
- Tied to a node via `nodeName`, supports topology and NUMA attributes

---

@layout image-right

## DRA: ResourceClaim

@subtitle A standardized way to request hardware: not just GPUs. Stable in K8s 1.34.

<!--
DeviceClass defines a category of devices by capability. ResourceClaim requests specific hardware from that category. ResourceClaimTemplate creates a claim per pod automatically. Together these replace the old device plugin model.
-->

![ResourceClaim and ResourceClaimTemplate](assets/hami/dra-resource-claim.png)

- **DeviceClass:** groups devices with identical resource models. **ResourceClaim:** a workload's ticket to hardware. **ResourceClaimTemplate:** reusable blueprint, auto-creates a claim per Pod.

---

## HAMi Capabilities

@subtitle Six things HAMi brings to GPU scheduling

<!--
Six capabilities. The key ones for this talk: hard isolation, advanced scheduling, and unified monitoring. Heterogeneous management is the differentiator -- not just NVIDIA.
-->

::: grid {cols=2}
::: card
### {icon:layers cls=accent-primary} Heterogeneous Management

Manage GPU, NPU, MLU, and other accelerators in one workflow.
:::
::: card
### {icon:shield-check cls=accent-primary} Hard Isolation

Slice memory and compute with hard isolation at runtime.
:::
::: card
### {icon:git-branch cls=accent-contrast} Advanced Scheduling

Binpack, spread, and topology-aware placement policies.
:::
::: card
### {icon:box cls=accent-primary} Kubernetes Native

Kubernetes-native APIs, DRA, and CDI support.
:::
::: card
### {icon:gauge cls=accent-primary} Resource Isolation & QoS

Memory and core quotas for fair, stable sharing.
:::
::: card
### {icon:chart-bar cls=accent-contrast} Unified Monitoring

Consistent metrics and visibility across vendors.
:::
:::


---

@layout two-col

## How HAMi Works

@subtitle Pod creation to GPU isolation

<!--
Seven stages from pod submission to isolated GPU. The mutating webhook injects the request, the HAMi core library enforces isolation via symbolic hijacking: no kernel modules.
-->

HAMi intercepts pod creation and GPU allocation through seven stages:

- **Mutating webhook:** detects GPU requests, routes pod to HAMi scheduler
- **Scheduler:** selects GPU and node via HAMi scheduler extender
- **HAMi driver:** generates device config
- **Container runtime:** reads config, injects HAMi-Core library
- **HAMi core:** enforces isolation in-process via symbolic hijacking

@col

```pdg
graph dir=TB order=source
pod "Pod submitted" shape=round fill=#F6ECD9 stroke=#F1C560 color=#3a2020 rank=0
webhook "Mutating webhook" shape=round fill=#fce8e8 stroke=#7A0504 color=#3a2020 rank=1
sched "Scheduler" shape=round fill=#fce8e8 stroke=#7A0504 color=#3a2020 rank=2
device "HAMi driver" shape=round fill=#fce8e8 stroke=#7A0504 color=#3a2020 rank=3
runtime "Container runtime" shape=round fill=#F6ECD9 stroke=#F1C560 color=#3a2020 rank=0
core "HAMi core" shape=round fill=#fce8e8 stroke=#7A0504 color=#3a2020 rank=1
workload "Workload (isolated GPU)" shape=round fill=#F6ECD9 stroke=#F1C560 color=#3a2020 rank=2
pod -> webhook "set scheduler"
webhook -> sched "select GPU+node"
sched -> device "allocate device"
device ..> runtime "device config" constraint=false
runtime -> core "enforce isolation"
core -> workload "sees isolated GPU"
```

---

@layout two-col

## GPU Sharing

@subtitle Dynamic fine-grained device slicing

<!--
Same YAML across vendors. Ascend example on the right. Memory is hard limit, cores are best-effort. This is what users actually write.
-->

- **NVIDIA, Ascend, Cambricon, Hygon, Iluvatar** supported
- **Fine-grained:** as small as 1MB device memory, 1% computing cores
- **Transparent to tasks:** no code changes required
- **Hard resource isolation** inside containers
- One API across vendors: same YAML, any accelerator

@col

```yaml
# Ascend 910C: 8GB + 20% compute
resources:
  limits:
    huawei.com/Ascend910C: "1"
    huawei.com/Ascend910C-core: "20"
    huawei.com/Ascend910C-memory: "8192"
```

```yaml
# NVIDIA: 3GB on any GPU
resources:
  limits:
    nvidia.com/gpu: 1
    nvidia.com/gpumem: 3000
```


---

## GPU Utilization Impact
@hidden

@subtitle Idle tasks swap to host RAM

Idle tasks swap to host RAM, freeing device memory for active workloads:

::: card
```seaborn
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(8, 2.8))

fg = plt.rcParams["text.color"]
dimmed = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
danger = cmap(4.5 / 12)
danger_bright = cmap(5 / 12)
elastic = cmap(2.5 / 12)
base = cmap(0.5 / 12)
ax.set_facecolor("none")
fig.patch.set_alpha(0)

r = 0.14
bs = f"round,pad={r}"

# Row 1: base=8, spike=3
ax.barh(1, 8, color=base, height=0.65)
ax.barh(1, 3, left=8, color=danger, height=0.65)
ax.plot([10, 10], [0.62, 1.38], color=danger, linewidth=2.5, solid_capstyle="butt")

# Row 2: base=8, spike=7
ax.barh(0, 8, color=base, height=0.65)
ax.barh(0, 7, left=8, color=elastic, height=0.65)
ax.plot([10, 10], [-0.38, 0.38], color=fg, linewidth=1.5, linestyle="--")
ax.plot([15, 15], [-0.38, 0.38], color=fg, linewidth=1.5, linestyle="--")

ax.set_xlim(0, 15.2)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

ax.text(0, 1.38, "Without HAMi", ha="left", va="bottom", fontsize=10, color=fg, fontweight="bold")
ax.text(0, 0.38, "With HAMi: Elastic Scaling", ha="left", va="bottom", fontsize=10, color=fg, fontweight="bold")

ax.text(4, 1, "Normal base load", ha="center", va="center", fontsize=9, color=fg, fontweight="bold")
ax.text(9.5, 1, "Traffic spike", ha="center", va="center", fontsize=7.5, color=dimmed, fontweight="bold")
ax.text(10, 1.42, "10 GB limit", ha="center", va="bottom", fontsize=8, color=danger_bright, fontweight="bold")

ax.text(4, 0, "Normal base load", ha="center", va="center", fontsize=9, color=fg, fontweight="bold")
ax.text(11.5, 0, "Traffic spike", ha="center", va="center", fontsize=7.5, color=dimmed, fontweight="bold")
ax.text(10, -0.42, "10 GB\nsoft limit", ha="center", va="top", fontsize=7.5, color=dimmed)
ax.text(15, -0.42, "15 GB\nburst", ha="center", va="top", fontsize=7.5, color=dimmed)
```
:::

:::card
```seaborn
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 2.8))

fg = plt.rcParams["text.color"]
dimmed = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
green = cmap(2.5 / 12)
blue = cmap(0.5 / 12)
red = cmap(4.5 / 12)
grey = "#9ca3af"
sleep_bg = "#374151"

ax.set_facecolor("none")
fig.patch.set_alpha(0)

# Top: IDLE(25) + EXECUTING(50) + IDLE(25)
ax.barh(1, 25, color=grey, height=0.65)
ax.barh(1, 50, left=25, color=green, height=0.65)
ax.barh(1, 25, left=75, color=grey, height=0.65)

# Bottom: EXECUTING(25) + SLEEP(50) + EXECUTING(25)
ax.barh(0, 25, color=blue, height=0.65)
ax.barh(0, 50, left=25, color=sleep_bg, height=0.65)
ax.barh(0, 25, left=75, color=blue, height=0.65)

# Segment dividers
for x in [25, 75]:
    ax.plot([x, x], [0.62, 1.38], color=fg, linewidth=0.8, linestyle="--")
    ax.plot([x, x], [-0.38, 0.62], color=fg, linewidth=0.8, linestyle="--")

ax.set_xlim(0, 100)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

# Side labels
ax.text(0, 1.38, "HIGH PRIORITY", ha="left", va="bottom", fontsize=10, color=green, fontweight="bold")
ax.text(0, 0.38, "LOW PRIORITY", ha="left", va="bottom", fontsize=10, color=blue, fontweight="bold")

# Top bar labels
ax.text(12.5, 1, "IDLE", ha="center", va="center", fontsize=9, color=fg)
ax.text(50, 1, "EXECUTING", ha="center", va="center", fontsize=9, color=fg, fontweight="bold")
ax.text(87.5, 1, "IDLE", ha="center", va="center", fontsize=9, color=fg)

# Bottom bar labels
ax.text(12.5, 0, "EXECUTING", ha="center", va="center", fontsize=9, color=fg)
ax.text(50, 0, "SLEEP", ha="center", va="center", fontsize=9, color=red, fontweight="bold")
ax.text(87.5, 0, "EXECUTING", ha="center", va="center", fontsize=9, color=fg)

ax.text(50, -0.35, "CUDA-KERNEL BOUNDARY", ha="center", va="top", fontsize=7, color=red)
```
:::

---

## Priority Preemption

@subtitle High priority pauses low priority at kernel boundaries

<!--
HIGH PRIORITY tasks preempt LOW PRIORITY at CUDA kernel boundaries. No wasted compute. The kernel boundary is the key -- you cannot preempt mid-kernel.
-->
@hidden

High-priority tasks preempt low-priority ones at CUDA kernel boundaries: no wasted compute, clean context switch:

:::card
```seaborn
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 2.8))

fg = plt.rcParams["text.color"]
dimmed = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
green = cmap(2.5 / 12)
blue = cmap(0.5 / 12)
red = cmap(4.5 / 12)
grey = "#9ca3af"
sleep_bg = "#374151"

ax.set_facecolor("none")
fig.patch.set_alpha(0)

# Top: IDLE(25) + EXECUTING(50) + IDLE(25)
ax.barh(1, 25, color=grey, height=0.65)
ax.barh(1, 50, left=25, color=green, height=0.65)
ax.barh(1, 25, left=75, color=grey, height=0.65)

# Bottom: EXECUTING(25) + SLEEP(50) + EXECUTING(25)
ax.barh(0, 25, color=blue, height=0.65)
ax.barh(0, 50, left=25, color=sleep_bg, height=0.65)
ax.barh(0, 25, left=75, color=blue, height=0.65)

# Segment dividers
for x in [25, 75]:
    ax.plot([x, x], [0.62, 1.38], color=fg, linewidth=0.8, linestyle="--")
    ax.plot([x, x], [-0.38, 0.62], color=fg, linewidth=0.8, linestyle="--")

ax.set_xlim(0, 100)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

# Side labels
ax.text(0, 1.38, "HIGH PRIORITY", ha="left", va="bottom", fontsize=10, color=green, fontweight="bold")
ax.text(0, 0.38, "LOW PRIORITY", ha="left", va="bottom", fontsize=10, color=blue, fontweight="bold")

# Top bar labels
ax.text(12.5, 1, "IDLE", ha="center", va="center", fontsize=9, color=fg)
ax.text(50, 1, "EXECUTING", ha="center", va="center", fontsize=9, color=fg, fontweight="bold")
ax.text(87.5, 1, "IDLE", ha="center", va="center", fontsize=9, color=fg)

# Bottom bar labels
ax.text(12.5, 0, "EXECUTING", ha="center", va="center", fontsize=9, color=fg)
ax.text(50, 0, "SLEEP", ha="center", va="center", fontsize=9, color=red, fontweight="bold")
ax.text(87.5, 0, "EXECUTING", ha="center", va="center", fontsize=9, color=fg)

ax.text(50, -0.35, "CUDA-KERNEL BOUNDARY", ha="center", va="top", fontsize=7, color=red)
```
:::

---

## Memory Oversubscription
@hidden

<!--
23 GB device + 46 GB virtual = 3x models. GPU memory swapped to host RAM for idle tasks. Works for model loading and inference, not for active training.
-->

@subtitle 23 GB device + 46 GB virtual = 3x models

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

::: notes{ tag="green" }
GPU memory automatically swapped to host RAM for idle tasks. Typical scenario: model loading and inference serving.
:::

---

## GPU Sharing Parameters

@subtitle Fine-grained control per task
@hidden

- : GPU memory size, defaults to all available
- : compute percentage, 0-100

---

@layout image-right

## Scheduling Policies

@subtitle Binpack & Spread

<!--
Two axes, four patterns. Node binpack saves money, node spread saves uptime. GPU binpack saves whole GPUs for training, GPU spread saves tail latency. Pick based on workload: training wants binpack, inference with SLOs wants spread.
-->

![Binpack vs Spread scheduling](assets/hami_intro/binpack_spread.png)

- **Node binpack** frees whole machines: reduces cost, helps cluster autoscaler
- **Node spread** isolates faults: HA across zones, blast radius control
- **GPU binpack** prevents fragmentation: frees entire GPUs for training
- **GPU spread** protects tail latency: reduces HBM and NVLink contention
- Advanced scheduling works with standalone HAMi; DRA mode can use Yunikorn

---

@layout image-right

## Scheduling Policies

@subtitle Topology-Aware

<!--
NVLink vs PCIe is a 7-14x bandwidth gap. HAMi schedules multi-GPU workloads to NVLink-connected pairs, avoids PCIe bridge pairs. Ascend uses HCCS, other vendors have their own high-speed interconnects: same topology logic applies. This matters for tensor parallelism and large-model training.
-->

![NUMA topology-aware scheduling](assets/hami_intro/topology_numa.png)

- **NVLink 3 (A100):** 600 GB/s, 12 links
- **NVLink 4 (H100/H200):** 900 GB/s bidirectional across 18 links
- **NVLink 5 (B200/B300):** 1.8 TB/s, 14x PCIe 5.0
- **NVLink 6 (Rubin):** ~3.6 TB/s target
- **PCIe 5.0 x16:** 128 GB/s. **PCIe 6.0:** 242 GB/s
- **HAMi topology policy:** prefers NVLink (NVIDIA), HCCS (Ascend), and other high-speed interconnects, avoids PCIe bridge pairs

---



## GPU Sharing Approaches

@subtitle MIG vs HAMi vs HAMi+DRA vs NVIDIA DRA

<!--
Common question: why not just use MIG? MIG doesn't work on all devices. You need to manually load MIG templates. HAMi does it automatically based on workload choice. NVIDIA's DRA driver has limited slicing. DRA itself still lacks advanced scheduling.
-->

| Capability | MIG | HAMi | HAMi+DRA | NVIDIA DRA |
|------------|:---:|:---:|:---:|:---:|
| Pre-configured templates | {icon:x cls=accent-secondary} | {icon:check cls=accent-primary} | {icon:check cls=accent-primary} | {icon:check cls=accent-primary} |
| Dynamic MIG repartition | {icon:x cls=accent-secondary} | {icon:check cls=accent-primary} | {icon:check cls=accent-primary} | {icon:check cls=accent-primary} |
| Symbolic hijacking | {icon:x cls=accent-secondary} | {icon:check cls=accent-primary} | {icon:check cls=accent-primary} | {icon:x cls=accent-secondary} |
| Consumable capacities | {icon:x cls=accent-secondary} | {icon:check cls=accent-primary} | {icon:check cls=accent-primary} | {icon:x cls=accent-secondary} |
| Multi-vendor | {icon:x cls=accent-secondary} | {icon:check cls=accent-primary} | {icon:check cls=accent-primary} | {icon:x cls=accent-secondary} |
| Advanced scheduling | {icon:x cls=accent-secondary} | {icon:check cls=accent-primary} | {icon:x cls=accent-secondary} | {icon:x cls=accent-secondary} |

NVIDIA DRA supports MIG, MPS, and VFIO passthrough with dynamic repartitioning. HAMi differentiates with symbolic hijacking for sub-MIG slicing (1MB), consumable capacities for flexible resource requests, and multi-vendor support. HAMi-DRA supports multiple DRA drivers. Its NVIDIA driver builds on NVIDIA's upstream, adding consumable capacities.

---

# Part 3: Viettel Cloud

@subtitle What we measured, what broke, and what we learned

---

## Who We Are

@subtitle Viettel Cloud, the AI Platform, and the GPU-sharing slice we'll cover

<!--
Lead, AI/GPU Platform = 'Viettel Cloud AI-Native'
Viettel Cloud = Viettel Group cloud, largest telco in Vietnam
we give our engineers AI Notebooks with fractional GPU
GPUs are MIXED: 1 pool H200 + pools L40/L40S/A30/A6000 - remember, it matters later
DON'T read the cert list. one sentence, then move.
-->

::: grid {cols=2}
::: card {tag=cyan}
### The Anh Nguyen

Software Engineer, Viettel Networks

- Technical lead, **Viettel AI / GPU Platform**
- **CNCF Kubestronaut**
- **NVIDIA Certified Professional**, AI Ops
- **CNCF Glossary** VN Lead, **SIG Docs VI** approver
- **Kubernetes & HAMi** member
:::
::: card {tag=green}
### Viettel Cloud

Cloud platform of Viettel Group, Vietnam's largest telco.

- **Viettel Cloud AI-Native** - the AI / GPU platform
- **AI Notebooks with fractional GPU** - dev & training
- Also **inference serving**
- **H200** pool (141 GB), plus **L40, L40S, A30, A6000, ...**
:::
:::

---

## Certified Kubernetes AI Platform

@subtitle 31 platforms in the world have it. We are one.

<!--
CNCF Certified K8s AI Platform - 31 in the world
AWS, Google, Azure, Oracle, Red Hat... and Viettel - we are #20
first & only in Vietnam
POINT at the Viettel logo, then GO. don't linger.
-->

![Certified Kubernetes - AI Platform](assets/kcd_vietnam/certified-k8s-ai-platform.png)

![badge](assets/kcd_vietnam/ai-conformance-badge.png) Our **AI Platform** - **first & only in Vietnam**, #**20** worldwide.

---

## What We Run Today

@subtitle HAMi in our clusters

<!--
HAMi 2.9 on BOTH clusters (H200 + mixed) - engineers use it daily
memory is real: pod sees 2 GB, not 141
next to Slinky/inference/KEDA - 2 schedulers, no conflict
per-pod GPU metrics (DCGM can't - only per physical GPU)
users write YAML: gpumem = HARD, gpucores = best-effort
researchers just pick the size in AI Notebooks UI (Kubeflow)
numbers in this talk: mostly H200, a few L40
-->

- {icon:server cls=accent-primary} **HAMi v2.9** on **both clusters**: the H200 pool, and the mixed-GPU one
- {icon:users cls=accent-primary} Our own engineers use it every day
- {icon:lock cls=accent-primary} The memory limit is real: pod sees **2 GB, not 141 GB**
- {icon:git-branch cls=accent-primary} Lives next to **Slinky, Inference, KEDA**
- {icon:chart-bar cls=accent-primary} Full monitoring, down to **per-pod GPU metrics**

This is all a user writes:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
    nvidia.com/gpumem: 2000   # MB - a hard limit
    nvidia.com/gpucores: 30   # % - best effort
```

Our researchers do not write that - they pick the GPU size in our **AI Notebooks**, built on **Kubeflow Notebooks**.

Numbers in this talk: mostly the **H200 pool**, a few from **L40**.

---

## The Problem We Measured

@subtitle Asking for a GPU is not the same as using it

<!--
2 jobs, each held a WHOLE H200 (141 GB)
1) Chronos forecast (infra load), ~200M params -> 1 GB / 141, compute 16-18%
2) YOLO11 training, cabinet damage, 17k images -> 39 GB
why only 39? batch = ACCURACY not memory; busy ~90%; data pipeline blocks first
=> 39 GB is the RIGHT size -> ~100 GB spare is real
[pause] many GPUs have NO MIG (L40/L40S/A6000) - slicing not even a choice
K8s gives one option: nvidia.com/gpu:1 - whole card or nothing
don't rush the '1 GB out of 141'
-->

Two real jobs. Each one held **a whole H200, 141 GB**:

```seaborn
import matplotlib.pyplot as plt

FG, DIM = "#3a2020", "#7a6a5a"
RED, YELLOW, GREY = "#e61e24", "#f4a93a", "#e0e0df"

fig, ax = plt.subplots(figsize=(10.5, 3.0))
ax.set_facecolor("none")
fig.patch.set_alpha(0)

ax.text(-40, 1.75, "GPU MEMORY  -  ALLOCATED VS USED", fontsize=10.5, color=DIM, family="monospace")

ax.barh(1, 141, color=GREY, height=0.5)
ax.barh(1, 1, color=RED, height=0.5)
ax.barh(0, 141, color=GREY, height=0.5)
ax.barh(0, 39, color=YELLOW, height=0.5)

ax.text(-4, 1, "Time-series\n(inference)", ha="right", va="center", fontsize=12.5, color=FG, fontweight="bold", linespacing=1.4)
ax.text(-4, 0, "Defect detection\n(training)", ha="right", va="center", fontsize=12.5, color=FG, fontweight="bold", linespacing=1.4)

ax.text(6, 1, "1 GB used  -  SM 16-18%", ha="left", va="center", fontsize=12, color=FG)
ax.text(44, 0, "39 GB used", ha="left", va="center", fontsize=12, color=FG)

ax.text(141, 1.42, "one whole H200 = 141 GB", ha="right", va="bottom", fontsize=11, color=DIM)

ax.annotate("", xy=(139, -0.55), xytext=(41, -0.55),
            arrowprops=dict(arrowstyle="<->", color=DIM, linewidth=1.4))
ax.text(90, -0.74, "100 GB free  →  inference  -  notebooks  -  CV / embedding",
        ha="center", va="top", fontsize=11, color=FG, fontweight="bold")

ax.set_xlim(-40, 148)
ax.set_ylim(-1.15, 1.95)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.set_xticks([])
```

- The time-series job leaves **140 GB and 80% of the GPU** doing nothing
- Detection training took **39 GB** - it still left most of the card unused
- **Many of our GPUs have no MIG:** L40, L40S, A6000, ...

> Kubernetes gives you one choice: `nvidia.com/gpu: 1`. The whole card, or nothing.

---

## The Result: 3.4x More Work Per GPU

@subtitle Fix the SLA, scale replicas, fill the empty GPU

<!--
Native 20.7 @18% | slice 19.6 (noise) | +KEDA 10 replicas -> 71.1 @ same 160ms
=> ~3.5 cards natively; HAMi does it on 1 -> 70% fewer cards, ~half power
LAND: HAMi FILLS the empty GPU - it does NOT make one pod faster
team: unfair baseline -> 3 tests: no-SLA 29.6 (P95 -> 6s, still 10%), batch->512 (7-10%), dtypes none
=> one instance can't fill the card -> the 3.4x is real
-->

```seaborn
import matplotlib.pyplot as plt

FG, DIM = "#3a2020", "#7a6a5a"
RED, GREEN, GREY = "#e61e24", "#39ae4a", "#e0e0df"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.0),
                               gridspec_kw={"width_ratios": [1.3, 1], "wspace": 0.32})
fig.patch.set_alpha(0)
for ax in (ax1, ax2):
    ax.set_facecolor("none")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    ax.set_xticks([])

# ---- left: throughput, labels to the LEFT so nothing overlaps the line ----
ax1.text(-42, 2.9, "REQ/S PER CARD  @  P95 160 MS", fontsize=10.5, color=DIM, family="monospace")
for y, v, n, c in [(2, 20.7, "Native", GREY), (0, 71.1, "HAMi + KEDA", RED)]:
    ax1.barh(y, v, color=c, height=0.62)
    ax1.text(-3, y, n, ha="right", va="center", fontsize=12, color=FG, fontweight="bold")
    ax1.text(v + 3, y, str(v), ha="left", va="center", fontsize=12.5, color=FG, fontweight="bold")
ax1.plot([20.7, 20.7], [-0.5, 2.5], color=DIM, linewidth=1.2, linestyle=(0, (4, 3)))
ax1.text(20.7, 2.55, "one whole GPU", ha="center", va="bottom", fontsize=10.5, color=DIM)
ax1.text(-3, -0.55, "3.4x per card", ha="right", va="center", fontsize=11.5, color=RED, fontweight="bold")
ax1.set_xlim(-42, 100)
ax1.set_ylim(-0.9, 3.1)

# ---- right: SM utilization ----
ax2.text(-0.15, 128, "SM UTILIZATION VS REPLICAS", fontsize=10.5, color=DIM, family="monospace")
xs, vals = [0, 1, 2, 3], [18, 31, 54, 100]
ax2.plot(xs, vals, color=RED, linewidth=2.2, zorder=2)
for x, v, c, r in zip(xs, vals, [GREY, RED, RED, GREEN], [7, 5.5, 5.5, 9]):
    ax2.plot(x, v, "o", markersize=r, color=c, markeredgecolor="white", markeredgewidth=1.3, zorder=3)
    ax2.text(x, v + 8, f"{v}%", ha="center", fontsize=11.5, color=FG, fontweight="bold")
for x, lab in zip(xs, ["1", "2", "5", "10 replica"]):
    ax2.text(x, -13, lab, ha="center", fontsize=12, color=DIM)
ax2.set_xlim(-0.35, 3.4)
ax2.set_ylim(-22, 140)
```

One pod uses only **18% of the card**. Pack **10 replicas** on it and the GPU hits **100%** - same latency.

- **HAMi does not make one pod faster** - it fills the GPU that was sitting empty
- Bigger batches did not help either: **32 to 512**, GPU still 7-10%
- Same 71 req/s (H200): **1 GPU instead of 3.4** → **~71% fewer cards**, **~51% less power**, **~$7k/month** at an example $4/GPU-h

---

## One Card, One Day

@subtitle One slice guaranteed, on purpose - and what it costs

<!--
free space fits anything: small LLMs, agents, CV, embeddings
the PRICE: cap notebook to 70% cores -> 1h00 -> 1h20 = +20 min
why the reservation is solid:
  - memory FENCED: sees own slice, can't OOM neighbours
  - cores CAPPED with `force`: 70% genuinely reserved, not 'if idle'
  - we PAY 20 min on purpose (small model cheap; big model costs more)
LAND: 20 min turns 'maybe there is space' into 'this space is yours'
-->

**Workload:** an AI Notebook training YOLO11 - ~17k images, batch 64 → **39 GB** used. Batch is sized for **accuracy**, not to fill the card - so the spare **~100 GB is genuinely free**, not just idle. We fence **~30%** and cap the notebook to **70% of the cores**.

```seaborn
import matplotlib.pyplot as plt

FG, DIM = "#3a2020", "#7a6a5a"
RED, GREY = "#e61e24", "#eceae8"

fig, ax = plt.subplots(figsize=(5.2, 2.85))
fig.patch.set_alpha(0)
ax.set_facecolor("none")
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.set_xticks([])

ax.text(-0.55, 104, "PRICE OF CAPPING", fontsize=11.5, color=DIM, family="monospace")
ax.plot([-0.5, 1.55], [60, 60], color=DIM, linewidth=1.2, linestyle=(0, (4, 3)), zorder=3)
ax.bar(0, 60, width=0.5, color=GREY, zorder=2)
ax.bar(1, 80, width=0.5, color=RED, zorder=2)
ax.text(0, 63, "1h00", ha="center", va="bottom", fontsize=15, color=FG, fontweight="bold")
ax.text(1, 83, "1h20", ha="center", va="bottom", fontsize=15, color=FG, fontweight="bold")
ax.text(1.34, 70, "+20 min", ha="left", va="center", fontsize=13, color=RED, fontweight="bold")
ax.text(0, -8, "full", ha="center", va="top", fontsize=12, color=DIM)
ax.text(1, -8, "70% cores", ha="center", va="top", fontsize=12, color=DIM)
ax.set_xlim(-0.8, 2.5)
ax.set_ylim(-20, 112)
```

- {icon:lock cls=accent-primary} **Memory is fenced.** The notebook sees only its own slice - it cannot OOM the neighbours
- {icon:gauge cls=accent-primary} **Cores are capped** with `force` - the freed share is **reserved**, not "maybe"
- {icon:refresh-cw cls=accent-contrast} **The price:** ~20 minutes, on purpose - *a small model; a big one costs much more*

---

## The Rest Follows The Load

@subtitle One notebook fixed all day - inference flexes by the hour

<!--
green = the notebook, NEVER changes (capped, guaranteed, same machine all day)
everything right of it FOLLOWS the load:
  morning: everyone opens forecasts -> time-series x6
  office hrs: -> x1, LLM inference x5 (<20B, e.g. Qwen2.5-14B)
  night: inference quiet -> more notebooks + overnight training
LAND: they peak at different hours -> take turns on one card -> never idles
-->

```seaborn
import matplotlib.pyplot as plt

FG, DIM = "#3a2020", "#7a6a5a"
BLUE, BLUEL, RED, YELLOW, GREY = "#28a4db", "#8fcdec", "#e61e24", "#f4a93a", "#eceae8"

fig, ax = plt.subplots(figsize=(11, 3.35))
fig.patch.set_alpha(0)
ax.set_facecolor("none")
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.set_xticks([])

ax.text(-26, 2.86, "ONE H200 ACROSS ONE DAY", fontsize=11.5, color=DIM, family="monospace")
rows = [
    (2, "Morning", [(30, BLUE, "Notebook ~30%"), (50, RED, "Time-series  ×6"), (20, GREY, "")]),
    (1, "Office hours", [(30, BLUE, "Notebook ~30%"), (8, RED, "×1"), (42, YELLOW, "LLM inference  ×5"), (20, GREY, "")]),
    (0, "Night", [(30, BLUE, "Notebook ~30%"), (42, BLUEL, "more training"), (8, RED, "×1"), (20, GREY, "")]),
]
for y, label, segs in rows:
    left = 0
    for w, c, txt in segs:
        ax.barh(y, w, left=left, color=c, height=0.62, edgecolor="white", linewidth=1.8)
        if txt:
            ax.text(left + w / 2, y, txt, ha="center", va="center", fontsize=10.5,
                    color="#161616" if c in (YELLOW, BLUEL) else "white", fontweight="bold")
        left += w
    ax.text(-3, y, label, ha="right", va="center", fontsize=13, color=FG, fontweight="bold")
ax.text(100, 2.7, "card full", ha="right", va="bottom", fontsize=10, color=DIM)
ax.plot([100, 100], [-0.4, 2.58], color=DIM, linewidth=1.0, linestyle=(0, (2, 3)), zorder=1)
ax.set_xlim(-26, 106)
ax.set_ylim(-0.6, 3.2)
```

- {icon:lock cls=accent-primary} **The notebook never moves.** Its slice is fixed all day → training stays stable and guaranteed
- {icon:refresh-cw cls=accent-contrast} **KEDA hands the freed space off through the day.** The morning **burst fades** → cores go to **LLM <20B** → one time-series instance stays for scattered load → at night, spare **auto-scales more notebooks** for extra overnight training. *Never idle.*

---

@hidden
## Stable While Shared

@subtitle Does sharing make training jittery? We measured it

<!--
BACKUP - show only if asked about stability
CV = coefficient of variation of epoch time (lower = steadier)
alone: ~1% | shared + NO cap: 19% (jittery) | cap with `force`: 9% (steady)
=> the cap roughly HALVES the jitter, on the same shared card
honest: cap protects STABILITY, not throughput. hard isolation = MIG.
-->

The card is now *truly* shared - the notebook trains while **bursty inference** flexes beside it. Does that shake the training? We measured epoch-time **CV** - standard deviation ÷ mean, lower is steadier.

```seaborn
import matplotlib.pyplot as plt

FG, DIM = "#3a2020", "#7a6a5a"
RED, GREEN = "#e61e24", "#39ae4a"

fig, ax = plt.subplots(figsize=(5.6, 2.95))
fig.patch.set_alpha(0)
ax.set_facecolor("none")
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.set_xticks([])

ax.text(-0.55, 23.2, "EPOCH-TIME JITTER  (CV, LOWER = STEADIER)", fontsize=10, color=DIM, family="monospace")
bars = [(0, 1, GREEN, "alone"), (1, 19, RED, "shared, no cap"), (2, 9, GREEN, "shared, capped")]
for x, v, c, lab in bars:
    ax.bar(x, v, width=0.56, color=c, zorder=2)
    ax.text(x, v + 0.8, f"{v}%", ha="center", va="bottom", fontsize=15, color=FG, fontweight="bold")
    ax.text(x, -1.4, lab, ha="center", va="top", fontsize=11.5, color=DIM)
ax.annotate("", xy=(1.82, 10.2), xytext=(1.18, 17.6),
            arrowprops=dict(arrowstyle="->", color=FG, linewidth=1.7, connectionstyle="arc3,rad=-0.32"))
ax.text(2.02, 15.0, "cap halves it", ha="center", va="center", fontsize=10.5, color=FG, fontweight="bold")
ax.set_xlim(-0.65, 2.7)
ax.set_ylim(-4, 24.5)
```

- {icon:check cls=accent-primary} **Alone, nothing contends:** CV ~**1%** - rock-steady epochs
- {icon:triangle-alert cls=accent-secondary} **Shared with bursty inference, no cap:** CV jumps to **19%** - jittery, hard to predict
- {icon:gauge cls=accent-primary} **Cap the neighbours (`force`):** CV back to **9%** - steady again, same shared card

> **Honest caveat:** cap isolates *stability*, not *throughput* - for hard throughput isolation, use **MIG**.

---

## But It Does Not Always Help

@subtitle HAMi fills the *empty* part of a card - a full one has nothing to give

<!--
helps: job SMALL or BURSTY, can't fill card alone (bursty = comes in waves) -> our 10 pods, 3.4x
does NOT help when the job already fills the GPU - measured twice:
  - LLM SGLang: 1 big 11.6k tok/s > 4 small 7.3k (continuous batching)
  - training LSTM x1/x2/x4: 2779 -> 2278 -> 2148 = 0.77x, packing LOSES
=> full card: packing = isolation + fair share, NOT throughput
[pause] gpumem = REAL limit (neighbour safe) | gpucores = only a HINT
  10% vs 90% pods -> same ~11 ops/s each (fair share under contention)
  3rd line: with `force` the cap is real (the 70%, costs 20 min)
LAND: promise memory. do not promise compute.
cut-for-time: drop LLM/training detail, NEVER the gpumem/gpucores table
-->

::: grid {cols=2}
::: card {tag=green}
### {icon:check cls=accent-primary} It helps when the card is empty

**Inference:** one pod = **~18% SM**, card **82% idle**.

- Pack ~10 → SM hits **100%** → **3.4x more work**
:::
::: card {tag=red}
### {icon:x cls=accent-secondary} Not when it is already full

**Training / big LLM:** one instance **already saturates** the card.

- Big LLM: one **11.6k** tok/s **>** four small **7.3k**
- Same training job **× 4**: **0.77x** - packing *loses*
:::
:::

**Careful what you promise your users:**

| What you ask for | What you get |
|---|---|
| `gpumem` - memory | **A real limit.** Your neighbour is safe |
| `gpucores`, default | **Only a hint.** 10% and 90% ran the same speed |
| `gpucores`, **`force`** | **A real cap.** 70% cores → run takes 1h20, not 1h |

---

## What It Really Took

@subtitle The hard part is not installing HAMi

<!--
install = a Helm chart. NOT the hard part.
1) Kyverno blocked it: plugin needs host driver/devices + kubelet socket -> privileged+hostPath -> policy rejects -> allow hami-system ns
2) nvidia.com/gpu ambiguous - both the NVIDIA device plugin AND HAMi claim it. two switches: OFF operator device-plugin; CDI OFF (CDI wires devices itself; HAMi needs the plain legacy runtime)
3) fractional/full/Slinky fought for nodes -> own pool + own scheduler + a taint
4) 2.9 renamed every metric -> dashboards empty -> new names + doc fix upstream
LAND (SLOW): this is an operations project, not a one-line install
-->

| Obstacle | Solution |
|---|---|
| HAMi's **privileged access** conflicts with **Kyverno** policies | Exclude `hami-system` from the **pod-security** policies |
| **`nvidia.com/gpu`** is ambiguous - claimed by both the **NVIDIA device plugin** and HAMi | Operator device plugin off, CDI off |
| **Resource-pool overlap** - fractional, full-GPU, and **Slurm** (Slinky) | Own pool, own scheduler, and a taint |
| HAMi 2.9 **metrics refactor** - Grafana dashboards mismatch, go **empty** | Use `hami_*`. We fixed the docs upstream |

> **It is an operations project, not a one-line install.**

---

## Where The Magic Breaks

@subtitle Useful to know before you debug for two days

<!--
HAMi sits in front of every CUDA call (libvgpu, LD_PRELOAD). code that goes around CUDA = HAMi is blind.
GOOD news first: what stays inside CUDA does NOT break - even multi-GPU (P2P/all-reduce/TP+CUDA graphs, NCCL 2.28, incl old NCCL on the legacy path)
2 failures, both go around CUDA:
  - musl image (Alpine/busybox): libvgpu needs glibc -> 'libdl.so.2 not found', exit 127 before your code runs. fix: glibc base (Debian/Ubuntu CUDA)
  - MATLAB: its Runtime deadlocks at startup, freezes BEFORE it ever reaches a CUDA call
-->

HAMi sits in front of every CUDA call. **Go around CUDA, and HAMi cannot see you.**

```seaborn
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

FG, DIM = "#3a2020", "#7a6a5a"
GREEN, RED = "#39ae4a", "#e61e24"

fig, ax = plt.subplots(figsize=(10.5, 2.6))
fig.patch.set_alpha(0)
ax.set_facecolor("none")
ax.set_xlim(0, 100)
ax.set_ylim(-1, 44)
ax.axis("off")

def box(x, w, text, fc, ec, tc, fs=12.5):
    y, h = 25, 12
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=2",
                                linewidth=1.8, edgecolor=ec, facecolor=fc, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight="bold", zorder=4, linespacing=1.3)

box(3, 22, "App / framework", "#ffffff", DIM, FG)
box(40, 26, "HAMi libvgpu\n(intercept)", "#e6f5e9", GREEN, "#1f5b2b")
box(82, 15, "GPU", "#ffffff", DIM, FG)

ax.annotate("", xy=(39.5, 31), xytext=(25.5, 31), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=2.3, mutation_scale=16))
ax.annotate("", xy=(81.5, 31), xytext=(66.5, 31), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=2.3, mutation_scale=16))
ax.text(32.5, 34.2, "CUDA", ha="center", fontsize=10, color=DIM, family="monospace")
ax.text(50, 41.5, "through CUDA  →  HAMi caps & fences it", ha="center", fontsize=11.5, color="#1f5b2b", fontweight="bold")

byp = FancyArrowPatch((13, 24.5), (89, 24.5), connectionstyle="arc3,rad=0.15",
                      arrowstyle="-|>", mutation_scale=18, lw=2.1, color=RED, linestyle=(0, (5, 3)), zorder=2)
ax.add_patch(byp)
ax.text(50, 7.5, "around CUDA  →  HAMi is blind", ha="center", fontsize=11.5, color=RED, fontweight="bold")
ax.text(50, 2.5, "e.g. MATLAB - freezes before it ever reaches CUDA", ha="center", fontsize=9.5, color=DIM)
```

- {icon:package cls=accent-secondary} **Alpine / musl images crash.** libvgpu - HAMi's `LD_PRELOAD` interposer - needs **glibc**; on Alpine/busybox it can't find `libdl.so.2` (exit **127**). Use a glibc CUDA image - Debian or Ubuntu
- {icon:x cls=accent-secondary} **Runtimes that skip CUDA hang.** MATLAB freezes *before* it ever reaches a CUDA call
- {icon:check cls=accent-primary} **What does *not* break:** even multi-GPU - P2P, all-reduce, tensor parallel + CUDA graphs on NCCL 2.28 - all stays inside CUDA

---

## What Is Next For Us

@subtitle From one pool to a real service

- {icon:users cls=accent-primary} **More teams** inside Viettel, with quota per team
- {icon:server cls=accent-primary} **More pools** - the H200 and mixed-GPU pools today, the rest of the fleet next
- {icon:gauge cls=accent-contrast} **More workload types** on the same card - agents, bigger LLMs, batch jobs
- {icon:git-compare-arrows cls=accent-contrast} **Move to DRA** - keep the same isolation, swap the custom API for the standard Kubernetes one

---

# Part 4: Where We Are Today

@subtitle Adoption, Case Studies, Community 

---

@hidden
## Applicable Scenarios

@subtitle Online inference, A/B testing, mixed workloads

<!--
Four scenarios HAMi enables. Key message: GPU sharing is not one-size-fits-all. Online inference saves cost, A/B testing saves hardware, mixed train/infer keeps GPUs busy, LLM optimization fits more models per device.
-->

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

@layout metrics
## Where We Are Today

@subtitle Production metrics from CNCF case studies

::: grid {cols=4}
::: card {metric}
100%
Hardware pool utilization
Baike Holdings
:::
::: card {metric}
10x
GPU utilization in CI
NIO
:::
::: card {metric}
30%
Fewer GPU hours
China Merchants Bank
:::
::: card {metric}
10,000+
Pods running concurrently
Baike Holdings
:::
:::

@row

::: notes{ tag="green" }
China Merchants Bank · SNOW Corp. · NIO · KE Holdings · DaoCloud · SF Technology · Prep Education · [cncf.io/case-studies](https://www.cncf.io/case-studies/) · Reach out for help submitting yours.
:::

---

@layout ecosystem
## Community & Adopters

@subtitle Devices, integrations, and who uses HAMi

<!--
4.1k stars, 325k pulls, 500+ contributors, 27 countries. 11 device types, 20+ adopters. This is the ecosystem slide -- show the breadth. The QR code links to github.com/Project-HAMi/HAMi.
-->

#### Open Source, CNCF Backed, Production Ready
::: grid {cols=5}
::: card {metric}
4.1k
Github Stars
:::
::: card {metric}
325k
Docker Pulls
:::
::: card {metric}
500+
Contributors
:::
::: card {metric}
27
Contributor Countries
:::
::: card

![Kubernetes](assets/ecosystem/integrations/kubernetes.png) ![Volcano](assets/ecosystem/integrations/volcano.png) ![Kueue](assets/ecosystem/integrations/kueue.png) ![Koordinator](assets/ecosystem/integrations/koordinator.png) ![KAI Scheduler](assets/ecosystem/integrations/kai-scheduler.png) ![cozystack](assets/ecosystem/integrations/cozystack.svg)
:::
:::

#### Ecosystem & Device Support
::: grid {cols=2}
::: card
![NVIDIA](assets/ecosystem/devices/nvidia.png) ![Ascend](assets/ecosystem/devices/ascend.png) ![Cambricon](assets/ecosystem/devices/cambricon.png) ![Hygon](assets/ecosystem/devices/hygon.png) ![Iluvatar](assets/ecosystem/devices/illuvitar.png)
![Metax](assets/ecosystem/devices/metax.png) ![Moore Threads](assets/ecosystem/devices/moorethreads.png) ![Kunlunxin](assets/ecosystem/devices/kunlunxin.png) ![Enflame](assets/ecosystem/devices/enflame.png)
![AWS](assets/ecosystem/devices/aws.png) ![VastStream](assets/ecosystem/devices/vaststream.png)
:::
:::

#### Adopters
::: grid {cols=2}
::: card
![4Paradigm](assets/ecosystem/adopters/4paradigm.png) ![Baidu](assets/ecosystem/adopters/baiduzhineng.png) ![Baike](assets/ecosystem/adopters/baike.png) ![China Merchants](assets/ecosystem/adopters/chinamerchants.png) ![China Mobile](assets/ecosystem/adopters/chinamobile.png)
![China Unicom](assets/ecosystem/adopters/chinaunicom.png) ![DaoCloud](assets/ecosystem/adopters/daocloud.png) ![Dynamia](assets/ecosystem/adopters/dynamia.png) ![H3C](assets/ecosystem/adopters/h3c.png) ![Huawei](assets/ecosystem/adopters/huawei.png)
![LinkedIn](assets/ecosystem/adopters/linkedin.png) ![MSXF](assets/ecosystem/adopters/msxf.png) ![NIO](assets/ecosystem/adopters/nio.png) ![PPIO](assets/ecosystem/adopters/ppio.png) ![Prep](assets/ecosystem/adopters/prep.png)
![SAP](assets/ecosystem/adopters/sap.png) ![SF Technology](assets/ecosystem/adopters/sftechnology.png) ![Si-Tech](assets/ecosystem/adopters/si-tech.png) ![Snow](assets/ecosystem/adopters/snow.png) ![Viettel](assets/ecosystem/adopters/viettel.png)
:::
:::

---

@kicker Thank You
@side-image assets/kcd_vietnam/qr-code.png
# Questions?

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI  -  Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh
@speaker name="The Anh Nguyen" role="Software Engineer, Viettel Networks  -  CNCF Kubestronaut" github=github.com/ntheanh201 linkedin=linkedin.com/in/ntheanh201
