---
theme: kubecon_japan
title: "10x Your Neocloud's GPU Utilization with HAMi"
logo: assets/brand/dynamia-logo.svg
logo_dark: assets/brand/dynamia-logo-white.png
footer: "ContainerDays 2026 Singapore"
transition: fade
paginate: true
size: 16:9
style: |
  :root { --bg-image: none; --watermark: none; }
  img[src$=".svg"] { max-height: 360px; }
  img[src*="device-plugin-vs-dra"] { max-height: 240px; }
  .layout-bigtable table { font-size: 1.12em; }
  .layout-bigtable td, .layout-bigtable th { padding: 0.55em 0.8em; }
  .layout-midtable table { font-size: 0.95em; }
  .layout-midtable td, .layout-midtable th { padding: 0.5em 0.7em; }
  .layout-cols:has(img[src*="scheduling-brains"]) { grid-template-columns: 1.5fr 1fr; }
  .layout-title { background: linear-gradient(135deg, #1D1D6B 0%, #3939D8 60%, #0A0A3A 100%); }
  .layout-title h1 { max-width: 70%; }
  .layout-title .kicker { color: rgba(255,255,255,0.88); margin-bottom: 1.1em; }
  .layout-title .subtitle { color: rgba(255,255,255,0.92); font-weight: 500; margin-bottom: 1em; }
  .layout-title .speaker { color: rgba(255,255,255,0.88); margin-top: 0.4em; }
  .layout-title .speaker .role { color: rgba(255,255,255,0.78); }
  .layout-title .speaker-links a { color: rgba(255,255,255,0.9); }
  .layout-title .speaker-links svg { stroke: rgba(255,255,255,0.92); }
  .layout-title .side-image { width: 170px; bottom: 40%; }
  .layout-title .side-image img { width: 170px; max-width: 170px; max-height: none; }
---

<!--
25 min talk, ContainerDays 2026 Singapore, Tuesday Oct 27. Concept A: the blueprint, built bottom-up as the layers of a neocloud.
Sources for every number: research/containerdays-sg-2026/case-studies.md (11 CNCF case studies, cncf.io/case-studies/?_sft_lf-project=hami).
Timing: hook + DRA 4 min, layers 1-3 7 min, sell 4 min, operate + heterogeneous 3 min, overhead + 10x + limits 5 min, recap 2 min.

Open: "Who here sells GPU capacity? Who buys it? Who runs both?" Then: I work with neoclouds and GPU vendors across APAC. This talk is the stack they end up building. No vendor pitch: I will show where it does not work too.
-->
@variant dark
@side-image assets/qr-hami-repo.png
@kicker ContainerDays 2026 Singapore · CNCF Incubating project

# 10x Your Neocloud's GPU Utilization with HAMi

@speaker name="Reza Jelveh" role="Head of Global Market, Dynamia" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

---

## A GPU box is not a GPU cloud

@subtitle Whole-card allocation, measured by seven teams

```seaborn
fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
used, used_l, track = cmap(5.5 / 12), cmap(4.5 / 12), cmap(0.5 / 12)

rows = [
    ("NIO", "CI / testing", 5, 10, "5-10%"),
    ("PREP EDU", "inference", 10, 20, "10-20%"),
    ("CETC Cloud", "embedding, VRAM", 12.5, 12.5, "12.5%"),
    ("Ke Holdings", "whole platform", 13, 13, "13%"),
    ("Zhuoyu", "dev envs, small inference", 0, 15, "<15%"),
    ("Sangfor", "small models", 15, 20, "15-20%"),
    ("Own H200", "time-series inference, SM", 16, 18, "16-18%"),
]

fig, ax = plt.subplots(figsize=(12, 4.7))
fig.patch.set_alpha(0)
ax.set_facecolor("none")
ax.axvspan(5, 20, color=used_l, alpha=0.18, zorder=0)
for i, (org, wl, lo, hi, lab) in enumerate(rows):
    y = len(rows) - 1 - i
    ax.barh(y, 100, color=track, alpha=0.35, height=0.62, zorder=1)
    ax.barh(y, hi, color=used_l, height=0.62, zorder=2)
    if hi > lo and lo > 0:
        ax.barh(y, hi - lo, left=lo, color=used, height=0.62, zorder=3)
    else:
        ax.barh(y, hi, color=used, height=0.62, zorder=3)
    ax.text(-2, y + 0.05, org, ha="right", va="bottom", fontsize=12, color=fg, fontweight="bold")
    ax.text(-2, y + 0.02, wl, ha="right", va="top", fontsize=10, color=dim)
    ax.text(hi + 1.5, y, lab, ha="left", va="center", fontsize=12, color=fg, fontweight="bold")
ax.text(100, len(rows) - 0.35, "one whole card = 100%", ha="right", va="bottom", fontsize=9.5, color=dim)
ax.text(12.5, -0.8, "5-20%", ha="center", va="center", fontsize=10, color=used, fontweight="bold")
ax.set_xlim(-34, 101)
ax.set_ylim(-1.1, len(rows) - 0.1)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
```

Kubernetes default: `nvidia.com/gpu: 1`. The whole card, or nothing.

<!--
2 min. The hook.
Seven different teams, seven workloads, the same answer: a whole card is 5-20% busy.
- NIO: CI/testing on full GPUs at 5-10% (CNCF case study, Mar 2026).
- PREP EDU (Vietnam, on-prem RTX 4070/4090): 10-20% with static allocation.
- CETC Cloud: embedding model held a 64 GB card and needed 8 GB, that is 12.5% of VRAM.
- Ke Holdings: 13% across the whole platform.
- Zhuoyu: Codespaces dev envs and small inference under 15%.
- Sangfor: small models 15-20%, one card one model.
- Our own measurement on Viettel Cloud: a time-series inference job held a whole H200 (141 GB), used 1 GB, SM 16-18%.
A neocloud that rents whole cards sells this waste to its customers, or eats it. A GPU box is cards in a rack. A GPU cloud sells capacity that customers actually use. The rest of the talk is the stack in between, built bottom-up.
-->

---

## DRA is the request, not the sharing

@subtitle Why DRA alone does not fix utilization

![Device plugin vs DRA](assets/hami/device-plugin-vs-dra.png)

::: card {tag=green}
### {icon:file-text cls=accent-primary} Request
ResourceClaims, ResourceSlices, typed capacity. **This is DRA.**
:::
::: card {tag=red}
### {icon:shield cls=accent-secondary} Enforce
Stop a pod from using more than its slice inside the container. **Not DRA.**
:::
::: card {tag=yellow}
### {icon:git-branch cls=accent-contrast} Schedule sharing
Publish fractional capacity, pack slices, respect topology. **Needs a driver and a policy.**
:::

<!--
2 min. Promise 1: why DRA alone does not fix utilization.
DRA gives Kubernetes a clean way to say "I want part of a device". It replaces the device plugin's integer count with ResourceClaims against ResourceSlices. That is the request API.
But a claim is a promise on paper. Something has to make the slice real inside the container: memory limits, compute limits. And something has to decide which slices go on which card, binpack or spread, and which cards sit next to each other.
Sangfor said it best in their case study: "GPU sharing without smart scheduling leads to suboptimal placement; scheduling without GPU virtualization leaves nothing to schedule."
So the stack has more than one layer. Next slide.
-->

---

@layout midtable

## The neocloud stack, bottom-up

@subtitle Five layers between a GPU box and a GPU cloud

| Layer | Job | HAMi piece | Production proof |
| --- | --- | --- | --- |
| {icon:activity cls=accent-contrast} 5 Operate | Measure usage, upgrade, scale ahead | vGPUmonitor, metrics | NIO, SNOW, Zhuoyu |
| {icon:store cls=accent-secondary} 4 Sell | Slices as SKUs, quotas, over-subscription | quota, over-subscription | DaoCloud D.run |
| {icon:file-text cls=accent-primary} 3 Request | Pod asks for memory + compute | device plugin, HAMi-DRA | Sangfor (roadmap) |
| {icon:git-branch cls=accent-primary} 2 Schedule | Capacity model, packing, topology | scheduler extender | CMB, Sangfor, Zhuoyu |
| {icon:shield-check cls=accent-primary} 1 Enforce | Hard memory + compute limit per pod | HAMi-core libvgpu.so | all of them |

<!--
1 min. The map for the rest of the talk. Read it bottom-up: you cannot sell what you cannot enforce, and you cannot enforce what you did not schedule.
Every layer has a production user from the CNCF case studies. HAMi is a CNCF Incubating project; the case studies are on cncf.io.
-->

---

@layout two-col

## Layer 1: enforce the slice

@subtitle vGPU interception, no app or driver changes

- `libvgpu.so` loaded via `/etc/ld.so.preload`
- Every CUDA call passes through it
- **Memory:** over the MiB limit, OOM in this pod only
- **Compute:** token bucket on kernel launches
- `nvidia-smi` in the pod shows the slice

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
    nvidia.com/gpumem: 3000   # MiB
    nvidia.com/gpucores: 30   # % of SMs
```

@col

```pdg
graph dir=TB
app "Your app\n(unchanged)" shape=round
lib "libvgpu.so\nmemory MiB · compute %" shape=round fill=#e3f0ff stroke=#3939D8
drv "CUDA driver" shape=round
gpu "GPU slice\n3000 MiB · 30%" shape=round fill=#e8f5e9 stroke=#2e7d32
app -> lib " CUDA calls"
lib -> drv " within limits"
drv -> gpu
```

<!--
2 min. Promise 2: how vGPU interception enforces memory and compute.
HAMi-core is a small library. The device plugin's Allocate mounts it and writes it into ld.so.preload, so the dynamic linker loads it before the app. It sits in front of the CUDA driver API.
Memory: every allocation is checked against the pod's limit in MiB. Over the limit means out of memory inside this pod; the neighbours keep running. NIO's lesson: VRAM is the hard constraint, an OOM cannot wait, compute shortage can be absorbed by delay.
Compute: a token bucket meters kernel launches so the pod averages its percent of the SMs. Granularity is 1 MiB and 1% on NVIDIA.
nvidia-smi inside the pod reports 3000 MiB total. The app sees a smaller GPU, not a shared one.
No kernel module, no driver change, no image change. SF Technology reports zero changes to driver, kernel, image or source.
Live demo of this exists in the workshop at 12:30.
-->

---

@layout bigtable

## Layer 1: one API, four enforcement mechanisms

@subtitle The request is uniform, the hook depends on the vendor

| Mechanism | Vendors | Granularity | Enforced by |
| --- | --- | --- | --- |
| User-space interception, token bucket | NVIDIA, Ascend | 1 MiB / 1% (CMB vNPU-core: 1 GB / 1%) | `libvgpu.so`, vNPU-core |
| Hardware-honoured static caps | NVIDIA MPS, AMD CU masking | per process, static | GPU hardware scheduler |
| Hardware-fenced partitions | Kunlunxin vXPU, Hygon vDCU, MIG | coarse, fixed profiles | silicon |
| No hook point | DeepX, Axelera | none | scheduler-side accounting only |

`gpucores: 40` means the same thing to the tenant. Underneath, HAMi uses whatever the chip offers.

<!--
1.5 min. Still promise 2, plus promise 7 (domestic chips).
NVIDIA and Ascend have no hardware compute cap, so HAMi intercepts launches in user space: finest granularity, 1%. China Merchants Bank built vNPU-core for Ascend the same way: token bucket for compute, user-space memory management, 1 GB memory / 1% compute (CMB part 1 case study).
AMD CU masking and NVIDIA MPS are caps the hardware scheduler honours, static per process.
Kunlunxin vXPU and Hygon vDCU are fenced in hardware, coarse but silicon-enforced. MIG belongs here too.
And some NPUs (DeepX, Axelera) expose no quota API and no interception point: there you can only account for capacity in the scheduler. That is honest status, not a shipped feature.
For a neocloud this matters: the SKU you sell is the same, the guarantee behind it is not. Know which row each of your chips is in.
-->

---

## Layer 2: schedule what you sliced

@subtitle Capacity model, placement policy, topology

::: grid {cols=3}
::: card {tag=cyan}
### {icon:database cls=accent-primary} Capacity model
Each card reports memory MiB, compute % and a share count. The scheduler fits requests per card, not per node.
:::
::: card {tag=green}
### {icon:layers cls=accent-primary} Binpack or spread
On two axes: which node, which card. Binpack frees whole cards for big jobs, spread avoids noisy neighbours.
:::
::: card {tag=yellow}
### {icon:network cls=accent-contrast} Topology
CMB: paired allocation inside dual-chip modules, **100% of the pool usable**. 3-tier network scoring: **-30% cross-machine** placements.
:::
:::

| Axis | binpack | spread |
| --- | --- | --- |
| Which node | fewer nodes, whole nodes stay free | across nodes |
| Which card | same card, whole cards stay free | across cards, fewer noisy neighbours |

NIO: VRAM is the hard constraint. An OOM cannot wait, a compute shortage can.

<!--
2 min. Promise 3: how the scheduler allocates heterogeneous devices.
Capacity: the device plugin writes every card's memory, cores and share count onto the node. The scheduler extender filters per card: a pod that needs 45 GB stays pending on a node with two 40 GB cards even though the node total fits. That is the workshop's Lab 2.
Policy: binpack and spread exist on the node axis and the card axis, set per pod by annotation. For a neocloud: binpack small tenants so whole cards stay free for whole-card customers.
Topology, from China Merchants Bank part 1: their supernode chips come as dual-chip modules. Odd card counts across modules caused driver errors and left parts of the pool unusable. They enforced paired allocation within a module in the HAMi device plugin and scheduler, and got 100% of the hardware pool usable. Then a three-tier network score (same node, same LEAF, cross LEAF) cut cross-machine scheduling by 30%.
-->

---

@layout two-col

## Layer 2: one isolation layer, several brains

@subtitle Keep HAMi-core, bring your own scheduler

![One isolation layer, several scheduling brains](assets/containerdays/containerdays-scheduling-brains.svg)

@col

| Brain | Who runs it |
| --- | --- |
| **Volcano** gang, queues | Sangfor, SF Technology |
| **Koordinator** quotas, device share | Zhuoyu |
| **Kueue** admission | CMB (training) |
| **KAI** fractions, topology | resource-isolator ships `libvgpu.so` |
| **HAMi extender** | default path |

> "Sharing without smart scheduling leads to suboptimal placement." Sangfor

<!--
1.5 min. Still promise 3.
HAMi is two things: a capacity model plus scheduler extender, and HAMi-core, the isolation library. Other schedulers can replace the brain and keep the isolation.
- Sangfor: Volcano for gang scheduling and LWS, HAMi for GPU virtualization.
- SF Technology: kube-scheduler and Volcano through the HAMi extender and webhook.
- Zhuoyu: Koordinator's Device Share binds the slice, koordlet injects env via NRI, HAMi-Core enforces. Only the isolation layer is HAMi.
- CMB: Kueue admits training, KEDA scales inference, HAMi allocates the accelerators.
- KAI Scheduler (NVIDIA, CNCF Sandbox): since v0.16.4 the kai-resource-isolator delivers the same libvgpu.so.
Full Sangfor quote: "GPU sharing without smart scheduling leads to suboptimal placement; scheduling without GPU virtualization leaves nothing to schedule."
For a neocloud: you probably already picked a batch scheduler. You do not have to replace it.
-->

---

@layout compare

## Layer 3: request through DRA

@subtitle How DRA fits, and where it falls short today

::: card {tag="green"}
### {icon:check cls=accent-primary} How it fits
- **HAMi-DRA** webhook rewrites `nvidia.com/gpu` into ResourceClaims
- Same MiB and % semantics as typed capacity
- Kubernetes 1.34+, DRA Consumable Capacity gate, CDI
:::

::: arrow
{icon:arrow-right size=32}
:::

::: card {tag="red"}
### {icon:triangle-alert cls=accent-secondary} Where it falls short
- No CNCF case study runs DRA sharing in production yet
- Sangfor lists it as future work
- Claim metrics are accounting, not usage
- A claim enforces nothing in the container: Layer 1 still does
:::

::: notes{ tag="green" }
DRA replaces the request API. It does not replace enforcement or packing.
:::

<!--
2 min. Promise 4: how DRA fits, and where it falls short.
HAMi-DRA (github.com/Project-HAMi/HAMi-DRA) is a mutating webhook. It rewrites the classic nvidia.com/gpu, gpumem, gpucores requests into DRA ResourceClaims, so existing Pod specs keep working. Since HAMi v2.8 the same memory MiB and compute % semantics exist as typed ResourceSlice capacities. It needs Kubernetes 1.34+ with the DRA Consumable Capacity feature gate and CDI in the runtime. There is a ResourceClaimTemplate mode for Kueue admission.
Where it falls short, honestly: none of the 11 CNCF case studies runs DRA sharing in production today. Sangfor lists joining the HAMi DRA ecosystem as future work. Allocation metrics from claims are accounting: they tell you what was promised, not what is used. And a claim does not stop a process from allocating more memory: that is still libvgpu.so.
My advice to a neocloud today: build on the device plugin path, keep the Pod API stable, move to DRA underneath when your Kubernetes version and your schedulers are ready. Users will not notice.
-->

---

## Layer 4: sell slices, not cards

@subtitle DaoCloud D.run: a GPU cloud on HAMi

::: grid {cols=4}
::: card {metric}
10,000+
GPU cards under HAMi
:::
::: card {metric}
7
D.run regions, 10+ data centers
:::
::: card {metric}
80%+
Average utilization per card
:::
::: card {metric}
-20-30%
GPU-related opex
:::
:::

::: notes{ tag="green" }
vGPU slices are standard SKUs in a marketplace. Users pay by workload size, not by full card.
:::

> "With HAMi's unified vGPU abstraction, D.run seamlessly manages both NVIDIA and domestic GPUs at scale." DaoCloud

<!--
2 min. Promise 5 and 8: production patterns from cloud providers running 10,000+ GPUs, the neocloud blueprint.
DaoCloud CNCF case study (Dec 2025). D.run is their public GPU cloud for developers and small teams; DCE is their private Kubernetes platform for enterprises. Mainland China plus Hong Kong.
- HAMi is active on 10,000+ GPU cards, DaoCloud-operated and customer-owned.
- 7 active D.run regions, 10+ data centers, single regions up to about 3,000 GPUs.
- More than 80% average utilization per card.
- 20-30% lower GPU-related opex, and faster regional expansion.
DaoCloud is one of HAMi's earliest contributors: over-subscription, node config and heterogeneous hardware went upstream from them.
Quote: "With HAMi's unified vGPU abstraction, D.run seamlessly manages both NVIDIA and domestic GPUs at scale." (Captain, AI/LLM Infra Product Lead)
Note: they give no "before" number, so I do not claim a multiplier for them.
-->

---

@layout two-col

## Layer 4: from card to SKU

@subtitle The D.run model, step by step

```pdg
graph dir=TB
pool "Card pool\nNVIDIA + domestic" shape=round fill=#e3f0ff stroke=#3939D8
slice "vGPU slices\nmemory + compute" shape=round fill=#e8f5e9 stroke=#2e7d32
sku "SKU catalog\npay by workload size" shape=round fill=#fff9e6 stroke=#f9a825
pub "D.run marketplace\npublic cloud" shape=round
ent "DCE quotas + RBAC\nenterprise pool" shape=round
pool -> slice " HAMi-core"
slice -> sku " package"
sku -> pub
sku -> ent
```

@col

| Step | What D.run does |
| --- | --- |
| **Define** | Slice cards into vGPU units with fixed memory + compute |
| **Package** | Standard SKUs in a central marketplace |
| **Fill** | Controlled over-subscription lifts card utilization |
| **Govern** | Quotas + RBAC at vGPU level, per department and queue |
| **Expand** | One abstraction over NVIDIA + domestic, region by region |

<!--
2 min. The centerpiece, still promises 5 and 8.
This is the blueprint, as DaoCloud describes it in their case study:
1. Define the unit: a vGPU slice with defined memory and compute. That is Layer 1.
2. Package slices as standardized SKUs in a central marketplace. The customer buys by workload size, not by the card. A 7B inference endpoint does not need an H100; it needs a slice.
3. Fill: controlled over-subscription. Not every tenant peaks at once, so you sell slightly more than the physical card, with the scheduler watching. DaoCloud contributed over-subscription upstream.
4. Govern: on DCE, the private platform, quotas and RBAC are enforced at vGPU level, for department and queue limits. That is how an enterprise tenant gets a predictable share.
5. Expand: NVIDIA and domestic GPUs under the same abstraction, so a new region can launch with whatever the supply chain delivers.
The case study does not publish SKU sizes or prices, so I do not show any. Your SKUs come from your workload profiles: CETC's lesson is to start from workload profiles, not a preset partition ratio.
-->

---

## Layer 5: operate it

@subtitle Allocation is not utilization

::: grid {cols=3}
::: card {tag=cyan}
### {icon:chart-bar cls=accent-primary} Measure usage
Two numbers, two dashboards. HAMi scheduler `:9395` reports allocation, vGPUmonitor `:9394` reports usage.
:::
::: card {tag=green}
### {icon:refresh-cw cls=accent-primary} Upgrade safely
NIO: blue-green device plugin upgrades for inference, phased rollout, performance validated on every version.
:::
::: card {tag=yellow}
### {icon:trending-up cls=accent-contrast} Scale ahead
SNOW: KEDA scales on queue saturation, ahead of model warm-up. **700%** viral spike handled, **2x** fewer GPUs.
:::
:::

```seaborn
fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
alloc, used, track = cmap(1.5 / 12), cmap(5.5 / 12), cmap(0.5 / 12)

fig, ax = plt.subplots(figsize=(12, 2.1))
fig.patch.set_alpha(0)
ax.set_facecolor("none")
for y, v, c, name, sub, lab in [
    (1, 95, alloc, "Allocation", "scheduled / schedulable cards", ">95%"),
    (0, 55, used, "Utilization", "mean SM util, node telemetry", ">55%"),
]:
    ax.barh(y, 100, color=track, alpha=0.35, height=0.6)
    ax.barh(y, v, color=c, height=0.6)
    ax.text(-1.5, y + 0.03, name, ha="right", va="bottom", fontsize=12, color=fg, fontweight="bold")
    ax.text(-1.5, y + 0.01, sub, ha="right", va="top", fontsize=9, color=dim)
    ax.text(v - 1.5, y, lab, ha="right", va="center", fontsize=12, color="white", fontweight="bold")
ax.annotate("", xy=(95, -0.42), xytext=(55, -0.42), arrowprops=dict(arrowstyle="<->", color=dim, linewidth=1.3))
ax.text(75, -0.5, "reserved, not busy", ha="center", va="top", fontsize=10, color=fg, fontweight="bold")
ax.text(-30, 1.55, "ZHUOYU, SAME FLEET, TWO NUMBERS", fontsize=10, color=dim, family="monospace")
ax.set_xlim(-30, 101)
ax.set_ylim(-0.95, 1.75)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
```

<!--
1.5 min. Production patterns, part 2 (promise 5).
Measure: Zhuoyu publishes clean definitions. Allocation = scheduled cards / schedulable cards. Utilization = mean SM utilization from node telemetry. They hit >95% allocation and >55% utilization overall, ~60% on shared inference. If you only watch allocation you will think you are full while the silicon idles. HAMi exposes both: scheduler metrics on 9395 are reservations, vGPUmonitor on 9394 is usage. Price from one, plan capacity from the other.
Upgrade: NIO validates performance on every HAMi version upgrade, allows mixed versions during phased rollout, and uses blue-green style device plugin upgrades for inference.
Scale: SNOW Corp (Korea, 1,000+ A100s) scales on unacked_messages / active_consumers at ~0.7 so new replicas are warm before the queue explodes. They handled a 700% viral traffic spike (the Ghibli filter trend) and need 2x fewer GPUs for train plus inference pipelines, because trainer and inference engine share one GPU in the same pod. Honest attribution: SNOW credits most savings to KEDA; HAMi for sharing and avoiding a re-architecture.
-->

---

@layout compare

## One pool, every vendor

@subtitle Domestic chips as first-class citizens

::: card {tag="red"}
### {icon:server cls=accent-secondary} One cluster per delivery
CMB, without HAMi: **8+ clusters**, each with its own device plugin, scheduling policy, monitoring and runbooks.
:::

::: arrow
{icon:arrow-right size=32}
:::

::: card {tag="green"}
### {icon:layers cls=accent-primary} One heterogeneous pool
Kunlunxin, Ascend, NVIDIA, PPU, Moore Threads, MetaX: ~10,000 cards. **99%** of compute under one management, utilization **35% → 60%+**.
:::

::: notes{ tag="green" }
DaoCloud: NVIDIA + domestic under one vGPU abstraction. SF Technology: Ascend, Kunlun, Sunway. No vendor lock-in.
:::

<!--
1.5 min. Promise 7: domestic chips as first-class citizens.
China Merchants Bank part 1 and 2 (Jul and Sep 2026). Their accelerator deliveries are a mix: Kunlunxin, several Ascend models, NVIDIA, PPUs, Moore Threads, MetaX. Without a common layer, every delivery would become its own Kubernetes cluster: 8+ clusters, each with its own device plugin, scheduling policy, monitoring and runbooks. With HAMi: about 10,000 heterogeneous cards, 99% of accelerator compute under unified management, average utilization 35% to 60%+. CMB is careful to say the improvement cannot be attributed to any single component: Kueue, KEDA, Fluid and HAMi together.
DaoCloud manages NVIDIA and domestic GPUs under the same abstraction and calls domestic vendors first-class citizens. SF Technology runs Ascend, Baidu Kunlun and Sunway.
Supported list per the CETC case study: NVIDIA, Ascend, Cambricon, Hygon, Iluvatar CoreX, Moore Threads, MetaX, Enflame, Kunlunxin, AWS Neuron, Vastai.
For a neocloud in APAC: you buy what the supply chain delivers. The pool should not care.
-->

---

@layout two-col

## Overhead and best-fit workloads

@subtitle What production users share, and what they keep whole

- **CETC:** embedding on 8 GB / 20% compute, throughput **within 5%**, p95 unchanged
- **NIO:** **1/6 GPU** best for simulation, **1/8** lowered throughput
- **CMB:** ResNet50 per card **64.6 → 94.8 img/s** with partitioning
- **Own:** notebook at 70% cores, 1 h run **+20 min**

@col

| Workload | Run on | Who |
| --- | --- | --- |
| CI, dev envs, notebooks | HAMi slice | NIO, CETC, Zhuoyu |
| Small, bursty inference | HAMi slice | Ke, Sangfor, DaoCloud, SF |
| Embedding, simulation | HAMi slice | CETC, NIO |
| Hard isolation | MIG | NIO |
| Large training, LLMs | whole cards | Ke, CMB, NIO, CETC |

<!--
2 min. Promise 6: overhead expectations and best-fit workloads.
Overhead is real but small where the workload fits:
- CETC Cloud: embedding model moved from a whole 64 GB card to 8 GB and 20% compute. Token throughput within 5% of whole-card, p95 latency and model load time essentially identical.
- NIO: finer is not better. About 1/6 of a GPU was optimal for simulation; at 1/8 scheduling and virtualization overhead reduced throughput. NIO also says plainly that HAMi introduces some overhead compared to full GPU allocation.
- CMB: ResNet50 inference, batch 32: one card went from 64.6 to 94.8 images/s (+46.7%) with finer partitioning, because more work runs concurrently.
- Our own Viettel notebook: capping to 70% of cores cost 20 minutes on a 1 hour training run. That is the price of a guaranteed neighbour slice, paid on purpose.
Best fit, from the case studies: Ke, Sangfor, DaoCloud, SF, PREP and NIO share small or bursty inference; CETC and Zhuoyu share dev environments; NIO and SF share CI. NIO puts algorithm development on MIG for hard isolation. Ke, CMB, NIO and CETC keep large training and large LLM serving on whole cards.
Rule of thumb: share what is small, bursty, interactive or latency-tolerant.
-->

---

## Where the 10x comes from

@subtitle Per workload: yes. Whole platform: 2-3x

```seaborn
fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
wl, wl_l, pf = cmap(5.5 / 12), cmap(4.5 / 12), cmap(1.5 / 12)

rows = [
    ("CETC Cloud", "dev pods per device, 2 → 30", 15, None, "15x", wl),
    ("NIO", "CI GPU util, 5% → 30-50%", 10, 4, "4-10x", wl),
    ("Sangfor", "models per GPU, 1 → 8+", 8, None, "8x", wl),
    ("Own H200", "req/s per card at p95 160 ms", 3.4, None, "3.4x", wl),
    ("Sangfor", "GPU utilization", 3, None, ">3x", pf),
    ("Ke Holdings", "platform util, 13% → 37%", 2.8, None, "2.8x", pf),
    ("SNOW", "GPUs for train + inference, 2 → 1", 2, None, "2x", pf),
    ("CMB", "avg accelerator util, 35% → 60%+", 1.7, None, "1.7x", pf),
]

fig, ax = plt.subplots(figsize=(12, 5.8))
fig.patch.set_alpha(0)
ax.set_facecolor("none")
for i, (org, metric, v, lo, lab, c) in enumerate(rows):
    y = len(rows) - 1 - i
    if lo:
        ax.barh(y, lo, color=c, height=0.62)
        ax.barh(y, v - lo, left=lo, color=wl_l, height=0.62)
    else:
        ax.barh(y, v, color=c, height=0.62)
    ax.text(-0.25, y + 0.04, org, ha="right", va="bottom", fontsize=12, color=fg, fontweight="bold")
    ax.text(-0.25, y + 0.02, metric, ha="right", va="top", fontsize=10, color=dim)
    ax.text(v + 0.25, y, lab, ha="left", va="center", fontsize=12, color=fg, fontweight="bold")
ax.plot([10, 10], [-0.6, len(rows) - 0.4], color=dim, linewidth=1.2, linestyle=(0, (4, 3)))
ax.text(10, len(rows) - 0.35, "10x", ha="center", va="bottom", fontsize=10, color=dim, fontweight="bold")
ax.text(16.8, 5.5, "per workload\nbaseline 5-15%", ha="right", va="center", fontsize=10.5, color=wl, fontweight="bold")
ax.text(16.8, 1.5, "whole platform\ntraining already\nuses its cards", ha="right", va="center", fontsize=10.5, color=pf, fontweight="bold")
ax.set_xlim(-6.2, 17)
ax.set_ylim(-0.7, len(rows) + 0.1)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
```

<!--
1.5 min. The honest version of the title.
Red bars are single workload classes, blue bars are whole platforms.
- CETC Cloud: 2 to 30 concurrent dev pods on the same device, 15x.
- NIO: CI GPU utilization from 5% to 30-50%. Their text says about 4x, the CNCF headline box says 10x: the range is 4-10x depending on where in 5-10% you start.
- Sangfor: 1 to 8+ models per GPU.
- Our own H200: 20.7 to 71.1 req/s per card at the same p95 of 160 ms, 3.4x, with HAMi plus KEDA.
- Sangfor GPU utilization overall: more than 3x.
- Ke Holdings platform: 13% to 37%, about 3x.
- SNOW: 2x fewer GPUs for training plus inference pipelines.
- CMB: 35% to 60%+ average accelerator utilization.
So: 10x is real where the baseline is 5-15%: CI, dev, notebooks, embedding, small inference. A whole platform lands at 2-3x because big training already uses its cards. For a neocloud whose customers are mostly small inference and dev, your mix decides where you land.
-->

---

## Honest limits

@subtitle No vendor pitch: where this does not work

::: grid {cols=3}
::: card {tag=red}
### {icon:shield-off cls=accent-secondary} Not a sandbox
For trusted tenants only. `CUDA_DISABLE_CONTROL`, static CUDA, direct ioctls bypass it.
:::
::: card {tag=yellow}
### {icon:lock cls=accent-contrast} MIG for hard isolation
NIO: algorithm dev on MIG. Untrusted tenants: MIG or whole cards.
:::
::: card {tag=yellow}
### {icon:cpu cls=accent-contrast} Training stays whole
Ke, CMB, NIO, CETC keep big training and big LLMs on whole cards.
:::
::: card {tag=red}
### {icon:ruler cls=accent-secondary} Finer is not better
NIO: 1/8 GPU slower than 1/6. Interception can clash with pointer analysis.
:::
::: card {tag=cyan}
### {icon:chart-bar cls=accent-primary} Reserved is not used
Usage needs a runtime collector. Per-tenant telemetry varies by vendor.
:::
::: card {tag=cyan}
### {icon:flask-conical cls=accent-primary} DRA is early
No production case study yet. Upgrades need perf validation (NIO).
:::
:::

<!--
2 min. Promise 9: no vendor pitch. Say these out loud.
- Soft isolation is a resource and fairness control for trusted workloads, not a security boundary. Setting CUDA_DISABLE_CONTROL=true skips the libvgpu.so preload; a statically linked CUDA runtime or direct /dev/nvidia* ioctls bypass it too. On a public neocloud, do not sell HAMi slices to mutually untrusted tenants as if they were VMs.
- MIG where you need hard isolation: NIO runs algorithm development on MIG, HAMi for CI, inference and simulation, time-slicing for contention-tolerant work.
- Training stays on whole cards at Ke, CMB, NIO and CETC.
- Finer is not better: NIO found 1/8 GPU slower than 1/6. NIO also found that some compiler and library features doing pointer or address analysis conflict with GPU interception.
- Allocation is not utilization: claim and scheduler metrics are accounting. Live usage needs a runtime collector. Per-tenant telemetry is uneven: AMD has no first-party per-tenant path today.
- DRA: no CNCF case study runs it in production. Upgrades need performance validation and phased rollout (NIO).
-->

---

## The blueprint

@subtitle GPU box to GPU cloud, in six checks

::: grid {cols=3}
::: card {tag=cyan}
### {icon:shield-check cls=accent-primary} 1. Enforce
Hard memory + compute limit per pod. Know which chips use interception and which are hardware-fenced.
:::
::: card {tag=cyan}
### {icon:git-branch cls=accent-primary} 2. Schedule
Per-card capacity, binpack for small tenants, topology for modules and network. Keep your batch scheduler.
:::
::: card {tag=cyan}
### {icon:file-text cls=accent-primary} 3. Request
Stable Pod API now. DRA underneath when your Kubernetes and scheduler are ready.
:::
::: card {tag=green}
### {icon:store cls=accent-primary} 4. Sell
Slices as SKUs from workload profiles. Quotas + RBAC at vGPU level. Over-subscribe with care.
:::
::: card {tag=green}
### {icon:activity cls=accent-primary} 5. Operate
Price from allocation, plan from usage. Blue-green upgrades. Scale on saturation.
:::
::: card {tag=yellow}
### {icon:layers cls=accent-contrast} 6. Pool everything
One pool for every vendor. Whole cards and MIG where sharing does not fit.
:::
:::

<!--
1.5 min. Recap, promise 8.
If you take one slide home, take this one. Bottom-up:
1. Enforce: hard memory and compute limits per pod. Map your chips to the four mechanisms.
2. Schedule: per-card capacity, binpack small tenants to keep whole cards free, topology for dual-chip modules and network tiers (CMB). Keep the batch scheduler you have: Volcano, Kueue, Koordinator or KAI.
3. Request: keep the Pod API stable; HAMi-DRA lets you move underneath later.
4. Sell: slices as SKUs, derived from workload profiles (CETC), quotas and RBAC at vGPU level, over-subscription under control (DaoCloud).
5. Operate: two metric families, blue-green device plugin upgrades (NIO), proactive scaling (SNOW).
6. Pool everything: one pool for NVIDIA and domestic chips (CMB, DaoCloud). Whole cards and MIG where sharing does not fit.
That is how DaoCloud runs 10,000+ cards above 80% per card.
-->

---

@variant dark
@side-image assets/qr-hami-repo.png
@kicker CNCF Incubating · 4,900+ stars · 500+ contributors · hundreds of enterprises

# Thank you

@subtitle github.com/Project-HAMi/HAMi

@speaker name="Reza Jelveh" role="Head of Global Market, Dynamia" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

<!--
Questions. Hands-on: the HAMi workshop at ContainerDays, today 12:30, github.com/Project-HAMi/hami-workshop.
Numbers: 4,900+ GitHub stars (4,929 via GitHub API on 2026-10-24), 500+ contributors from 20+ countries and production at hundreds of enterprises (CETC case study, Sep 2026).
All case studies: cncf.io/case-studies/?_sft_lf-project=hami
-->

---

@hidden

## Backup: one H200, one job

@subtitle Our own measurement, Viettel Cloud

```seaborn
fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
red, yellow, track = cmap(5.5 / 12), cmap(6.5 / 12), cmap(0.5 / 12)

fig, ax = plt.subplots(figsize=(10.5, 2.9))
fig.patch.set_alpha(0)
ax.set_facecolor("none")
ax.text(-40, 1.75, "GPU MEMORY: ALLOCATED VS USED", fontsize=10.5, color=dim, family="monospace")
ax.barh(1, 141, color=track, alpha=0.5, height=0.5)
ax.barh(1, 1, color=red, height=0.5)
ax.barh(0, 141, color=track, alpha=0.5, height=0.5)
ax.barh(0, 39, color=yellow, height=0.5)
ax.text(-4, 1, "Time-series\n(inference)", ha="right", va="center", fontsize=12, color=fg, fontweight="bold", linespacing=1.4)
ax.text(-4, 0, "Defect detection\n(training)", ha="right", va="center", fontsize=12, color=fg, fontweight="bold", linespacing=1.4)
ax.text(6, 1, "1 GB used, SM 16-18%", ha="left", va="center", fontsize=11.5, color=fg)
ax.text(44, 0, "39 GB used", ha="left", va="center", fontsize=11.5, color=fg)
ax.text(141, 1.42, "one whole H200 = 141 GB", ha="right", va="bottom", fontsize=10.5, color=dim)
ax.annotate("", xy=(139, -0.55), xytext=(41, -0.55), arrowprops=dict(arrowstyle="<->", color=dim, linewidth=1.4))
ax.text(90, -0.74, "~100 GB free", ha="center", va="top", fontsize=11, color=fg, fontweight="bold")
ax.set_xlim(-40, 148)
ax.set_ylim(-1.15, 1.95)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
```

- Native: **20.7 req/s** per card at p95 160 ms. HAMi + KEDA, 10 replicas: **71.1 req/s**, same p95: **3.4x**
- SM 18% → 31% → 54% → 100% at 1 / 2 / 5 / 10 replicas. Bigger batches (32 → 512) left the GPU at 7-10%

<!--
Backup if asked "did you measure this yourselves". From drawings.md / Viettel Cloud deck.
Same 71 req/s natively needs ~3.4 cards: ~71% fewer cards, ~51% less power, ~$7k/month at an example $4/GPU-h (example price, not a quote).
HAMi does not make one pod faster; it fills the card that was idle.
-->

---

@hidden

## Backup: stable while shared

@subtitle Epoch-time jitter (CV) of a training notebook on a shared H200

```seaborn
fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
red, green = cmap(5.5 / 12), cmap(3.5 / 12)

fig, ax = plt.subplots(figsize=(6.5, 3.0))
fig.patch.set_alpha(0)
ax.set_facecolor("none")
for x, v, c, lab in [(0, 1, green, "alone"), (1, 19, red, "shared, no cap"), (2, 9, green, "shared, capped")]:
    ax.bar(x, v, width=0.56, color=c)
    ax.text(x, v + 0.8, f"{v}%", ha="center", va="bottom", fontsize=14, color=fg, fontweight="bold")
    ax.text(x, -1.4, lab, ha="center", va="top", fontsize=11, color=dim)
ax.set_xlim(-0.65, 2.65)
ax.set_ylim(-4, 24)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
```

The `force` cap halves the jitter. It isolates stability, not throughput: for hard throughput isolation, use MIG.

<!--
Backup if asked about noisy neighbours. Own measurement (drawings.md): CV = std dev / mean of epoch time. Alone ~1%, shared with bursty inference and no cap 19%, shared with force cap 9%.
-->

---

@hidden

## Backup: the same request, any vendor

@subtitle One API, no code changes

::: grid {cols=2}
::: card {tag=cyan}
### NVIDIA: 15 GB and 30%
```yaml
resources:
  limits:
    nvidia.com/gpu: 1
    nvidia.com/gpumem: 15000
    nvidia.com/gpucores: 30
```
:::
::: card {tag=green}
### Ascend 910C: 8 GB and 20%
```yaml
resources:
  limits:
    huawei.com/Ascend910C: "1"
    huawei.com/Ascend910C-core: "20"
    huawei.com/Ascend910C-memory: "8192"
```
:::
:::

Supported per CETC case study: NVIDIA, Ascend, Cambricon, Hygon, Iluvatar CoreX, Moore Threads, MetaX, Enflame, Kunlunxin, AWS Neuron, Vastai.

<!--
Backup for "how does a tenant ask for a slice". YAML from the workshop deck (gpu_workshop.md).
-->

---

@hidden

@layout image-right

## Backup: DRA ResourceClaim

@subtitle What HAMi-DRA generates from nvidia.com/gpu requests

![ResourceClaim and ResourceClaimTemplate](assets/hami/dra-resource-claim.png)

- **DeviceClass:** devices with one resource model
- **ResourceClaim:** a workload's ticket to hardware
- **ResourceClaimTemplate:** one claim per Pod, used for Kueue admission
- HAMi-DRA: Kubernetes 1.34+, Consumable Capacity gate, CDI

<!--
Backup for DRA deep-dive questions. github.com/Project-HAMi/HAMi-DRA.
-->

---

@hidden

## Backup: sources

@subtitle CNCF case studies used in this talk

| Organisation | Used for | Date |
| --- | --- | --- |
| DaoCloud | D.run blueprint, 10,000+ cards, >80%, -20-30% opex | Dec 2025 |
| China Merchants Bank 1 + 2 | 8+ clusters avoided, topology, 35% → 60%+ | Jul + Sep 2026 |
| Sangfor | Volcano, 1 → 8+ models per GPU, >3x | Sep 2026 |
| NIO | CI 5% → 30-50%, finer is not better, MIG, upgrades | Mar 2026 |
| SNOW Corp | KEDA saturation scaling, 700% spike, 2x fewer GPUs | May 2026 |
| Ke Holdings | 13% → 37%, whole cards for training | Feb 2026 |
| Zhuoyu | Koordinator, allocation >95% vs utilization >55% | Sep 2026 |
| CETC Cloud | 2 → 30 dev pods, within 5% throughput | Sep 2026 |
| SF Technology | zero app changes, Ascend / Kunlun / Sunway | Sep 2025 |
| PREP EDU | 10-20% baseline, Vietnam on-prem | Aug 2025 |

<!--
All at cncf.io/case-studies/?_sft_lf-project=hami (read 2026-10-24).
-->
