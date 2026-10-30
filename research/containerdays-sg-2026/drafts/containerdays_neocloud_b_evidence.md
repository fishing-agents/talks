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
  .layout-title { background: linear-gradient(135deg, #1D1D6B 0%, #3939D8 60%, #0A0A3A 100%); }
  .layout-title h1 { max-width: 70%; }
  .layout-title .kicker { color: rgba(255,255,255,0.88); margin-bottom: 1.1em; }
  .layout-title .subtitle { color: rgba(255,255,255,0.92); font-weight: 500; margin-bottom: 1em; }
  .layout-title .speaker { color: rgba(255,255,255,0.88); margin-top: 0.4em; }
  .layout-title .speaker .role { color: rgba(255,255,255,0.78); }
  .layout-title .speaker-links a { color: rgba(255,255,255,0.9); }
  .layout-title .speaker-links svg { stroke: rgba(255,255,255,0.92); }
  .layout-title .side-image { width: 170px; bottom: 40%; }
  .layout-title .subtitle { white-space: nowrap; }
  .layout-timeline-horizontal .card { max-width: 11em; font-size: 0.88em; }
  .slide-body > .grid + .grid { margin-top: 0.8em !important; }
  .layout-title .side-image img { width: 170px; max-width: 170px; max-height: none; }
  .layout-dense table { font-size: 0.8em; }
  .layout-dense th, .layout-dense td { padding: 0.28em 0.55em; }
  .layout-table-md table { font-size: 0.84em; }

---

<!--
25 min talk, ContainerDays 2026 Singapore, Tuesday Oct 27. Concept B: the evidence deck.
Spine: 11 CNCF case studies from 10 organisations, plus our own H200 measurement. Every number on these slides comes from one of those studies; the company is named in the notes of each slide.
Timing: hook and who 4 min, mechanism 7 min, results 6 min, limits and blueprint 5 min, buffer 3 min.
Opening line: "I'm not going to tell you what HAMi can do. I'm going to show you what ten production users measured, including the parts that did not work."
Facts if asked: CNCF Incubating project, 4,900+ GitHub stars, 500+ contributors from 20+ countries, in production at hundreds of enterprises (CETC case study wording).
-->
@variant dark
@side-image assets/qr-hami-repo.png
@kicker ContainerDays 2026 Singapore · CNCF Incubating project

# 10x Your Neocloud's GPU Utilization with HAMi

@subtitle What ten production users measured

@speaker name="Reza Jelveh" role="Head of Global Market, Dynamia" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

---

## Seven organisations measured the same 5-20%

@subtitle Whole-card utilization before sharing, as each one reported it

```seaborn
import matplotlib.pyplot as plt

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
used = cmap(5.5 / 12)
used_l = cmap(4.5 / 12)
track = "#e5e7eb"

fig, ax = plt.subplots(figsize=(11.4, 4.3))
fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
ax.set_facecolor("none")
fig.patch.set_alpha(0)

rows = [
    ("NIO", "CI / testing", 5, 10, "5-10%", "range"),
    ("PREP EDU", "inference, RTX 4070/4090", 10, 20, "10-20%", "range"),
    ("CETC Cloud", "embedding model, VRAM", 12.5, 12.5, "12.5%", "point"),
    ("Ke Holdings", "whole platform", 13, 13, "13%", "point"),
    ("Zhuoyu", "dev envs, small inference", 0, 15, "<15%", "upper"),
    ("Sangfor", "small models", 15, 20, "15-20%", "range"),
    ("Own H200", "time-series inference, SM", 16, 18, "16-18%", "range"),
]
n = len(rows)
for i, (org, what, lo, hi, txt, kind) in enumerate(rows):
    y = n - 1 - i
    ax.barh(y, 100, color=track, height=0.66, zorder=1)
    if kind == "upper":
        ax.barh(y, hi, color=used_l, height=0.66, hatch="///", edgecolor=used, linewidth=0, zorder=2)
    else:
        ax.barh(y, lo, color=used, height=0.66, zorder=2)
        if hi > lo:
            ax.barh(y, hi - lo, left=lo, color=used_l, height=0.66, zorder=2)
    ax.text(hi + 1.5, y, txt, ha="left", va="center", fontsize=14, color=fg, fontweight="bold", zorder=3)
    ax.text(33.5, y, what, ha="left", va="center", fontsize=12, color=dim, zorder=3)
    ax.text(-1.5, y, org, ha="right", va="center", fontsize=14, color=fg, fontweight="bold")

ax.text(100, n - 0.5, "one whole card = 100%", ha="right", va="bottom", fontsize=12, color=dim)
ax.text(-19, n - 0.5, "SOLID = LOW END   LIGHT = REPORTED RANGE   HATCHED = UPPER BOUND ONLY",
        ha="left", va="bottom", fontsize=10, color=dim, family="monospace")
ax.set_xlim(-19, 100.5)
ax.set_ylim(-0.5, n + 0.1)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.set_xticks([])
```

Different industries, chips and countries. Most of every card: paid for and idle.

<!--
2 min. This is the whole talk in one chart. Seven independent measurements, before any sharing:
- NIO (autonomous driving), CI/testing on full GPUs: 5-10%. CI is mostly CPU: compile, fetch, preprocess.
- PREP EDU (Vietnam, EdTech, consumer RTX cards): 10-20% with static allocation.
- CETC Cloud: an embedding model held a whole 64 GB card and used 8 GB: 12.5% of VRAM. That one is memory, not SM.
- Ke Holdings: 13% across the whole platform, thousands of GPUs.
- Zhuoyu: dev environments (Codespaces) and small inference below 15%. They only gave an upper bound, so the bar is hatched.
- Sangfor: small models 15-20%, one card one model.
- Our own H200: a time-series inference job used 1 GB of 141 GB, SM 16-18%.
The chart shows ranges as ranges; I did not average anything. Different units (SM, VRAM, platform average) are labelled.
Line to land: nobody here has a capacity problem. They have an allocation problem.
-->

---

@layout dense

## Who measured it

@subtitle 11 CNCF case studies, 10 organisations

| Organisation | What they run | Region | Scale |
| --- | --- | --- | --- |
| DaoCloud | GPU cloud (D.run) + enterprise platform | China, Hong Kong {icon:map-pin cls=accent-secondary} | 10,000+ cards {icon:server cls=accent-primary}, 7 regions |
| China Merchants Bank | Bank, private AI platform | China | ~10,000 cards {icon:server cls=accent-primary}, many vendors |
| SNOW Corp. | Consumer GenAI, 200M+ users | South Korea {icon:map-pin cls=accent-secondary} | 1,000+ A100s |
| PREP EDU | EdTech, on-prem | Vietnam {icon:map-pin cls=accent-secondary} | RTX 4070 / 4090 |
| Ke Holdings | Housing platform ML | China | Thousands of GPUs, 5 clusters |
| NIO | Autonomous driving | China | ~600 GPUs |
| Zhuoyu | Autonomous driving cloud | China | 300K-800K pods/day |
| Sangfor | Enterprise cloud, security | China | 2,000+ R&D engineers |
| SF Technology | Logistics | China | 65 services on 28 GPUs |
| CETC Cloud | Edge knowledge appliance | China | 8 mixed GPUs per box |

{icon:map-pin cls=accent-secondary} APAC beyond mainland China · {icon:server cls=accent-primary} 10,000+ cards in production

<!--
1.5 min. Not a logo slide: these are the people whose numbers I use for the rest of the talk.
Two of them run 10,000+ cards: DaoCloud (a GPU cloud provider, D.run public cloud plus DCE private platform, mainland China and Hong Kong, 7 D.run regions, 10+ data centers, single regions up to about 3,000 GPUs) and China Merchants Bank (about 10,000 heterogeneous accelerators, 99% of compute under unified management). CMB is a bank, not a cloud, but it is run like an internal cloud.
APAC outside China: SNOW Corp in Korea (NAVER subsidiary, SNOW, EPIK, B612 apps, 1,000+ A100s), PREP EDU in Vietnam (small on-prem team on consumer RTX cards), DaoCloud's Hong Kong regions. Our own measurements come from work with Viettel Cloud in Vietnam.
Sources: cncf.io/case-studies, filter project HAMi. China Merchants Bank has two studies (Jul and Sep 2026).
-->

---

@layout compare

## Why DRA alone did not fix it

@subtitle DRA is how you ask. Sharing is what happens after.

::: card {tag="cyan"}
### {icon:file-text cls=accent-primary} DRA gives you
- A request API: ResourceClaims instead of `nvidia.com/gpu: 1`
- Consumable capacity (K8s 1.34+): ask for MiB and % of a device
- Allocation records: who reserved what
:::

::: arrow
{icon:arrow-right size=32}
:::

::: card {tag="green"}
### {icon:cpu cls=accent-primary} Sharing still needs
- **Enforcement** in the container: memory and compute caps
- A **sharing-aware scheduler**: binpack, topology, quotas
- **Vendor hooks** for every chip in the pool
:::

::: notes {tag="green"}
None of the 11 case studies runs DRA in production yet: Sangfor lists it as future work. HAMi-DRA keeps the Pod YAML and turns it into ResourceClaims.
:::

<!--
1.5 min. Promise from the abstract: why DRA alone does not fix utilization, how it fits, where it falls short.
DRA is a better request API. It replaces "one whole device" with a claim that can say "this much memory, this share of compute". It does not put a limit inside the container: a claim for 8 GB is a number in the API server until something enforces it on the device. And it does not decide how to pack slices onto cards.
Sangfor said it best: "GPU sharing without smart scheduling leads to suboptimal placement; scheduling without GPU virtualization leaves nothing to schedule."
Where it falls short today: in the case studies, nobody runs it in production yet. Sangfor lists joining the HAMi DRA ecosystem as future work. DRA allocation metrics are accounting, not usage.
How it fits: HAMi-DRA is a mutating webhook that rewrites nvidia.com/gpu requests into ResourceClaims. Needs Kubernetes 1.34+ with the DRA consumable capacity feature gate and CDI. Same slice semantics since HAMi v2.8. A ResourceClaimTemplate mode exists for Kueue. So DRA is the front door; enforcement and scheduling stay the same layer.
-->

---

@layout two-col

## How the sharing is enforced

@subtitle HAMi-core in every shared container

- **`libvgpu.so`** loaded via `ld.so.preload`: intercepts the CUDA calls
- **Memory** counted in MiB: past the limit, OOM inside that Pod only
- **Compute** throttled by a token bucket in 1% steps
- `nvidia-smi` in the Pod shows the slice, not the card
- No driver, kernel, image or code changes (SF Technology)

@col

```pdg
graph dir=TB
pod "Pod requests\ngpu-core + gpu-memory-ratio" shape=round fill=#e3f0ff stroke=#3939D8 color=#2a2a5a
sch "koord-scheduler Device Share\nbinds a slice of one card" shape=round fill=#e3f0ff stroke=#3939D8 color=#2a2a5a
nri "koordlet via NRI\ninjects limits as env" shape=round fill=#e3f0ff stroke=#3939D8 color=#2a2a5a
core "HAMi-Core intercepts CUDA\nenforces memory + compute" shape=round fill=#e8f5e9 stroke=#2e7d32 color=#2a2a5a
pod -> sch stroke=#6a7a99
sch -> nri stroke=#6a7a99
nri -> core stroke=#6a7a99
```

**Zhuoyu:** Koordinator places, HAMi-Core enforces.

<!--
1.5 min. Promise: how vGPU interception enforces memory and compute limits.
HAMi-core is a user-space library. The device plugin mounts it and it is preloaded via ld.so.preload, so every CUDA call from the container goes through it.
Memory: allocations are counted against the limit in MiB. Ask past the limit and the allocation fails with out of memory inside that Pod. The neighbours keep running.
Compute: kernel launches are throttled with a token bucket, granularity 1% of the card.
nvidia-smi in the Pod reports the slice size, so frameworks that size themselves from free memory behave.
SF Technology stresses zero changes to driver, kernel, image or source code.
Right side: Zhuoyu Technology, an autonomous driving company, uses Koordinator as the scheduler and only HAMi-Core for isolation. The Pod asks for gpu-core and gpu-memory-ratio, koord-scheduler's Device Share binds a slice, koordlet injects the limits through NRI, HAMi-Core enforces them. They upstreamed two Koordinator PRs for it (#2577 HAMi-Core availability, #2578 vGPU metrics).
Point: the isolation layer is separable from the scheduler.
-->

---

@layout table-md

## Domestic chips are first-class

@subtitle One request API, a different hook per vendor

| Hardware | How compute is capped | Enforced by | Granularity |
| --- | --- | --- | --- |
| NVIDIA, Ascend | User-space interception (HAMi-core, vNPU-Core) | Token bucket in the runtime | 1% compute, MiB / GB memory |
| AMD CU masking, NVIDIA MPS | Static cap per process | Hardware scheduler | Static |
| Kunlunxin vXPU, Hygon vDCU | Hardware partitions | Silicon | Coarse |
| DeepX, Axelera | No hook point, no quota API | Nothing | No compute slicing |

- The Pod always asks the same way: `gpucores: 40`. HAMi picks the mechanism
- CMB runs Kunlunxin, Ascend, NVIDIA, PPU, Moore Threads and MetaX in **one pool**
- CETC lists 11 supported vendor families. SF Technology runs Ascend, Kunlun and Sunway

<!--
1.5 min. Promise: domestic chips as first-class citizens, and part of how the enforcement differs per vendor.
Compute slicing is the goal; the mechanism depends on the silicon. NVIDIA and Ascend have no hardware compute cap usable for this, so it is done in user space: HAMi-core on NVIDIA, vNPU-Core on Ascend (CMB describes vNPU-Core as token bucket for compute plus user-space memory management, 1 GB memory and 1% compute granularity).
AMD CU masking and NVIDIA MPS are caps honoured by the hardware scheduler, static per process.
Kunlunxin vXPU and Hygon vDCU are hardware-fenced: coarse but silicon-enforced.
And the honest boundary: vendors with no hook and no quota API, like DeepX and Axelera today, cannot be compute-sliced without reverse engineering.
The supported list from the CETC case study: NVIDIA, Ascend, Cambricon, Hygon, Iluvatar CoreX, Moore Threads, MetaX, Enflame, Kunlunxin, AWS Neuron, Vastai. DaoCloud uses the phrase "first-class citizens" for domestic GPUs on D.run.
-->

---

## Mixed hardware, one cluster

@subtitle China Merchants Bank: ~10,000 cards from many vendors

::: card {metric}
8+
separate clusters avoided, one per hardware delivery
:::

::: card {metric}
100%
of the pool usable after paired allocation
:::

::: card {metric}
-30%
cross-machine scheduling, network scored in 3 tiers
:::

::: notes {tag="green"}
Odd-card allocation across dual-chip modules caused driver errors. HAMi's device plugin and scheduler now place pairs inside one module.
:::

<!--
1.25 min. Promise: how the scheduler allocates heterogeneous devices. Source: China Merchants Bank, part 1 (Jul 2026).
Without a common layer, every hardware delivery (Kunlunxin, several Ascend models, NVIDIA, PPUs, Moore Threads, MetaX) would have been its own Kubernetes cluster: 8+ clusters, each with its own device plugin, scheduling policy, monitoring and runbooks.
Topology matters more on domestic hardware. Their supernodes use dual-chip modules. Allocating an odd number of cards across modules caused driver errors and higher latency. They enhanced the HAMi device plugin and scheduler to enforce paired allocation within a module; parts of the pool that were unusable before are now usable: 100% of the hardware pool.
Network topology: three tiers (same node, same LEAF, cross LEAF) in the score, plus deterministic hashing on the controller UID to keep a batch's pods together. Result: 30% less cross-machine scheduling.
Today 99% of their accelerator compute is under unified management.
-->

---

@layout table-md

## Sharing always ships with a scheduler

@subtitle One isolation layer, several scheduling brains

| Organisation | Scheduler and control | What HAMi does there |
| --- | --- | --- |
| Sangfor | Volcano (gang, LWS) | GPU virtualization |
| SF Technology | kube-scheduler + Volcano | Extender, webhook, isolation |
| Zhuoyu | Koordinator (ElasticQuota, Gang, Device Share) | HAMi-Core isolation only |
| China Merchants Bank | Kueue for training, KEDA for inference | Accelerator allocation |
| SNOW Corp. | KEDA on a custom saturation metric | GPU sharing inside one Pod |
| DaoCloud | Own quota + RBAC | vGPU slices, over-subscription |

> "GPU sharing without smart scheduling leads to suboptimal placement; scheduling without GPU virtualization leaves nothing to schedule." Sangfor

<!--
1.25 min. Still promise 3, the scheduling side, and the start of the production patterns.
No case study runs HAMi alone. Every one pairs it with the scheduler they already had:
- Sangfor: Volcano for gang scheduling and LeaderWorkerSet.
- SF Technology: HAMi's scheduler extender and webhook in front of kube-scheduler and Volcano.
- Zhuoyu: Koordinator does placement and quotas, 100+ ElasticQuotas; HAMi-Core only isolates.
- CMB: same control plane, two policies: Kueue for training admission, KEDA plus Prometheus for inference.
- SNOW: KEDA does the scaling; HAMi lets trainer and inference share one GPU inside one pod.
- DaoCloud: their own quota and RBAC at vGPU level.
Pattern: you are not choosing a scheduler when you choose HAMi. You keep yours.
Also integrates with KAI Scheduler (kai-resource-isolator ships the same libvgpu.so); see the 12:30 workshop for hands-on.
-->

---

## Where the 10x comes from

@subtitle Per workload it is real. Per platform it is 2-3x.

```seaborn
import matplotlib.pyplot as plt

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
wl, wl_l = cmap(3.5 / 12), cmap(2.5 / 12)
pf = cmap(1.5 / 12)

fig, ax = plt.subplots(figsize=(11.4, 4.5))
fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
ax.set_facecolor("none")
fig.patch.set_alpha(0)

rows = [
    ("PER WORKLOAD, BASELINE 5-15%", None, None, None, None),
    ("CETC Cloud", "dev pods per device: 2 to 30", 15, 15, "15x"),
    ("Sangfor", "models per GPU: 1 to 8+", 8, 8, "8x"),
    ("NIO", "CI GPU util: 5% to 30-50%", 4, 10, "4-10x"),
    ("PER CARD OR WHOLE PLATFORM", None, None, None, None),
    ("Own H200", "req/s per card: 20.7 to 71.1", 3.4, 3.4, "3.4x"),
    ("Sangfor", "GPU utilization", 3, 3, ">3x"),
    ("Ke Holdings", "platform util: 13% to 37%", 2.8, 2.8, "2.8x"),
    ("SNOW Corp.", "GPUs for train + inference: 2 to 1", 2, 2, "2x"),
    ("CMB", "avg accelerator util: 35% to 60%+", 1.7, 1.7, "1.7x"),
]
n = len(rows)
group = wl
for i, (org, what, lo, hi, txt) in enumerate(rows):
    y = n - 1 - i
    if what is None:
        ax.text(-3.3, y - 0.05, org, ha="left", va="center", fontsize=10.5, color=dim, family="monospace")
        group = wl if org.startswith("PER WORK") else pf
        continue
    ax.barh(y, lo, color=group, height=0.68, zorder=2)
    if hi > lo:
        ax.barh(y, hi - lo, left=lo, color=wl_l, height=0.68, zorder=2)
    ax.text(hi + 0.2, y, txt, ha="left", va="center", fontsize=14, color=fg, fontweight="bold")
    ax.text(17.4, y, what, ha="left", va="center", fontsize=11.5, color=dim)
    ax.text(-0.15, y, org, ha="right", va="center", fontsize=13, color=fg, fontweight="bold")

ax.plot([10, 10], [-0.5, n - 0.5], color=fg, linewidth=1.1, linestyle=(0, (4, 3)), zorder=1)
ax.text(10.15, n - 1.0, "the title: 10x", ha="left", va="center", fontsize=11.5, color=fg, fontweight="bold")
ax.set_xlim(-3.4, 25.6)
ax.set_ylim(-0.55, n - 0.45)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.set_xticks([])
```

10x is real where the baseline is 5-15%: CI, dev envs, embedding, small inference.

<!--
2 min. This is where I explain the title honestly.
Top group, single workloads that started at 5-15%:
- CETC Cloud: dev pods on one appliance went from 2 to 30 concurrent: 15x.
- Sangfor: models per GPU from 1 to 8+.
- NIO: CI GPU utilization from 5% to 30-50%. The CNCF headline box says 10x, the text says about 4x. I show both ends: 4x to 10x depending on which baseline you take.
Bottom group, whole cards or whole platforms:
- Our own H200: 20.7 to 71.1 requests per second per card at the same p95 of 160 ms, HAMi plus KEDA with 10 replicas: 3.4x.
- Sangfor overall GPU utilization: more than 3x.
- Ke Holdings: 13% to 37%, about 2.8x, zero downtime during the move.
- SNOW Corp: half the GPUs for training plus inference pipelines.
- CMB: 35% to 60%+, which is 1.7x on ~10,000 cards. Their own warning: the improvement cannot be attributed to any single component.
Why the platform number is lower: training already uses its cards, and nobody shares big training. If someone promises 10x for your whole cloud, ask what your baseline is.
-->

---

@layout table-md

## What they chose not to share

@subtitle Same 10 organisations, sorted by workload

| Workload | Whole card | HAMi slice | MIG | Time-slicing |
| --- | --- | --- | --- | --- |
| Large training | Ke, CMB, NIO, CETC | | | |
| Large LLM serving | CETC, Ke | | | |
| Small / bursty inference | | Ke, Sangfor, DaoCloud, SF, PREP, NIO | | |
| Dev envs, notebooks | | CETC, Zhuoyu, own | NIO | |
| CI / testing | | NIO, SF | | |
| Embedding, rerank | | CETC | | |
| Simulation | | NIO | | |
| Contention-tolerant | | | | NIO |

::: notes {tag="green"}
Share what is small, bursty, interactive or latency-tolerant. Keep big training and big LLMs whole. MIG where you need hard isolation.
:::

<!--
1.5 min. Promise: best-fit workloads. This is the most useful slide for an operator.
Every one of them kept large training on whole cards: Ke, CMB, NIO, CETC.
Large LLM serving too: CETC keeps text generation on 4 exclusive GPUs, Ke runs large LLMs and training on a separate native-device-plugin cluster of H200 and H100.
What they share: small and bursty inference (Ke typically 1-2 GB VRAM per service), dev environments and notebooks (CETC, Zhuoyu Codespaces, our Viettel notebook), CI (NIO, SF test cluster), embedding and rerank (CETC), simulation (NIO).
NIO is the most interesting: they run all three. MIG for algorithm development where they want strong isolation, HAMi for CI, simulation and some inference, time-slicing for contention-tolerant work. That's not a vendor choice, it's a workload choice.
-->

---

## What sharing costs

@subtitle Overhead as measured, not as promised

::: grid {cols=2}
::: card {tag="green"}
### {icon:gauge cls=accent-primary} Within 5%: CETC Cloud
Embedding on 8 GB and 20% compute: token throughput within 5% of a whole card. p95 latency and model load time unchanged.
:::
::: card {tag="green"}
### {icon:trending-up cls=accent-primary} +46.7%: China Merchants Bank
ResNet50, batch 32: 64.6 to 94.8 images/s per card with finer partitioning. More concurrent work on one card.
:::
::: card {tag="yellow"}
### {icon:ruler cls=accent-contrast} Finer is not better: NIO
1/6 GPU was optimal for simulation. 1/8 added scheduling and virtualization overhead and lowered throughput.
:::
::: card {tag="red"}
### {icon:memory-stick cls=accent-secondary} VRAM is the hard limit: NIO
An OOM cannot wait. A compute shortage becomes scheduling delay. Size memory first.
:::
:::

@tiny Own measurement: capping a training notebook to 70% of the cores turned a 1 h run into 1 h 20 min. A cap is a price you choose.

<!--
1.5 min. Promise: overhead expectations.
CETC Cloud: the embedding model moved from a whole 64 GB card to an 8 GB allocation with 20% of compute. 56 GB of VRAM (87.5%) and 80% of compute freed. Token throughput stayed within 5% of the whole-card run, p95 latency and model load time essentially identical.
CMB: ResNet50 inference, batch 32. One card went from 64.6 to 94.8 images per second, +46.7%, because finer partitioning put more concurrent work on it. Throughput per card, not per job.
NIO: they found the sweet spot for simulation at about 1/6 of a GPU. At 1/8 the scheduling and virtualization overhead ate the gain. NIO also says plainly that HAMi introduces some overhead compared to full GPU allocation.
NIO's resource design rule: VRAM is the primary constraint because an out-of-memory cannot be deferred, while not enough compute just means work waits.
Own measurement if asked: capping a training notebook to 70% of cores turned a 1 hour run into 1 h 20 min. That's a price you choose for a guaranteed slice.
-->

---

## The neocloud case: DaoCloud D.run

@subtitle A GPU cloud that sells slices, not cards

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
average utilization per card
:::

::: card {metric}
20-30%
lower GPU-related opex
:::

::: grid {cols=4}
::: card {tag="cyan"}
### {icon:scissors cls=accent-primary} Slice
vGPU units with defined memory and compute
:::
::: card {tag="green"}
### {icon:shopping-cart cls=accent-primary} Package
SKUs in a marketplace: pay by workload size
:::
::: card {tag="yellow"}
### {icon:layers cls=accent-contrast} Oversubscribe
Controlled, to lift cluster utilization
:::
::: card {tag="red"}
### {icon:users cls=accent-secondary} Govern
Quotas + RBAC per vGPU, NVIDIA + domestic
:::
:::

<!--
1.5 min. Promise: production patterns from cloud providers running 10,000+ GPUs. Source: DaoCloud case study (Dec 2025).
DaoCloud runs two products on HAMi: D.run, a public GPU cloud for developers and small teams, and DCE, a private Kubernetes platform for enterprises. HAMi is active on 10,000+ cards, DaoCloud-operated and customer-owned, single regions up to about 3,000 GPUs, mainland China and Hong Kong.
The neocloud pattern in four moves:
1. Slice cards into vGPU units with defined memory and compute.
2. Package the slices as standardized SKUs in a central marketplace. Users pay by workload size, not for a full card.
3. Controlled over-subscription to lift utilization.
4. For enterprise tenants on DCE: a central pool with quotas and RBAC enforced at vGPU level, per department and queue.
Results they report: more than 80% average utilization per card, 20-30% lower GPU-related opex, faster regional expansion. No before number is given for the 80%, so I don't turn it into a multiplier.
They also avoided proprietary vGPU licensing, and they were one of the earliest upstream contributors (over-subscription, node config, heterogeneous hardware).
-->

---

## Three more production stories

@subtitle Korea, an edge box, a bank

::: grid {cols=3}
::: card {tag="cyan"}
### SNOW Corp. · Korea
**700%** viral traffic spikes handled

**2x fewer GPUs** for training + inference

Trainer and inference share one GPU in one Pod. KEDA scales on queue saturation, ahead of ~60 s warm-up.
:::
::: card {tag="green"}
### CETC Cloud · edge
**2 to 30** concurrent dev pods on one device

**56 GB** of a 64 GB card reclaimed from embedding

Text generation keeps 4 GPUs exclusive. Profiles per workload, not one ratio.
:::
::: card {tag="yellow"}
### China Merchants Bank
**35% to 60%+** average utilization

**-60%+** inference cost per 1M tokens

Kueue for training, KEDA for inference, Fluid for model loading.
:::
:::

::: notes {tag="yellow"}
Honest attribution: SNOW credits most of its savings to KEDA. CMB: the gain "cannot be attributed to any single component".
:::

<!--
1.5 min. Three different shapes of the same pattern.
SNOW Corp (Korea, NAVER subsidiary, 200M+ users, 1,000+ A100s): the Ghibli filter trend gave them 3x traffic in 3 hours, 700% spikes, and they held. Trainer and inference engine share one GPU in the same pod for train-to-inference pipelines: 2x fewer GPUs for those pipelines. KEDA uses a custom consumer saturation metric (unacked messages / active consumers, threshold about 0.7) to scale ahead of the ~60 s model warm-up. Honest attribution: most of their cost savings (USD 17.4M estimated vs on-demand cloud) come from KEDA autoscaling; HAMi is credited for sharing and for avoiding a re-architecture during the Kubernetes migration.
CETC Cloud: a portable knowledge-base appliance with 8 heterogeneous GPUs. Dev capacity from 2 to 30 concurrent dev pods. Embedding from a whole 64 GB card to 8 GB, 56 GB reclaimed. They insist on profiles per workload type, not a preset partition ratio.
China Merchants Bank part 2 (Sep 2026): average accelerator compute utilization 35% to 60%+, inference cost per 1M tokens down 60%+. Stack: Kueue, KEDA plus Prometheus, HAMi, Fluid, vLLM and SGLang on Ray. Again: not attributable to any single component.
-->

---

## What operating it taught them

@subtitle From the case studies, not from the docs

::: grid {cols=3}
::: card
### {icon:refresh-cw cls=accent-primary} Upgrades change performance
NIO validates every version, rolls out in phases, and upgrades inference device plugins blue-green.
:::
::: card
### {icon:wrench cls=accent-contrast} Toolchains can clash
NIO: some compiler and library features that do pointer analysis conflict with interception.
:::
::: card
### {icon:chart-bar cls=accent-primary} Allocation is not utilization
Zhuoyu: allocation over 95%, utilization over 55%. Track both, separately.
:::
::: card
### {icon:shield-check cls=accent-primary} Isolation before density
PREP EDU: sharing without isolation crashed apps. With limits, memory-conflict crashes stopped.
:::
::: card
### {icon:activity cls=accent-contrast} Scale on saturation
SNOW: KEDA scales on queue saturation, ahead of the ~60 s model warm-up.
:::
::: card
### {icon:hard-drive cls=accent-primary} Load speed limits elasticity
CMB: inference only scales as fast as models load. Fluid caches the models.
:::
:::

<!--
1.5 min. The things you only learn in production.
- NIO: validate performance on every HAMi version upgrade, phased rollout, mixed versions allowed in the cluster; blue-green style device plugin upgrades for inference nodes.
- NIO: some compiler and library features doing pointer or address analysis conflict with GPU interception. Test your toolchain before you share its nodes.
- Zhuoyu gave the cleanest definitions: allocation = scheduled cards / schedulable cards; utilization = mean SM utilization from node telemetry. Allocation above 95% and utilization above 55% (about 60% on shared inference) are both true at once. Scheduler and DRA metrics tell you what's reserved; usage needs a runtime collector.
- PREP EDU in Vietnam tried other sharing approaches without isolation first: resource conflicts, memory allocation issues, app crashes. With HAMi limits, memory-conflict crashes were eliminated; one year in production, 90% of their GPU infra.
- SNOW: scale on a saturation metric, not GPU utilization, because the model takes about 60 s to warm up.
- CMB: inference elasticity depends on model load speed; that's why Fluid is in their stack.
-->

---

## Honest limits

@subtitle What the case studies and our own tests say sharing does not do

- {icon:shield-alert cls=accent-secondary} **Soft isolation is not a security boundary.** `CUDA_DISABLE_CONTROL`, static CUDA or direct `/dev/nvidia*` ioctls skip it. Trusted tenants only
- {icon:lock cls=accent-primary} **Hard isolation means MIG.** NIO uses MIG for algorithm development
- {icon:ruler cls=accent-contrast} **Finer is not better.** 1/8 of a GPU lost to 1/6 (NIO)
- {icon:cpu cls=accent-primary} **Big training stays on whole cards.** Ke, CMB, CETC, NIO
- {icon:chart-bar cls=accent-contrast} **Allocation is not utilization.** Per-tenant telemetry is uneven across vendors
- {icon:file-text cls=accent-primary} **DRA is not in production** in any of the 11 case studies yet
- {icon:layers cls=accent-contrast} **Results are stack results.** KEDA, Kueue and Fluid share the credit (SNOW, CMB)

<!--
1.5 min. Promise: no vendor pitch. Say these plainly.
- HAMi-core is a resource and fairness control for workloads you trust. Setting CUDA_DISABLE_CONTROL=true skips the libvgpu.so preload; statically linked CUDA and direct ioctls on /dev/nvidia* bypass a preload library. Do not sell a soft slice to untrusted tenants as a security boundary.
- If you need hard isolation, use MIG where the hardware has it. NIO does exactly that for algorithm development.
- Finer is not better: NIO measured 1/8 losing to 1/6.
- Nobody in the case studies shares large training: Ke, CMB, CETC, NIO all keep it whole.
- Allocation is not utilization. And per-tenant telemetry differs per vendor; for example AMD has no first-party per-tenant path.
- DRA: none of the studies runs it in production yet.
- Attribution: SNOW credits most cost savings to KEDA; CMB says the gain cannot be attributed to any single component. HAMi is one layer of a stack.
-->

---

@layout timeline-horizontal

## The blueprint they converged on

@subtitle Every step is something one of the ten already does

::: grid {cols=5}
::: card {label="1"}
### Measure
Find the 5-15% jobs
:::
::: card {label="2"}
### Enforce
Memory + compute
:::
::: card {label="3"}
### Schedule
Your scheduler
:::
::: card {focus, label="4"}
### Sell
SKUs + quotas
:::
::: card {label="5"}
### Operate
Upgrades, usage
:::
:::

::: notes {tag="green"}
Step zero: decide what stays whole. Big training and big LLMs keep whole cards.
:::

<!--
1.5 min. Promise: a concrete blueprint, GPU box to GPU cloud with sellable fractional capacity. Every step comes from someone in this talk.
0. Profile first: CETC's lesson, start from workload profiles, not a preset partition ratio. Training and big LLMs keep whole cards (Ke, CMB, CETC, NIO).
1. Measure: Zhuoyu's split of allocation versus utilization. Look for the 5-15% workloads: CI, dev envs, notebooks, embedding, small inference.
2. Enforce: HAMi-core on NVIDIA, vNPU-Core on Ascend, hardware partitions where they exist. MIG where you need hard isolation.
3. Schedule: Sangfor on Volcano, CMB on Kueue and KEDA, Zhuoyu on Koordinator. HAMi does not replace your scheduler.
4. Sell, the neocloud step: DaoCloud D.run. Standard slice SKUs in a marketplace, quotas and RBAC at vGPU level, controlled over-subscription. Over 80% per card.
5. Operate: NIO's phased upgrades, per-tenant accounting (CMB and NIO roadmaps), SNOW's saturation-based scaling.
-->

---

@variant dark
@side-image assets/qr-hami-repo.png
@kicker 11 case studies · 10 organisations · hundreds of enterprises in production

# Thank you

@subtitle Every number: cncf.io/case-studies, project HAMi

@speaker name="Reza Jelveh" role="Head of Global Market, Dynamia" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

<!--
30 s. The QR code goes to the HAMi repo. Every number in this talk is from the CNCF case study list on the subtitle line: filter by project HAMi.
If time: invite people to the HAMi workshop material (github.com/Project-HAMi/hami-workshop) and to find me at the Dynamia booth for questions.
Facts if asked: CNCF Incubating, 4,900+ GitHub stars, 500+ contributors from 20+ countries.
-->

---

@hidden

## Backup: SNOW Corp. in detail

@subtitle Consumer GenAI in Korea, 1,000+ A100s

::: card {metric}
700%
viral traffic spikes handled
:::

::: card {metric}
-91%
MTTR: 2 h to 10 min
:::

::: card {metric}
-85%
surge errors
:::

::: card {metric}
-55%
average GPU usage time
:::

::: notes {tag="green"}
1,200+ AI workflows, 400+ models, on-prem multi-region plus CSP bursting. HAMi let trainer and inference share a GPU in one Pod and unblocked the Kubernetes migration without re-architecture.
:::

<!--
Backup. SNOW Corp case study (May 2026). USD 17.4M estimated savings vs on-demand cloud at about USD 45/h per A100; most of the cost savings are attributed to KEDA autoscaling, HAMi to GPU sharing and avoiding re-architecture. KEDA metric: unacked_messages / active_consumers, threshold about 0.7.
-->

---

@hidden

## Backup: small teams, consumer cards

@subtitle SF Technology and PREP EDU

::: grid {cols=2}
::: card {tag="cyan"}
### SF Technology · logistics
- Production inference: **65 services on 28 GPUs**
- Test cluster: **19 services on 6 GPUs**
- Priority-based compute preemption
- **0 changes** to driver, kernel, image or source
:::
::: card {tag="green"}
### PREP EDU · Vietnam
- RTX 4070 + 4090, RKE2 + GPU Operator
- Baseline **10-20%** with static allocation
- HAMi on **90%** of GPU infra, 1 year in production
- Memory-conflict crashes eliminated
:::
:::

> "Deployment is practically plug-and-play: a Helm chart and a couple of labels." PREP EDU

<!--
Backup. SF Technology (Sep 2025): in-house EffectiveGPU built on HAMi; saved 37 GPUs in production and 13 in test; "up to 57% GPU savings". Supports Ascend, Baidu Kunlun, Sunway.
PREP EDU (Aug 2025): per-service limits by NLP token length, GPU type pinning via annotations, UUID pinning. Vu Hoang Tran quote.
-->

---

@hidden

## Backup: our own H200 measurement

@subtitle Fix the SLA, scale replicas, fill the empty GPU

```seaborn
import matplotlib.pyplot as plt

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
red = cmap(5.5 / 12)
green = cmap(3.5 / 12)
grey = "#e0e0df"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 3.0),
                               gridspec_kw={"width_ratios": [1.3, 1], "wspace": 0.32})
fig.patch.set_alpha(0)
for ax in (ax1, ax2):
    ax.set_facecolor("none")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    ax.set_xticks([])

ax1.text(-42, 2.9, "REQ/S PER CARD  @  P95 160 MS", fontsize=10.5, color=dim, family="monospace")
for y, v, n, c in [(2, 20.7, "Native", grey), (0, 71.1, "HAMi + KEDA", red)]:
    ax1.barh(y, v, color=c, height=0.62)
    ax1.text(-3, y, n, ha="right", va="center", fontsize=12, color=fg, fontweight="bold")
    ax1.text(v + 3, y, str(v), ha="left", va="center", fontsize=12.5, color=fg, fontweight="bold")
ax1.plot([20.7, 20.7], [-0.5, 2.5], color=dim, linewidth=1.2, linestyle=(0, (4, 3)))
ax1.text(20.7, 2.55, "one whole GPU", ha="center", va="bottom", fontsize=10.5, color=dim)
ax1.text(-3, -0.55, "3.4x per card", ha="right", va="center", fontsize=11.5, color=red, fontweight="bold")
ax1.set_xlim(-42, 100)
ax1.set_ylim(-0.9, 3.1)

ax2.text(-0.15, 128, "SM UTILIZATION VS REPLICAS", fontsize=10.5, color=dim, family="monospace")
xs, vals = [0, 1, 2, 3], [18, 31, 54, 100]
ax2.plot(xs, vals, color=red, linewidth=2.2, zorder=2)
for x, v, c, r in zip(xs, vals, [grey, red, red, green], [7, 5.5, 5.5, 9]):
    ax2.plot(x, v, "o", markersize=r, color=c, markeredgecolor="white", markeredgewidth=1.3, zorder=3)
    ax2.text(x, v + 8, f"{v}%", ha="center", fontsize=11.5, color=fg, fontweight="bold")
for x, lab in zip(xs, ["1", "2", "5", "10 replica"]):
    ax2.text(x, -13, lab, ha="center", fontsize=12, color=dim)
ax2.set_xlim(-0.35, 3.4)
ax2.set_ylim(-22, 140)
```

- HAMi does not make one pod faster: it fills the GPU that was sitting empty
- Bigger batches did not help: 32 to 512, GPU still 7-10%

<!--
Backup, from the Viettel Cloud work (drawings.md). Native 20.7 req/s per card at p95 160 ms; HAMi plus KEDA with 10 replicas 71.1 req/s at the same latency: 3.4x per card. SM 18% to 31% to 54% to 100% at 1, 2, 5, 10 replicas. Same 71 req/s natively would need about 3.4 cards: about 71% fewer cards, about 51% less power, about $7k/month at an example $4 per GPU-hour.
-->
