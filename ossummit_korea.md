---
theme: ossummit_korea
seaborn_theme: ossummit_korea
title: Simplifying AI for Edge Compute with HAMi
footer: Simplifying AI for Edge Compute with HAMi - Open Source Summit Korea 2026
logo: assets/brand/dynamia-logo.svg
logo_dark: assets/brand/dynamia-logo-white.png
watermark: assets/brand/cncf-logo.png
transition: fade
paginate: true
---

@variant dark
@side-image assets/brand/ossummit_korea/qr-code.png
@kicker Open Source Summit Korea 2026  -  Embedded & Open AI
# Simplifying AI for Edge Compute with HAMi

@subtitle Slicing one device, running many agents

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI  -  Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

---

# Part 1: The Problem

@subtitle The model is not the hard part, the compute is

---

## Not All Edge Compute Is Agents

@subtitle Most edge inference today is CV and classic ML

<!--
Most inference running on edge devices today is not language models. YOLO-style detection, classification, OCR, embeddings: small models, millisecond latency, already cheap on NPUs and embedded GPUs. Agents are a new slice and the hardest one to schedule: memory-heavy LLMs running concurrently on the same device.
-->

::: grid {cols=3}
::: card {tag=green}
### {icon:scan cls=accent-secondary} CV and classic inference

- YOLO, classification, OCR, embeddings, Deep Learning
- 1-50M params, millisecond latency
- Runs on NPUs and embedded GPUs today
:::
::: card {tag=cyan}
### {icon:message-square cls=accent-primary} LLMs

- Autoregressive text generation
- Weights plus KV cache in memory
- Needs GPU-class silicon
:::
::: card {tag=red}
### {icon:bot cls=accent-secondary} Agents

- LLMs in a tool-use loop
- Several concurrent per device
- Memory-hungry, latency-tolerant
:::
:::

One deployment pattern for all three: same device sharing for small-model inference and agent tasks.

---

## Edge Agents, Starved Compute

@subtitle Open-source agents need edge hardware

<!--
Hermes and OpenClaw can reason and use tools. Running them at the edge is hard: not because of the models, but because of the compute underneath. Limited memory, tight power budgets, unattended operation, no elastic scaling. To run agents at the edge, fix the compute layer first.
-->

Open-source agents like Hermes and OpenClaw can reason and use tools. Edge deployment is still hard: not the model, the compute underneath.

::: grid {cols=2}
::: card {tag=red}
### {icon:memory-stick cls=accent-secondary} Limited memory

A Jetson-class device has 8-64 GB of unified memory, shared with the OS. One agent stack can eat it all.
:::
::: card {tag=yellow}
### {icon:zap cls=accent-contrast} Tight power budgets

No 300 W data-center GPU at the edge. You get 5-40 W, often battery or solar.
:::
::: card {tag=cyan}
### {icon:user-x cls=accent-primary} Unattended

No cluster admin on call. Prometheus may scrape, but no one watches the dashboards. It has to work after setup.
:::
::: card {tag=green}
### {icon:scale cls=accent-primary} No elastic scaling

Cloud load grows: add GPUs. Edge load grows: nothing to add. The deployed box is all you get.
:::
:::

To run agents at the edge, fix the compute layer first.

---

## What is HAMi

@subtitle Before: one device, one task

<!--
GPUs are expensive and often underutilized. HAMi is a heterogeneous GPU sharing framework for Kubernetes. It slices GPUs and shares them across workloads, without rewriting your stack.
-->

![Before HAMi](assets/hami_intro/before-hami.png)

---

## What is HAMi
@transition none

@subtitle After: one device, many agents

![After HAMi](assets/hami_intro/after-hami.png)

---

@layout compare

## The Edge Compute Challenge

@subtitle What breaks, what HAMi needs to solve

::: card {tag=compare}
### Problem

- One model per device, most of it idle
- Fixed memory budgets: install once, never share
- One bad agent takes down the device
- Requirements vary wildly: tiny CV filters to large agent LLMs
:::

::: arrow

{icon:arrow-right cls=accent-primary size=48}
:::

::: card {tag=compare}
### Requirements

- Guaranteed to run: unattended, no ops team
- Runs stably: hard limits, one agent cannot kill the device
- Right device per workload, big or small: NPU for CV, GPU-class for LLMs, one API
- Same deployment patterns: no manifest changes per device
- Fine-grained slices: carve memory, time-share when demand exceeds
:::

<!--
At the edge the bar is different: no observability stacks, the device must run unattended, the silicon must match the workload, and deployment patterns stay unchanged. Edge workloads span tiny CV filters to large agent LLMs, big or small, on whatever silicon is there. The real work is memory isolation: carving unified memory so multiple agents run concurrently, and time-sharing when demand exceeds it.
-->

---

# Part 2: The Solution

@subtitle One scheduling plane across heterogeneous accelerators

---

## HAMi Capabilities

@subtitle Six things HAMi brings to GPU scheduling

<!--
Six capabilities. The key ones for this talk: hard isolation, advanced scheduling, and unified monitoring. Heterogeneous management is the differentiator, not just NVIDIA.
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

## Types of Slicing

@subtitle Four ways to share one device

<!--
Slicing comes in four flavors. Memory and compute slicing are the core of HAMi: 1 MiB memory, 1% compute. Compute slicing caps the % of the device's compute units a pod may use; it is enforced on every kernel launch and a pod cannot burst above its slice even when the device is idle (MPS %, dcucores, vcore are vendor names for the same quota). Time slicing is pure software: no vendor ships a time-quantum API, the scheduler rotates compute access over time. So even if a vendor exposes no slicing at all, you can hook its driver SDK and build your own. That is reverse engineering: fragile, breaks on SDK updates. Better to ask the vendor for support, the way HAMi does with NVIDIA and Huawei.

Compute slicing is the goal, the mechanism depends on the vendor. HAMi exposes one uniform API (gpucores: 40) and adapts: NVIDIA and Ascend have no hardware compute cap, so HAMi intercepts launches in user space (libvgpu.so, token bucket), finest granularity at 1%. AMD CU masking and NVIDIA MPS are hardware-scheduler-honored caps, static per process. Kunlunxin vXPU and Hygon vDCU are hardware-fenced, coarse but silicon-enforced. The boundary: vendors with no mechanism at all, like DeepX and Axelera, no hijack point and no quota API, so compute slicing is impossible without reverse engineering.
-->

::: grid {cols=2}
::: card {tag=green}
### {icon:memory-stick cls=accent-secondary} Memory slicing

- Carve memory per tenant
- HAMi: 1 MiB per pod
- Native: fixed partitions (MIG, vXPU)
:::
::: card {tag=cyan}
### {icon:gauge cls=accent-secondary} Compute slicing

- Cap compute at a % of the device
- HAMi: 1% per pod
:::
::: card {tag=yellow}
### {icon:clock cls=accent-contrast} Time slicing

- Workloads take turns
- Pure software
:::
::: card {tag=red}
### {icon:layers cls=accent-primary} Hardware partitioning

- MIG, SR-IOV, vXPU, vDCU
- Static, strongest isolation
:::
:::

**Time slicing is pure software:** reverse engineering possible, better if the vendor SDK supports it.

---

## Memory Slicing

@subtitle Carve unused memory into per-pod slices

<!--
Real measured jobs, each holding a whole H200 (141 GB): the time-series inference job used 1 GB, the YOLO training job 39 GB. Whole-card allocation wastes ~100 GB. Memory slicing carves it into MiB-level partitions, one per pod, dynamic.
-->

::: card
```seaborn
import matplotlib.pyplot as plt

fg = plt.rcParams["text.color"]
dimmed = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
red = cmap(4.5 / 12)
yellow = cmap(6.5 / 12)
grey = "#eceae8"

fig, ax = plt.subplots(figsize=(9.5, 2.9))
ax.set_facecolor("none")
fig.patch.set_alpha(0)

ax.text(-4, 1.75, "GPU MEMORY: ALLOCATED VS USED", fontsize=10.5, color=dimmed, family="monospace")

ax.barh(1, 141, color=grey, height=0.5)
ax.barh(1, 2, color=red, height=0.5)
ax.barh(0, 141, color=grey, height=0.5)
ax.barh(0, 39, left=2, color=yellow, height=0.5)

ax.text(-4, 1, "Inference\njob", ha="right", va="center", fontsize=12, color=fg, fontweight="bold", linespacing=1.4)
ax.text(-4, 0, "Training\njob", ha="right", va="center", fontsize=12, color=fg, fontweight="bold", linespacing=1.4)

ax.text(6, 1, "2 GB used", ha="left", va="center", fontsize=11.5, color=fg)
ax.text(44, 0, "39 GB used", ha="left", va="center", fontsize=11.5, color=fg)

ax.text(141, 1.42, "one whole H200 = 141 GB", ha="right", va="bottom", fontsize=10.5, color=dimmed)

ax.annotate("", xy=(139, -0.55), xytext=(41, -0.55),
            arrowprops=dict(arrowstyle="<->", color=dimmed, linewidth=1.4))
ax.text(90, -0.74, "~100 GB free: sliced per pod",
        ha="center", va="top", fontsize=10.5, color=fg, fontweight="bold")

ax.set_xlim(-4, 148)
ax.set_ylim(-1.15, 1.95)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.set_xticks([])
```
:::

- One job holds a whole card: 2 GB used of 141 GB
- Slicing frees the rest: MiB-level partitions per pod

---

## Compute Slicing

@subtitle Percent of compute per pod, enforced on every call

<!--
Each pod is capped at a percent of the device's compute units. The cap is enforced on every kernel launch: a pod cannot burst above its slice even when the rest of the device is idle. Units not assigned to a pod stay free for other pods.
-->

::: card
```seaborn
import matplotlib.pyplot as plt

fg = plt.rcParams["text.color"]
dimmed = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
green = cmap(2.5 / 12)
grey = "#9ca3af"

fig, ax = plt.subplots(figsize=(9, 2.7))
ax.set_facecolor("none")
fig.patch.set_alpha(0)

units, assigned = 8, 2
ax.bar(range(units), [1] * units, width=0.85,
       color=[green] * assigned + [grey] * (units - assigned),
       edgecolor="white", linewidth=1.5)

for u in range(units):
    ax.text(u, -0.18, str(u + 1), ha="center", va="top", fontsize=9.5, color=dimmed)

ax.annotate("", xy=(-0.35, -0.75), xytext=(1.35, -0.75),
            arrowprops=dict(arrowstyle="<->", color=fg, linewidth=1.4))
ax.text(0.5, -1.05, "pod A: 2 of 8 units = 25%", ha="center", va="top",
        fontsize=11.5, color=fg, fontweight="bold")
ax.text(4.5, -1.05, "6 units free for other pods", ha="center", va="top",
        fontsize=11.5, color=fg, fontweight="bold")

ax.text(-0.55, 1.75, "COMPUTE UNITS: 8 ON THE DEVICE, 2 ASSIGNED TO POD A",
        fontsize=10, color=dimmed, family="monospace")

ax.set_xlim(-0.6, 7.6)
ax.set_ylim(-1.5, 2.2)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.set_xticks([])
```
:::

- Each pod gets a fixed % of the device's compute units
- Hard ceiling on every kernel launch: no bursting above the slice
- Unused units stay free for other pods

---

## Time Slicing

@subtitle Workloads take turns at kernel boundaries

<!--
High-priority tasks preempt low-priority ones at CUDA kernel boundaries: no wasted compute, clean context switch. The kernel boundary is the key: you cannot preempt mid-kernel. Pure software: no vendor ships a time-quantum API.
-->

::: card
```seaborn
import matplotlib.pyplot as plt

fg = plt.rcParams["text.color"]
dimmed = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
green = cmap(2.5 / 12)
grey = "#9ca3af"

fig, ax = plt.subplots(figsize=(9, 3.1))
ax.set_facecolor("none")
fig.patch.set_alpha(0)

for i, name in enumerate(["Agent A", "Agent B", "Agent C", "Agent D"]):
    y = 3 - i
    for q in range(4):
        color = green if q == i else grey
        ax.barh(y, 25, left=q * 25, color=color, height=0.6)
    ax.text(-4, y, name, ha="right", va="center", fontsize=11, color=fg, fontweight="bold")
    ax.text(i * 25 + 12.5, y, "EXECUTING", ha="center", va="center", fontsize=9, color=fg, fontweight="bold")

for x in [25, 50, 75]:
    ax.plot([x, x], [-0.5, 3.5], color=fg, linewidth=0.8, linestyle="--")

ax.text(50, 3.85, "TIME SLICING: ONE DEVICE, FOUR SLICES",
        ha="center", fontsize=10.5, color=dimmed, family="monospace")
ax.text(106, -0.75, "time ->", ha="right", va="top", fontsize=9, color=dimmed)

ax.set_xlim(-6, 106)
ax.set_ylim(-1.0, 4.1)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.set_xticks([])
```
:::

- Rotate compute access over time
- Kernel boundary is the switch point: no mid-kernel preemption
- Preemption optional: without it, long kernels run to completion

---

## Hardware Partitioning

@subtitle Fixed slots, strongest isolation, least flexible

<!--
MIG, SR-IOV, vXPU, vDCU: partitions set at boot, enforced in hardware, memory and compute fenced per slot. Strongest isolation, least flexible: no live repartition. Software slicing can repartition live but lives in the runtime layer.
-->

::: card
```seaborn
import matplotlib.pyplot as plt

fg = plt.rcParams["text.color"]
dimmed = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
blue = cmap(0.5 / 12)
green = cmap(2.5 / 12)
orange = cmap(6.5 / 12)
grey = "#9ca3af"

fig, ax = plt.subplots(figsize=(8, 2.8))
ax.set_facecolor("none")
fig.patch.set_alpha(0)

for left, w, c, lab in [(0, 50, blue, "1/2 card"), (50, 25, green, "1/4 card"), (75, 25, orange, "1/4 card")]:
    ax.barh(1, w, left=left, color=c, height=0.65)
    ax.text(left + w / 2, 1, lab, ha="center", va="center", fontsize=9, color=fg, fontweight="bold")

ax.barh(0, 40, left=0, color=grey, height=0.65)
ax.barh(0, 35, left=40, color=grey, height=0.65)
ax.barh(0, 25, left=75, color=grey, height=0.65)
for x in [40, 75]:
    ax.plot([x, x], [-0.38, 0.62], color=fg, linewidth=1.2, linestyle="--")
for x, lab in [(20, "40%"), (57.5, "35%"), (87.5, "25%")]:
    ax.text(x, 0, lab, ha="center", va="center", fontsize=9, color=fg, fontweight="bold")

ax.text(0, 1.38, "HARDWARE PARTITIONS:  MIG, SR-IOV, vXPU, vDCU", ha="left", va="bottom", fontsize=10, color=fg, fontweight="bold")
ax.text(0, 0.38, "SOFTWARE PARTITIONS:  HAMi slices", ha="left", va="bottom", fontsize=10, color=fg, fontweight="bold")

ax.set_xlim(0, 100)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
```
:::

- MIG, SR-IOV, vXPU, vDCU: hardware partitions, silicon-enforced
- Memory and compute fenced per slot: strongest isolation

---

## Making NPUs Schedulable

@subtitle What it takes to share them

<!--
Three pieces are needed. Capacity reporting: tell the scheduler what each device has, in memory MiB and compute percent. Allocation: decide which slice goes where, binpack or spread. Enforcement: the hard part. On CUDA, HAMi hijacks the runtime calls. NPU SDKs are closed compilers: there is no hijack point, so enforcement has to happen in the SDK's runtime or stay scheduler-side. The DRA path solves this cleanly: typed capacities in ResourceSlices, allocation decided by the scheduler, no code changes. Status today: HAMi supports NVIDIA, Ascend, Cambricon, Hygon, Iluvatar and more; Jetson and these NPUs are not supported yet. This is the roadmap, honestly stated.
-->

- **Capacity reporting:** publish memory MiB and compute % per device
- **Allocation:** binpack and spread policies fit agents into the gaps
- **Enforcement: the hard part.** CUDA has a hijack point (the runtime library). NPU SDKs are closed compilers: no hijack, so limits live in the SDK runtime or scheduler-side
- **The clean path is DRA:** typed capacities in ResourceSlices, scheduler allocates, no code changes
- **Honest status:** HAMi shares NVIDIA, Ascend, Cambricon, Hygon, Iluvatar today. Jetson and these NPUs are the frontier, not a shipped feature

---

## Why Jetson Has No MIG

@subtitle Hardware partitioning is a data-center feature

<!--
MIG is not a software feature. It needs dedicated partitioning logic in the silicon, present in data-center GPUs like A100 and H100. NVIDIA engineers confirmed: the Orin's embedded Ampere die does not have the hardware support, and MIG was never enabled in JetPack for Orin. JetPack 7.0 adds MIG only on Jetson Thor T5000, and only as a technology preview. Software slicing is the only path on Jetson.
-->

::: grid {cols=3}
::: card {tag=red}
### {icon:cpu cls=accent-secondary} No hardware support

MIG needs partitioning logic in the silicon. Data-center GPUs (A100, H100) have it. Orin's embedded Ampere die does not.
:::
::: card {tag=yellow}
### {icon:box cls=accent-contrast} Never enabled in JetPack

MIG has never been enabled for Orin. JetPack 7.0 adds it only on Jetson Thor T5000, as a technology preview.
:::
::: card {tag=cyan}
### {icon:layers cls=accent-primary} CUDA context cap

Orin is capped at ~32 concurrent CUDA contexts. Software slicing is the only path to many tenants.
:::
:::

**MIG on Jetson: not a software toggle. The hardware is not there.**

---

## Small Models Do Not Need MIG

@subtitle Edge agents fit in slices, not fixed hardware partitions

<!--
The agents we want at the edge run small models: Llama-3.2-1B and 3B, Qwen2.5-0.5B through 3B, Hermes-3-3B. A few GB of weights plus context. MIG's smallest A100 slice is 1g.5gb: a fixed 5 GB partition. On an 8 GB Jetson, one MIG-class partition would leave almost nothing else. MiB-granular software slicing fits 10+ small agents where MIG could not fit a single fixed partition.
-->

::: grid {cols=2}
::: card {tag=green}
### {icon:bot cls=accent-primary} Edge agents run small models

Llama-3.2-1B/3B, Qwen2.5-0.5B to 3B, Hermes-3-3B: 1-8 GB with context. They fit in slices, not partitions.
:::
::: card {tag=red}
### {icon:layers cls=accent-secondary} MIG profiles are coarse

Smallest A100 slice is 1g.5gb: a fixed 5 GB partition. No dynamic repartition, no sub-slicing.
:::
::: card {tag=cyan}
### {icon:gauge cls=accent-primary} Granularity mismatch

On an 8 GB Jetson, one fixed 5 GB partition leaves nothing for anything else. MiB slices fit 10+ agents.
:::
::: card {tag=yellow}
### {icon:refresh-cw cls=accent-contrast} Dynamic, not static

MIG partitions are fixed at boot. Edge demand changes: agents come and go. Software slicing repartitions live.
:::
:::

**MIG solves a data-center problem with fixed profiles. The edge needs dynamic, fine-grained carving.**

---

## Jetson vs NPUs: DeepX, Axelera and Furiosa

@subtitle Different partitioning, different schedulability

<!--
DeepX and Furiosa are Korean, both based in Seongnam. DX-M1: 25 TOPS at 1-5 W on an M.2 card, 4 GB LPDDR5 on the module. Axelera is Dutch (Eindhoven): Metis AIPU, RISC-V with digital in-memory computing, ~214 TOPS at 3.5-15 W. Furiosa RNGD: datacenter NPU, 512 TOPS INT8 at 180 W, 48 GB HBM3, PCIe Gen5. Jetson is self-contained with unified memory; the NPUs are PCIe add-ons with memory on the card. Only RNGD has hardware partitioning (SR-IOV, fixed 6/12/24/48 GB); the rest share nothing at the hardware level, so scheduling them means accounting for on-card capacity, not carving host memory.

If someone asks why Metis wins on per-watt: moving data costs far more energy than doing the math. Axelera's chip computes inside its own memory, so the weights never travel. That only works while the model fits in the chip's small on-chip memory. Big models need big HBM memory, and then every chip pays the data-movement tax. That is why RNGD and every LLM chip lands at a few TOPS/W: not a flaw in RNGD, it is the physics of large models.

If someone asks about FP: RNGD lists FP8 512 TFLOPS and BF16 256 TFLOPS, and its FP8 equals its INT8. That matters for LLMs, which run in FP8 or BF16: you serve full-precision formats at full throughput, no INT8 quantization needed. Jetson's FP16 is 85 TFLOPS sparse (dense ~42.5); its 275 TOPS is also the sparse headline (GPU + NVDLA). DeepX and Axelera publish no FP numbers: in-memory compute runs INT8/INT4. For scale: RNGD FP8 per watt (512/180 = 2.8 TFLOPS/W) lands exactly on H100 dense FP8 per watt (1979/700 = 2.8).
-->

| | Jetson AGX Orin | DeepX DX-M1 | Axelera Metis | Furiosa RNGD |
|---|---|---|---|---|
| Architecture | CUDA GPU, unified memory | Proprietary NPU | RISC-V + in-memory compute | TCP NPU, 8 PEs |
| Peak compute (INT8) | 275 TOPS (sparse) | 25 TOPS | ~214 TOPS | 512 TOPS |
| Power | 15-60 W configurable | 1-5 W | 3.5-15 W | 180 W |
| Perf/watt | 1x baseline | ~20x vs GPGPU (vendor) | ~15 TOPS/W | ~2.8 TOPS/W |
| Memory | 64 GB unified LPDDR5 | 4 GB LPDDR5 on card | 16 MB L1 + 32 MB L2 SRAM, 4-16 GB DDR | 48 GB HBM3 |
| Partitioning | None | None | Static 25% L2 per core (1-4) | SR-IOV fixed: 6/12/24/48 GB |

*RNGD is datacenter class, not edge: 512 TOPS at 180 W is 2.8 TOPS/W, 1.8x the A100 (624 INT8 TOPS at 400 W) and on par with H100 dense FP8 (1979 TOPS at 700 W). Value here: Korean domestic silicon, air-cooled density, the only hardware partitioning in the table. Its edge sibling Warboy (64 TOPS) has none.*

---

@layout image-left
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

@layout two-col

## How HAMi Works

@subtitle From pod submission to isolated device

<!--
Five stages from pod submission to isolated GPU. The mutating webhook routes the pod, the scheduler picks a device, the HAMi core library enforces isolation in the container.
-->

- **Mutating webhook:** sees accelerator requests, routes pod to HAMi scheduler
- **Scheduler:** selects device and node
- **HAMi driver:** generates device config
- **Container runtime:** reads config, injects HAMi-Core library
- **HAMi core:** enforces isolation in-process

@col

```pdg
graph dir=TB order=source
pod "Pod submitted" shape=round fill=#F6ECD9 stroke=#F1C560 color=#3a2020 rank=0
webhook "Mutating webhook" shape=round fill=#fce8e8 stroke=#7A0504 color=#3a2020 rank=1
sched "Scheduler" shape=round fill=#fce8e8 stroke=#7A0504 color=#3a2020 rank=2
device "HAMi driver" shape=round fill=#fce8e8 stroke=#7A0504 color=#3a2020 rank=3
runtime "Container runtime" shape=round fill=#F6ECD9 stroke=#F1C560 color=#3a2020 rank=0
core "HAMi core" shape=round fill=#fce8e8 stroke=#7A0504 color=#3a2020 rank=1
workload "Workload (isolated device)" shape=round fill=#F6ECD9 stroke=#F1C560 color=#3a2020 rank=2
pod -> webhook "set scheduler"
webhook -> sched "select device"
sched -> device "allocate device"
device ..> runtime "device config" constraint=false
runtime -> core "inject library"
core -> workload "sees isolated device"
```

---

@layout two-col

## The Magic: Runtime Hijacking

@subtitle Your app does not change

<!--
HAMi ships a small library. The container runtime loads it before your app starts. On NVIDIA it intercepts CUDA calls and replies with your slice. Same pattern for other vendors: ACL calls on Ascend, CNRT on Cambricon. No code changes, no kernel modules, no driver changes. On closed NPU SDKs there is no hijack point: that is the enforcement gap.
-->

Your app calls CUDA. HAMi answers with a slice of the device.

- Small library loaded before your app (`LD_PRELOAD`)
- Intercepts CUDA calls, no app code changes
- No kernel modules, no driver changes
- Same pattern per vendor: ACL on Ascend, CNRT on Cambricon

@col

```pdg
graph dir=LR
app "Your app" shape=round fill=#F6ECD9 stroke=#F1C560 color=#3a2020
lib "HAMi core\n(cuMemAlloc...)" shape=round fill=#fce8e8 stroke=#7A0504 color=#3a2020
gpu "Device slice" shape=round fill=#F6ECD9 stroke=#F1C560 color=#3a2020
app -> lib "CUDA calls"
lib -> gpu "slice only"
```

---

## Why Memory Isolation Matters

@subtitle One bad agent must not kill its neighbors

<!--
Without isolation, one workload can grab all memory and OOM-kill the other tasks on the same device. HAMi enforces memory when it hijacks the runtime calls: every task sees only its own slice.
-->

::: grid {cols=2}
::: card {tag=red}
### {icon:triangle-alert cls=accent-secondary} Without HAMi

Tasks share a device with no borders. One greedy agent eats all memory and kills the neighbors. On a 8 GB Jetson, that is the whole device.
:::
::: card {tag=green}
### {icon:shield-check cls=accent-primary} With HAMi

Each task sees only its slice. Memory is a hard limit, enforced by the hijacked runtime calls: every allocation is checked against your slice.
:::
::: card {tag=yellow}
### {icon:refresh-cw cls=accent-contrast} Time-sharing

Idle memory can be swapped to host RAM, so more agents fit. Great for inference, not for active training.
:::
::: card {tag=cyan}
### {icon:gauge cls=accent-contrast} Per-task limits

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
    nvidia.com/gpumem: 3000
```
3 GB slice on any device. Same YAML works for Ascend, Cambricon and more.
:::
:::

---

## Consumable Capacities

@subtitle Device resources as a pool you draw from

<!--
Device resources are consumable: memory in MiB, compute in % of the device's compute units. The scheduler tracks remaining capacity per device and packs by it. HAMi-core enforces the ceiling on hijacked calls; nvidia-smi inside the pod shows your slice, not the card. Since v2.8 the same semantics exist on the DRA path (ResourceSlice typed capacities, ResourceClaims).
-->

::: grid {cols=2}
::: card {tag=cyan}
### {icon:gauge cls=accent-primary} Memory and compute, separate axes

Request MiB of memory and percent of compute units. What you use is what you get, no fixed profiles.
:::
::: card {tag=green}
### {icon:layers cls=accent-primary} Scheduler packs by remaining capacity

Every device reports memory and compute left. Binpack and spread policies fit requests into the gaps.
:::
::: card {tag=yellow}
### {icon:shield-check cls=accent-contrast} Enforced on hijacked calls

HAMi-core caps every allocation at your slice. Inside the pod, nvidia-smi shows 0 MiB / 4000 MiB.
:::
::: card {tag=red}
### {icon:git-branch cls=accent-contrast} Same semantics on DRA (v2.8+)

Typed ResourceSlice capacities (memory step 1 MiB, cores 0-100). Requests become ResourceClaims.
:::
:::

---

@layout image-right

## Scheduling Policies

@subtitle Binpack & Spread

<!--
Two axes, four patterns. Node binpack saves money, node spread saves uptime. GPU binpack saves whole devices, GPU spread saves tail latency. Pick based on workload: agents want binpack, latency-sensitive serving wants spread.
-->

![Binpack vs Spread scheduling](assets/hami_intro/scheduling_strategies.png)

- **Node binpack** frees whole machines: fewer active nodes, less power
- **Node spread** isolates faults: HA across a device fleet
- **GPU binpack** packs many agents onto one device
- **GPU spread** protects tail latency: one agent per device
- Advanced scheduling works with standalone HAMi; DRA mode can use Yunikorn

---

@layout two-col

## GPU Binpack

@subtitle Fill one device, run many agents

<!--
GPU binpack puts several agents on the same device. Each gets its own slice of memory and compute. This matters most when devices are scarce: on an 8 GB Jetson, four small agents fit where one would have.
-->

- Several agents share one device, each with its own slice of memory and compute
- Prevents fragmentation: scattered small workloads no longer block whole devices
- Frees whole devices for the job that cannot share
- Best for: fleets of small workloads - agent endpoints, batch jobs, dev and test

@col

![GPU Binpack](drawings/gpu_binpack.drawio.png)

---

@layout two-col

## GPU Spread

@subtitle One agent per device, no shared bottlenecks

<!--
GPU spread puts each agent on its own device. No tenant shares compute or memory bandwidth with another. If one agent thrashes its device, the neighbors do not feel it. Use it for latency-sensitive serving.
-->

- One agent per device: compute and memory bandwidth are never shared
- Isolates noisy neighbors: a thrasher on one device does not slow the others
- Protects tail latency: no cross-tenant contention
- Best for: latency-sensitive serving with strict SLOs

@col

![GPU Spread](drawings/gpu_spread.drawio.png)

---

# Part 3: Blueprint

@subtitle Edge AI without a cloud budget

---

## The Blueprint

@subtitle Three steps to a multi-agent edge device

<!--
The path is short. Pick a device: Jetson-class for CUDA compatibility (the HAMi slicing path exists for CUDA). NPUs like DeepX and Axelera have no runtime hook, so HAMi cannot slice them yet: they are the frontier, not today's choice. Slice it: memory in MiB, compute in percent, hard limits per agent. Schedule agents: binpack to pack them tight, spread for SLOs. Everything runs on k3s or k0s, managed with Kubernetes APIs, no ops team needed. Olares is the turnkey path: an open-source, k3s-based personal cloud OS that ships this stack pre-installed, with MCP and GPU scheduling built in, so agents run as standard containers on hardware you own.
-->

::: grid {cols=3}
::: card {tag=green}
### {icon:cpu cls=accent-primary} 1. Pick a device

Jetson-class GPU: CUDA compatibility, the HAMi slicing path. NPUs (DeepX, Axelera) are the frontier: no SDK hook, no slicing today.
:::
::: card {tag=cyan}
### {icon:gauge cls=accent-primary} 2. Slice it

Carve memory and compute into per-agent slices. Hard limits, live repartition, time-sharing when demand exceeds memory.
:::
::: card {tag=yellow}
### {icon:git-branch cls=accent-contrast} 3. Schedule agents

Binpack to pack many agents onto one device. Spread for latency-sensitive serving. Node spread across a device fleet for HA.
:::
:::

- **Deploy on Olares** ([github.com/beclab/olares](https://github.com/beclab/olares)): a k3s-based personal cloud OS that ships this stack pre-installed - agents as containers, MCP built in, local GPU scheduling
- Runs on k3s or k0s directly: Kubernetes APIs without the ops team
- One scheduling plane across heterogeneous accelerators
- Open source: HAMi is a CNCF Incubation project

---

## Demo

@subtitle 3 nodes x 2 A100s: MIG, YOLO, and two vLLMs

<!--
3 nodes with 2 A100s each. One configured for MIG, one running a bunch of YOLO workloads, and two vLLMs scheduled on top. Watch how HAMi packs and isolates them. Video plays inline; PDF shows a frame.
-->

@video assets/demo/llm_test.mp4
---

@layout metrics
## Where HAMi Is Today

@subtitle Production metrics from CNCF case studies

::: grid {cols=4}
::: card {metric}
0
Driver, kernel, code changes needed
SF Technology
:::
::: card {metric}
1-2 GB
Memory per small-model inference service
KE Holdings
:::
::: card {metric}
4x
GPU utilization: 5-10% to 30-50%
NIO
:::
::: card {metric}
90%
GPU infra managed by HAMi on RTX 4070/4090
Prep Edu
:::
:::

@row

::: notes{ tag="green" }
China Merchants Bank - SNOW Corp. - NIO - KE Holdings - DaoCloud - SF Technology - Prep Education - [cncf.io/case-studies](https://www.cncf.io/case-studies/)
:::

---

@layout ecosystem
## Community & Adopters

@subtitle Devices, integrations, and who uses HAMi

<!--
5.2k stars, 325k pulls, 500+ contributors, 27 countries. 11 device types, 20+ adopters. This is the ecosystem slide: show the breadth. The QR code links to github.com/Project-HAMi/HAMi.
-->

#### Open Source, CNCF Backed, Production Ready
::: grid {cols=5}
::: card {metric}
5.2k
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
# Questions? Try HAMi
@side-image assets/brand/ossummit_korea/qr-code.png

@subtitle github.com/Project-HAMi/HAMi

**Got devices we do not support yet? We would love to play with them.**

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI  -  Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh
