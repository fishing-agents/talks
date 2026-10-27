---
theme: kubecon_japan
title: "10x Your Neocloud's GPU Utilization with HAMi"
logo: assets/brand/dynamia-logo.svg
logo_dark: assets/brand/dynamia-logo-white.png
footer: "ContainerDays 2026 Singapore"
transition: fade
paginate: true
size: 16:9
seaborn_theme: kubecon_japan
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
  .layout-title .side-image img { width: 170px; max-width: 170px; max-height: none; }
  .layout-timeline-horizontal .card { padding: 0.6em 0.8em; font-size: 0.85em; }
  .layout-timeline-horizontal .card.focus { padding: 0.6em 0.8em; border: 0.15em solid var(--color-accent-primary); }
  .layout-timeline-horizontal .timeline-label { font-size: 0.75em; }
  [class*="layout-metrics"] .slide-body > :not(:first-child) { margin-top: 0.9em; }

---

<!--
25 min talk, ContainerDays 2026 Singapore, Tuesday Oct 27. Concept C: follow one H200 through one day; each part of the day introduces one mechanism, then the CNCF case studies generalise it.
Timing: hook + why (3 min), morning to office hours (8 min), afternoon to night (6 min), generalise + limits + blueprint (7 min), close (1 min).
Open: 'Raise your hand if you run GPUs on Kubernetes. Keep it up if you know your average utilization.' Then: this talk follows one card through one day.
-->
@variant dark
@side-image assets/qr-hami-repo.png
@kicker ContainerDays 2026 Singapore · CNCF Incubating project

# 10x Your Neocloud's GPU Utilization with HAMi

@subtitle One H200, one day

@speaker name="Reza Jelveh" role="Head of Global Market, Dynamia" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

---

## One job, 1 GB of a 141 GB H200

@subtitle Allocated is not used

<!--
Own measurement (Viettel Cloud work, drawings.md). Two real jobs, each held a WHOLE H200 (141 GB).
1) Time-series forecast, small model: 1 GB of 141 GB, SM 16-18%.
2) YOLO11 defect-detection training, ~17k images: 39 GB. Batch is sized for accuracy, not to fill the card, so the ~100 GB left over is genuinely free.
Don't rush '1 GB out of 141'. Pause.
Many cards have no MIG at all (L40, L40S, A6000), so hardware partitioning is not even an option there.
And this is not just us: seven organisations in the CNCF case studies measured whole-card utilization between 5 and 20%. We come back to that at the end.
-->

```seaborn
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = [*plt.rcParams["font.sans-serif"], "DejaVu Sans"]

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
red = plt.rcParams["patch.edgecolor"]
cmap = plt.get_cmap("Paired")
yellow = cmap(6.5 / 12)
grey = "#dfe2ec"
plt.rcParams["patch.force_edgecolor"] = False

fig, ax = plt.subplots(figsize=(12.5, 3.4))
ax.set_facecolor("none")
fig.patch.set_alpha(0)

ax.text(-40, 1.75, "GPU MEMORY: ALLOCATED VS USED", fontsize=11.5, color=dim, family="monospace")
ax.barh(1, 141, color=grey, height=0.5)
ax.barh(1, 1, color=red, height=0.5)
ax.barh(0, 141, color=grey, height=0.5)
ax.barh(0, 39, color=yellow, height=0.5)

ax.text(-4, 1, "Time-series\n(inference)", ha="right", va="center", fontsize=14, color=fg, fontweight="bold", linespacing=1.4)
ax.text(-4, 0, "Defect detection\n(training)", ha="right", va="center", fontsize=14, color=fg, fontweight="bold", linespacing=1.4)
ax.text(6, 1, "1 GB used, SM 16-18%", ha="left", va="center", fontsize=14, color=fg, fontweight="bold")
ax.text(44, 0, "39 GB used", ha="left", va="center", fontsize=14, color=fg)
ax.text(141, 1.42, "one whole H200 = 141 GB", ha="right", va="bottom", fontsize=12, color=dim)

ax.annotate("", xy=(139, -0.55), xytext=(41, -0.55),
            arrowprops=dict(arrowstyle="<->", color=dim, linewidth=1.4))
ax.text(90, -0.74, "~100 GB free: inference, notebooks, CV, embedding",
        ha="center", va="top", fontsize=13, color=fg, fontweight="bold")

ax.set_xlim(-40, 148)
ax.set_ylim(-1.15, 1.95)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.grid(False)
```

- The time-series job leaves **140 GB and over 80% of the SMs** doing nothing
- Many cards have **no MIG** at all: L40, L40S, A6000

> Kubernetes gives one choice: `nvidia.com/gpu: 1`. The whole card, or nothing.

---

@layout compare

## Why the default can't fix it

@subtitle Requesting a fraction is not enforcing one

<!--
Promise 1: why DRA alone does not fix utilization.
Device plugin: nvidia.com/gpu: 1 is an integer. The whole card or nothing. That is how the 1 GB job got 141 GB.
DRA: a real improvement. ResourceClaims can ask for part of a device, with typed capacities. But DRA is a request and allocation API. It does not stop a pod at 8 GB, it does not cap compute, and the default scheduler has no notion of packing shares on one card.
You need two more things: virtualization on the node that enforces the slice, and a scheduler that knows how to share.
Sangfor said it best in their CNCF case study (quote on slide).
-->

::: card {tag=red}
### {icon:box cls=accent-secondary} Device plugin
`nvidia.com/gpu: 1` is an integer: the whole card or nothing. The 1 GB job gets 141 GB.
:::

::: arrow
{icon:arrow-right size=32}
:::

::: card {tag=yellow}
### {icon:file-text cls=accent-contrast} DRA alone
A claim can ask for a fraction. Nothing on the node **enforces** it, and nothing **packs** shares onto one card.
:::

::: notes {tag=green}
"GPU sharing without smart scheduling leads to suboptimal placement; scheduling without GPU virtualization leaves nothing to schedule." Sangfor
:::

---

@layout timeline-horizontal

## One H200, one day

@subtitle Each part of the day adds one mechanism

<!--
The map for the next 15 minutes. Same card, same day; every stop adds one layer.
Morning: enforce a split. Late morning: scale replicas into the freed space. Office hours: the scheduler and autoscaler hand capacity around. Afternoon: the second card in the rack is not NVIDIA. Evening: where DRA fits. Night: turn the box into something you can sell.
-->

::: grid {cols=6}
::: card {focus, label="Morning"}
### Enforce
Split the card
:::
::: card {label="Late AM"}
### Scale
1 to 10 replicas
:::
::: card {label="Office hrs"}
### Schedule
Place, hand off
:::
::: card {label="Afternoon"}
### Mix
Not only NVIDIA
:::
::: card {label="Evening"}
### Request
Where DRA fits
:::
::: card {label="Night"}
### Sell
Box to cloud
:::
:::

---

@layout two-col

## Morning: split the card

@subtitle How vGPU interception enforces memory and compute

<!--
Promise 2: how interception enforces the limits.
1. The pod asks for memory in MiB and compute in percent of SMs, next to nvidia.com/gpu: 1.
2. HAMi's scheduler extender picks a physical card UUID with enough headroom and writes it on the pod.
3. The device plugin mounts the device and injects HAMi-core, libvgpu.so, through ld.so.preload. No app changes, no kernel modules, no driver changes.
4. HAMi-core intercepts the CUDA calls: every allocation is checked against the memory slice, so an OOM stays inside the slice. Kernel launches go through a token bucket that holds the pod at its compute percent, 1% granularity.
5. nvidia-smi inside the pod shows the slice, not the card: 15000 MiB, not 141 GB.
Same pattern per vendor where there is a hook point (Ascend ACL, Cambricon CNRT). The YAML is the same shape on Ascend: Ascend910C-memory, Ascend910C-core.
-->

1. Pod asks for **MiB** of memory and **%** of compute
2. Scheduler picks a card **UUID** with headroom
3. Device plugin injects **`libvgpu.so`** via `ld.so.preload`
4. HAMi-core intercepts CUDA: allocations capped at the slice, launches paced by a **% token bucket**
5. `nvidia-smi` in the pod shows **the slice, not the card**

@col

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
    nvidia.com/gpumem: 15000   # MiB
    nvidia.com/gpucores: 30    # % of SMs
```

```dot
digraph G {
  rankdir=LR
  bgcolor=transparent
  node [shape=box style="rounded,filled" fontname="Roboto" fontsize=15 margin="0.2,0.14"]
  edge [fontname="Roboto" fontsize=12]
  app [label="Your app" class="cyan"]
  lib [label="HAMi-core\nlibvgpu.so" class="yellow"]
  gpu [label="H200 slice" class="green"]
  app -> lib [label="CUDA calls"]
  lib -> gpu [label="within limits"]
}
```

---

## Morning: two fences on one card

@subtitle Memory is a hard wall, compute is a pace

<!--
Left: the measured split of our H200. The notebook training job (YOLO11) gets a 39 GB slice, the time-series job a 1 GB slice, about 100 GB is free for the next tenants. Memory is the hard constraint: an OOM cannot wait (NIO says the same in their case study), so memory is fenced, never over-committed by default.
Right: compute is different. Illustration, not a measurement: a pod at 25% of the SMs is paced on every kernel launch and cannot burst above its share even if the rest is idle. A compute shortage can be absorbed as delay, a memory shortage cannot.
-->

::: grid {cols=2}
::: card
### {icon:memory-stick cls=accent-primary} Memory: MiB slices
```seaborn
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = [*plt.rcParams["font.sans-serif"], "DejaVu Sans"]

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
accent = plt.rcParams["axes.edgecolor"]
red = plt.rcParams["patch.edgecolor"]
grey = "#dfe2ec"
plt.rcParams["patch.force_edgecolor"] = False

fig, ax = plt.subplots(figsize=(6.2, 2.9))
ax.set_facecolor("none")
fig.patch.set_alpha(0)
ax.text(0, 1.62, "MEMORY: ONE H200, 141 GB", fontsize=11, color=dim, family="monospace")
segs = [(39, accent, "39 GB"), (1, red, ""), (101, grey, "~100 GB free")]
left = 0
for w, c, t in segs:
    ax.barh(1, w, left=left, color=c, height=0.7, edgecolor="white", linewidth=1.5)
    if t:
        ax.text(left + w / 2, 1, t, ha="center", va="center", fontsize=12,
                color="white" if c == accent else fg, fontweight="bold")
    left += w
ax.text(19.5, 0.42, "notebook\n(training)", ha="center", va="top", fontsize=11, color=fg, linespacing=1.3)
ax.text(40, 0.42, "time-series\n1 GB", ha="left", va="top", fontsize=11, color=red, fontweight="bold", linespacing=1.3)
ax.text(141, 0.42, "next tenants", ha="right", va="top", fontsize=11, color=dim)
ax.set_xlim(-1, 142)
ax.set_ylim(-0.35, 1.85)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.grid(False)
```
:::
::: card
### {icon:gauge cls=accent-primary} Compute: paced on every launch
```seaborn
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = [*plt.rcParams["font.sans-serif"], "DejaVu Sans"]

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
cmap = plt.get_cmap("Paired")
green = cmap(3.5 / 12)
grey = "#dfe2ec"
plt.rcParams["patch.force_edgecolor"] = False

fig, ax = plt.subplots(figsize=(6.2, 2.9))
ax.set_facecolor("none")
fig.patch.set_alpha(0)
units, assigned = 8, 2
ax.bar(range(units), [1] * units, width=0.85,
       color=[green] * assigned + [grey] * (units - assigned), edgecolor="white", linewidth=1.5)
ax.annotate("", xy=(-0.4, -0.3), xytext=(1.4, -0.3),
            arrowprops=dict(arrowstyle="<->", color=fg, linewidth=1.4))
ax.text(0.5, -0.45, "pod A: 25%", ha="center", va="top", fontsize=12, color=fg, fontweight="bold")
ax.text(4.5, -0.45, "75% free for other pods", ha="center", va="top", fontsize=12, color=fg, fontweight="bold")
ax.text(-0.5, 1.25, "COMPUTE: % OF SMs (ILLUSTRATIVE)", fontsize=11, color=dim, family="monospace")
ax.set_xlim(-0.6, 7.6)
ax.set_ylim(-0.9, 1.5)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.grid(False)
```
:::
:::

- **Memory is the hard wall:** an OOM cannot wait, so it stays inside the slice
- **Compute is a pace:** a shortage becomes delay, no burst above the share

---

## Late morning: 1 to 10 replicas

@subtitle Fix the SLA, add replicas, fill the empty card

<!--
Own measurement on the H200, time-series inference service, p95 held at 160 ms.
Native: one pod per card, 20.7 req/s, SM 18%. With HAMi slices plus KEDA scaling to 10 replicas on the same card: 71.1 req/s at the same p95. SM goes 18 -> 31 -> 54 -> 100% at 1, 2, 5, 10 replicas.
Land it: HAMi does not make one pod faster. It fills the card that was sitting empty.
The team challenged the baseline: bigger batches (32 to 512) left the GPU at 7-10%; one instance simply cannot fill an H200.
Cost framing (example only): the same 71 req/s natively needs about 3.4 cards, so roughly 71% fewer cards, about 51% less power, ~$7k/month at an example $4/GPU-hour.
DEMO NOTE: this segment works as a recorded demo (replicas scaling, nvidia-smi SM climbing). No recording in the deck yet; if one is made, add it here.
-->

```seaborn
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = [*plt.rcParams["font.sans-serif"], "DejaVu Sans"]

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
accent = plt.rcParams["axes.edgecolor"]
red = plt.rcParams["patch.edgecolor"]
cmap = plt.get_cmap("Paired")
green = cmap(3.5 / 12)
grey = "#c9cddb"
plt.rcParams["patch.force_edgecolor"] = False

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 3.3),
                               gridspec_kw={"width_ratios": [1.3, 1], "wspace": 0.32})
fig.patch.set_alpha(0)
for ax in (ax1, ax2):
    ax.set_facecolor("none")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
    ax.grid(False)

ax1.text(-42, 3.35, "REQ/S PER CARD @ P95 160 MS", fontsize=10.5, color=dim, family="monospace")
for y, v, n, c in [(2, 20.7, "Native", grey), (0, 71.1, "HAMi + KEDA", red)]:
    ax1.barh(y, v, color=c, height=0.62)
    ax1.text(-3, y, n, ha="right", va="center", fontsize=12, color=fg, fontweight="bold")
    ax1.text(v + 3, y, str(v), ha="left", va="center", fontsize=12.5, color=fg, fontweight="bold")
ax1.plot([20.7, 20.7], [-0.5, 2.5], color=dim, linewidth=1.2, linestyle=(0, (4, 3)))
ax1.text(20.7, 2.55, "one whole GPU", ha="center", va="bottom", fontsize=10.5, color=dim)
ax1.text(-3, -0.6, "3.4x per card", ha="right", va="center", fontsize=11.5, color=red, fontweight="bold")
ax1.set_xlim(-42, 100)
ax1.set_ylim(-0.9, 3.6)

ax2.text(-0.15, 128, "SM UTILIZATION VS REPLICAS", fontsize=10.5, color=dim, family="monospace")
xs, vals = [0, 1, 2, 3], [18, 31, 54, 100]
ax2.plot(xs, vals, color=red, linewidth=2.2, zorder=2)
for x, v, c, r in zip(xs, vals, [grey, red, red, green], [7, 5.5, 5.5, 9]):
    ax2.plot(x, v, "o", markersize=r, color=c, markeredgecolor="white", markeredgewidth=1.3, zorder=3)
    ax2.text(x, v + 8, f"{v}%", ha="center", fontsize=11.5, color=fg, fontweight="bold")
for x, lab in zip(xs, ["1", "2", "5", "10 replicas"]):
    ax2.text(x, -13, lab, ha="center", fontsize=12, color=dim)
ax2.set_xlim(-0.35, 3.4)
ax2.set_ylim(-22, 140)
```

- One pod uses **18%** of the SMs. Ten replicas on the same card: **100%, same p95**
- HAMi does not make one pod faster: **it fills the card that sat empty**
- Bigger batches did not help: **32 to 512**, GPU still at 7-10%

---

## Office hours: the scheduler decides

@subtitle One slice fixed all day, the rest follows the load

<!--
Promise 3 starts here (scheduler), continued on the afternoon slide.
Own design for the Viettel AI notebook card: the notebook keeps its ~30% memory slice all day, never moves.
Morning: everyone opens forecasts, time-series runs x6. Office hours: time-series drops to x1, the space goes to LLM inference x5 (models under 20B). Night: inference is quiet, the space goes to more notebooks and overnight training.
Two decisions make this work:
- Placement: HAMi's scheduler scores on two axes, which node and which card. binpack fills the fuller card (consolidate, keep whole cards free for training), spread uses the emptier one (fewer noisy neighbours). Topology (NVLink, PCIe, NUMA) is part of the card choice.
- Hand-off: KEDA scales the replicas, so freed capacity moves to whoever peaks next. They peak at different hours, so they take turns on one card.
Bring your own brain: Volcano, Kueue, Koordinator, KAI Scheduler all sit on the same isolation layer (backup slide).
-->

```seaborn
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = [*plt.rcParams["font.sans-serif"], "DejaVu Sans"]

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
accent = plt.rcParams["axes.edgecolor"]
cmap = plt.get_cmap("Paired")
red = cmap(5.5 / 12)
orange = cmap(6.5 / 12)
bluel = cmap(0.5 / 12)
grey = "#dfe2ec"
plt.rcParams["patch.force_edgecolor"] = False

fig, ax = plt.subplots(figsize=(12.5, 3.6))
fig.patch.set_alpha(0)
ax.set_facecolor("none")
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.grid(False)

ax.text(-26, 2.86, "ONE H200 ACROSS ONE DAY", fontsize=11.5, color=dim, family="monospace")
rows = [
    (2, "Morning", [(30, accent, "Notebook ~30%"), (50, red, "Time-series x6"), (20, grey, "")]),
    (1, "Office hours", [(30, accent, "Notebook ~30%"), (8, red, "x1"), (42, orange, "LLM inference x5"), (20, grey, "")]),
    (0, "Night", [(30, accent, "Notebook ~30%"), (42, bluel, "more training"), (8, red, "x1"), (20, grey, "")]),
]
for y, label, segs in rows:
    left = 0
    for w, c, txt in segs:
        ax.barh(y, w, left=left, color=c, height=0.62, edgecolor="white", linewidth=1.8)
        if txt:
            ax.text(left + w / 2, y, txt, ha="center", va="center", fontsize=11,
                    color=fg if c in (orange, bluel) else "white", fontweight="bold")
        left += w
    ax.text(-3, y, label, ha="right", va="center", fontsize=13, color=fg, fontweight="bold")
ax.text(100, 2.7, "card full", ha="right", va="bottom", fontsize=10, color=dim)
ax.plot([100, 100], [-0.4, 2.58], color=dim, linewidth=1.0, linestyle=(0, (2, 3)), zorder=1)
ax.set_xlim(-26, 106)
ax.set_ylim(-0.6, 3.2)
```

- {icon:layout-grid cls=accent-primary} **Placement:** binpack or spread, per node and per card, topology-aware
- {icon:refresh-cw cls=accent-secondary} **Hand-off:** KEDA scales replicas, so freed slices go to whoever peaks next
- {icon:brain cls=accent-primary} **Your brain, same fences:** Volcano, Kueue, Koordinator, KAI Scheduler

---

## The price of a guaranteed slice

@subtitle Overhead you choose on purpose

<!--
Promise 6 (overhead), own measurements on the H200 notebook.
Left: capping the notebook to 70% of the cores with `force` turned a 1h00 training run into 1h20. +20 minutes, paid on purpose: the freed share is reserved, not 'maybe free'. Small model here; a big model pays more.
Right: does sharing make training jittery? Epoch-time CV (std dev / mean, lower is steadier): 1% alone, 19% shared with bursty inference and no cap, 9% shared with the cap. The cap roughly halves the jitter on the same shared card.
Honest caveat: the cap isolates stability, not throughput. For hard throughput isolation use MIG.
-->

```seaborn
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = [*plt.rcParams["font.sans-serif"], "DejaVu Sans"]

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
red = plt.rcParams["patch.edgecolor"]
cmap = plt.get_cmap("Paired")
green = cmap(3.5 / 12)
grey = "#c9cddb"
plt.rcParams["patch.force_edgecolor"] = False

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 3.3), gridspec_kw={"width_ratios": [1, 1.4], "wspace": 0.25})
fig.patch.set_alpha(0)
for ax in (ax1, ax2):
    ax.set_facecolor("none")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    ax.grid(False)

ax1.text(-0.55, 104, "TRAINING RUN, CAPPED", fontsize=10.5, color=dim, family="monospace")
ax1.plot([-0.5, 1.55], [60, 60], color=dim, linewidth=1.2, linestyle=(0, (4, 3)), zorder=3)
ax1.bar(0, 60, width=0.5, color=grey, zorder=2)
ax1.bar(1, 80, width=0.5, color=red, zorder=2)
ax1.text(0, 63, "1h00", ha="center", va="bottom", fontsize=14, color=fg, fontweight="bold")
ax1.text(1, 83, "1h20", ha="center", va="bottom", fontsize=14, color=fg, fontweight="bold")
ax1.text(1.34, 70, "+20 min", ha="left", va="center", fontsize=12.5, color=red, fontweight="bold")
ax1.text(0, -6, "full card", ha="center", va="top", fontsize=11.5, color=dim)
ax1.text(1, -6, "70% cores", ha="center", va="top", fontsize=11.5, color=dim)
ax1.set_xlim(-0.8, 2.3)
ax1.set_ylim(-20, 112)

ax2.text(-0.55, 23.2, "EPOCH-TIME JITTER (CV, LOWER = STEADIER)", fontsize=10.5, color=dim, family="monospace")
for x, v, c, lab in [(0, 1, green, "alone"), (1, 19, red, "shared,\nno cap"), (2, 9, green, "shared,\ncapped")]:
    ax2.bar(x, v, width=0.56, color=c, zorder=2)
    ax2.text(x, v + 0.8, f"{v}%", ha="center", va="bottom", fontsize=14, color=fg, fontweight="bold")
    ax2.text(x, -1.2, lab, ha="center", va="top", fontsize=11.5, color=dim)
ax2.annotate("", xy=(1.82, 10.2), xytext=(1.18, 17.6),
             arrowprops=dict(arrowstyle="->", color=fg, linewidth=1.7, connectionstyle="arc3,rad=-0.32"))
ax2.text(2.3, 17.0, "cap halves it", ha="center", va="center", fontsize=11, color=fg, fontweight="bold")
ax2.set_xlim(-0.65, 2.7)
ax2.set_ylim(-4, 24.5)
```

- {icon:lock cls=accent-primary} **+20 min** buys a reserved share, not a "maybe free" one
- {icon:triangle-alert cls=accent-secondary} The cap protects **stability, not throughput**: hard throughput isolation is MIG

---

@layout two-col

## Afternoon: the second card isn't NVIDIA

@subtitle One pool, one API, per-vendor enforcement

<!--
Promises 3 and 7: heterogeneous scheduling, domestic chips as first-class citizens.
The API stays one shape (memory + cores per vendor resource name); the enforcement underneath depends on what the vendor gives you:
- NVIDIA and Ascend have no hardware compute cap, so HAMi intercepts in user space (token bucket, 1%).
- AMD CU masking and NVIDIA MPS are caps the hardware scheduler honours, static per process.
- Kunlunxin vXPU and Hygon vDCU are hardware-fenced: coarse, but silicon-enforced.
- Vendors with no hook point and no quota API (DeepX, Axelera today): no compute slicing without reverse engineering. Honest boundary.
China Merchants Bank (CNCF case study, ~10,000 cards): Kunlunxin, several Ascend models, NVIDIA, PPUs, Moore Threads, MetaX. Without HAMi every hardware delivery would have been its own cluster: 8+ clusters, each with its own device plugin, scheduler policy, monitoring, runbooks. With topology-aware paired allocation on their dual-chip supernodes (odd-card allocation caused driver errors), 100% of the pool became usable; network-tier scoring cut cross-machine scheduling by 30%.
DaoCloud uses the exact phrase 'first-class citizens' for domestic GPUs on D.run.
CETC's list of supported devices: NVIDIA, Ascend, Cambricon, Hygon, Iluvatar CoreX, Moore Threads, MetaX, Enflame, Kunlunxin, AWS Neuron, Vastai.
-->

| Hardware | Compute cap |
| --- | --- |
| NVIDIA, Ascend | User-space interception, 1% token bucket |
| AMD CU masking, NVIDIA MPS | Hardware-honoured, static |
| Kunlunxin vXPU, Hygon vDCU | Hardware-fenced, coarse |
| DeepX, Axelera | No hook point today |

```yaml
nvidia.com/gpucores: 30          # same shape,
huawei.com/Ascend910C-core: 20   # any vendor
```

@col

::: card {tag=green}
### {icon:merge cls=accent-primary} 8+ clusters avoided
China Merchants Bank: Kunlunxin, Ascend, NVIDIA, PPU, Moore Threads, MetaX in **one pool**
:::

::: card {tag=cyan}
### {icon:network cls=accent-primary} Topology counts
Paired allocation on supernodes: **100% of the pool usable**, cross-machine scheduling **-30%** (CMB)
:::

---

@layout compare

## Evening: where DRA fits

@subtitle The request model changes, the enforcement doesn't

<!--
Promise 4: how DRA fits, and where it falls short.
Fits: HAMi-DRA is a mutating webhook that rewrites nvidia.com/gpu requests into DRA ResourceClaims. Kubernetes 1.34+ with the DRA Consumable Capacity feature gate and CDI in the runtime. Since HAMi v2.8 the same semantics exist on the DRA path: typed capacities in ResourceSlices (memory step 1 MiB, cores 0-100). A ResourceClaimTemplate mode exists for Kueue admission. Your pod YAML does not change.
Falls short today:
- DRA allocates; it does not enforce. HAMi-core (or the vendor mechanism) still has to hold the pod to its slice on the node.
- Claims are accounting: they tell you what was reserved, not what is used. Live usage needs a runtime collector.
- Feature gate plus recent Kubernetes: not where most fleets run yet.
- None of the 11 CNCF case studies runs DRA in production; Sangfor lists joining the HAMi DRA ecosystem as future work.
-->

::: card {tag=green}
### {icon:check cls=accent-primary} What DRA gives
- **HAMi-DRA** webhook rewrites `nvidia.com/gpu` into **ResourceClaims**
- K8s **1.34+**, Consumable Capacity gate + CDI
- Typed capacities: MiB, % cores
:::

::: arrow
{icon:arrow-right size=32}
:::

::: card {tag=red}
### {icon:triangle-alert cls=accent-secondary} Where it falls short
- Allocates, **does not enforce**
- Claims are **accounting, not usage**
- No CNCF case study runs it in production yet
:::

::: notes {tag=green}
DRA is the clean request API. You still need virtualization on the node and a scheduler that shares.
:::

---

## Night: sell the slices

@subtitle DaoCloud D.run: the box became a cloud

<!--
Promises 5 and 8: production patterns from cloud providers running 10,000+ GPUs.
DaoCloud CNCF case study (Dec 2025): HAMi active on 10,000+ GPU cards, DaoCloud-operated plus customer-owned. D.run is their public GPU cloud: 7 active regions, 10+ data centers, single regions up to ~3,000 GPUs.
What they did:
- vGPU slices with defined memory and compute, exposed as standardized SKUs in a central marketplace. Users pay by workload size, not by full card.
- Controlled over-subscription to lift cluster utilization.
- In DCE (their private platform): quotas and RBAC enforced at vGPU level, per department and queue.
- NVIDIA and domestic GPUs under one abstraction.
Results: >80% average utilization per card, 20-30% lower GPU-related opex.
This is the night shift of our H200: the slices from the morning are now products.
-->

::: card {metric}
10,000+
GPU cards under HAMi
:::

::: card {metric}
80%+
avg utilization per card
:::

::: card {metric}
20-30%
lower GPU opex
:::

::: grid {cols=4}
::: card {tag=cyan}
### {icon:tag cls=accent-primary} SKUs
Slices sold by workload size
:::
::: card {tag=green}
### {icon:layers cls=accent-primary} Over-subscription
Controlled, to lift utilization
:::
::: card {tag=yellow}
### {icon:users cls=accent-contrast} Quotas + RBAC
At vGPU level, per tenant
:::
::: card {tag=red}
### {icon:globe cls=accent-secondary} One abstraction
NVIDIA + domestic, 7 regions
:::
:::

---

## It's not just one H200

@subtitle 10x where the baseline is 5-15%, 2-3x platform-wide

<!--
Now generalise. Every number here is from a CNCF case study or our own measurement.
Per workload (red): CETC dev pods per device 2 -> 30 (15x). NIO CI utilization 5% -> 30-50%: up to 10x (their headline says 10x, the text says ~4x, so I say 'up to'). Sangfor models per GPU 1 -> 8+. Our H200: 3.4x req/s per card.
Whole platform (blue): Sangfor GPU utilization >3x. Ke Holdings 13% -> 37%. SNOW: 2x fewer GPUs for train + inference. China Merchants Bank 35% -> 60%+.
The honest version of the title: 10x is real where you start at 5-15%: CI, dev environments, notebooks, embedding, small inference. Whole platforms land at 2-3x because training already uses its cards.
Seven organisations measured whole-card baselines between 5 and 20%: NIO CI 5-10%, Ke 13%, Zhuoyu <15%, Sangfor 15-20%, PREP EDU 10-20%, CETC 12.5% of VRAM, our H200.
-->

```seaborn
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = [*plt.rcParams["font.sans-serif"], "DejaVu Sans"]

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
accent = plt.rcParams["axes.edgecolor"]
red = plt.rcParams["patch.edgecolor"]
plt.rcParams["patch.force_edgecolor"] = False

per_workload = [
    ("CETC", "dev pods per device, 2 to 30", 15, "15x"),
    ("NIO", "CI GPU util, 5% to 30-50%", 10, "up to 10x"),
    ("Sangfor", "models per GPU, 1 to 8+", 8, "8x"),
    ("Own H200", "req/s per card at same p95", 3.4, "3.4x"),
]
platform = [
    ("Sangfor", "GPU utilization", 3, "3x+"),
    ("Ke Holdings", "platform util, 13% to 37%", 2.8, "2.8x"),
    ("SNOW", "GPUs for train + inference", 2, "2x"),
    ("CMB", "avg util, 35% to 60%+", 1.7, "1.7x"),
]
fig, axes = plt.subplots(1, 2, figsize=(13, 3.6), gridspec_kw={"wspace": 0.05})
fig.patch.set_alpha(0)
for ax, rows, c, title in [(axes[0], per_workload, red, "PER WORKLOAD"), (axes[1], platform, accent, "WHOLE PLATFORM")]:
    ax.set_facecolor("none")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    ax.grid(False)
    ax.plot([10, 10], [-0.5, 3.5], color=dim, linewidth=1.1, linestyle=(0, (4, 3)), zorder=1)
    ax.text(10, 3.55, "10x", ha="center", va="bottom", fontsize=11, color=dim)
    ax.text(-11.5, 4.05, title, ha="left", va="bottom", fontsize=12, color=c, family="monospace", fontweight="bold")
    for i, (org, metric, v, lab) in enumerate(rows):
        y = 3 - i
        ax.barh(y, v, color=c, height=0.62, zorder=2)
        ax.text(-0.5, y + 0.15, org, ha="right", va="center", fontsize=13, color=fg, fontweight="bold")
        ax.text(-0.5, y - 0.24, metric, ha="right", va="center", fontsize=10, color=dim)
        ax.text(v + 0.3, y, lab, ha="left", va="center", fontsize=13, color=fg, fontweight="bold", zorder=3)
    ax.set_xlim(-11.5, 19)
    ax.set_ylim(-0.6, 4.5)
```

- **Whole-card baselines in the case studies: 5-20%.** Start there and 10x is reachable
- Whole platforms land at **2-3x**: training already uses its cards

---

## What production users don't share

@subtitle Share small, bursty, interactive. Keep big training whole.

<!--
Promise 6: best-fit workloads and overhead expectations, from the case studies.
Table: whole card for large training (Ke, CMB, NIO, CETC) and large LLM serving (CETC keeps 4 GPUs exclusive for text generation; Ke keeps H200/H100 for big LLMs). HAMi slices for small and bursty inference (Ke, Sangfor, DaoCloud, SF, PREP EDU, NIO), dev environments and notebooks (CETC, Zhuoyu, our Viettel notebook), CI and testing (NIO, SF test cluster), embedding and rerank (CETC). NIO uses MIG where algorithm developers need strong isolation, and plain time-slicing for contention-tolerant work.
Overhead, as measured:
- CETC: embedding on 8 GB and 20% compute: token throughput within 5% of a whole card, p95 latency and model load time essentially unchanged.
- NIO: ~1/6 GPU was optimal for simulation; 1/8 added scheduling and virtualization overhead and lowered throughput. Finer is not better.
- CMB: ResNet50 batch 32, single-card throughput 64.6 -> 94.8 images/s (+46.7%) with finer partitioning, because more work runs concurrently.
-->

| Workload | How it runs | Who |
| --- | --- | --- |
| Large training, large LLM serving | **Whole card** | Ke, CMB, NIO, CETC |
| Small or bursty inference | **HAMi slice** | Ke, Sangfor, DaoCloud, SF, PREP EDU, NIO |
| Dev envs, notebooks, CI | **HAMi slice** (MIG for hard isolation) | CETC, Zhuoyu, NIO, SF |
| Embedding, rerank | **HAMi slice** | CETC |

::: card {metric}
within 5%
throughput on a slice (CETC)
:::

::: card {metric}
1/6 beats 1/8
finer is not better (NIO)
:::

::: card {metric}
+46.7%
card throughput, partitioned (CMB)
:::

---

## Honest limits

@subtitle No vendor pitch: where sharing stops

<!--
Promise 9: limits and trade-offs, not only wins.
- Soft isolation is a resource and fairness control for trusted workloads, not a security boundary. CUDA_DISABLE_CONTROL=true skips the libvgpu.so preload; statically linked CUDA and direct /dev/nvidia* ioctls bypass it. Untrusted multi-tenant: MIG or VMs.
- Finer is not better: NIO's 1/8 slices lost throughput against 1/6.
- Training stays on whole cards: Ke, CMB and CETC all keep big training and big LLMs exclusive.
- MIG for hard isolation: NIO runs algorithm development on MIG, HAMi for CI, simulation, selected inference.
- Allocation is not utilization: scheduler and DRA numbers are reservations; live usage needs a runtime collector. Per-tenant telemetry is uneven across vendors (AMD has no first-party tenant path).
- Interception can clash with toolchains: NIO hit compiler/library features doing pointer and address analysis. Validate upgrades, roll out in phases, blue-green the device plugin for inference (NIO).
-->

::: grid {cols=3}
::: card {tag=red}
### {icon:shield-off cls=accent-secondary} Not a security boundary
`CUDA_DISABLE_CONTROL`, static CUDA, raw ioctls bypass the preload
:::
::: card {tag=yellow}
### {icon:scissors cls=accent-contrast} Finer is not better
NIO: 1/6 GPU beat 1/8
:::
::: card {tag=cyan}
### {icon:dumbbell cls=accent-primary} Training stays whole
Ke, CMB, CETC keep big jobs exclusive
:::
::: card {tag=cyan}
### {icon:lock cls=accent-primary} MIG for hard isolation
NIO: MIG for algorithm dev
:::
::: card {tag=yellow}
### {icon:chart-no-axes-column cls=accent-contrast} Allocation is not usage
Reserved slices are accounting
:::
::: card {tag=red}
### {icon:wrench cls=accent-secondary} Interception has edges
Toolchain clashes, validate upgrades (NIO)
:::
:::

---

## Blueprint: GPU box to GPU cloud

@subtitle The checklist, in the order of the day

<!--
Promise 8: the concrete blueprint. Same order as the day.
1. Profile workloads first, not a preset ratio (CETC's main lesson). Share the small, bursty, interactive ones; keep training whole.
2. Enforce: memory in MiB, compute in percent, per slice. Software interception where the vendor has no cap, vendor mechanism where it does.
3. Schedule: binpack or spread plus topology. Bring the brain you already run: Volcano, Kueue, Koordinator, KAI.
4. Scale on saturation: KEDA hands freed slices to whoever peaks next (SNOW scales ahead of ~60 s warm-up; CMB uses KEDA for inference, Kueue for training).
5. Sell: SKUs by slice, controlled over-subscription, quotas and RBAC at vGPU level (DaoCloud).
6. Measure usage, not allocation, per tenant; validate upgrades in phases (NIO).
-->

::: grid {cols=3}
::: card {tag=cyan}
### {icon:clipboard-list cls=accent-primary} 1. Profile
Share small, bursty, interactive. Keep training whole.
:::
::: card {tag=cyan}
### {icon:lock cls=accent-primary} 2. Enforce
MiB + % per slice, per vendor mechanism
:::
::: card {tag=cyan}
### {icon:layout-grid cls=accent-primary} 3. Schedule
binpack / spread + topology, your scheduler
:::
::: card {tag=green}
### {icon:trending-up cls=accent-primary} 4. Scale
KEDA on saturation hands slices off
:::
::: card {tag=green}
### {icon:tag cls=accent-primary} 5. Sell
SKUs, over-subscription, quotas + RBAC
:::
::: card {tag=green}
### {icon:activity cls=accent-primary} 6. Measure
Usage, not allocation, per tenant
:::
:::

---

<!--
Close: one card, one day, six mechanisms. 10x where you start at 5-15%, 2-3x for a whole platform, and the limits are real.
HAMi: CNCF Incubating, in production at hundreds of enterprises (CETC case study), 500+ contributors from 20+ countries, 4,900+ GitHub stars (GitHub API, 2026-10-24).
QR goes to the HAMi repo. Workshop labs: github.com/Project-HAMi/hami-workshop (ContainerDays Singapore track, same day 12:30).
Questions.
-->
@variant dark
@side-image assets/qr-hami-repo.png
@kicker CNCF Incubating · hundreds of enterprises · 4,900+ GitHub stars

# Thank you

@subtitle Questions?

@speaker name="Reza Jelveh" role="Head of Global Market, Dynamia" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

---

@hidden
## Backup: one isolation layer, several brains

@subtitle Every production case pairs sharing with a scheduler

<!--
BACKUP for 'which scheduler?' questions. Sangfor: Volcano (gang, LWS). SF Technology: kube-scheduler + Volcano, HAMi as extender + webhook + isolation. Zhuoyu: Koordinator Device Share, HAMi-Core only for isolation. CMB: Kueue for training, KEDA for inference. SNOW: KEDA on a custom saturation metric. DaoCloud: own quota + RBAC. KAI Scheduler's resource isolator delivers the same libvgpu.so.
-->

![One isolation layer, several scheduling brains](assets/containerdays/containerdays-scheduling-brains.svg)

---

@hidden
## Backup: reserved is not used

@subtitle Two metric families, keep them apart

<!--
BACKUP for observability questions. Scheduler and DRA metrics are reservations (allocation); vGPUmonitor or a runtime collector reports usage. Zhuoyu defines them explicitly: allocation = scheduled cards / schedulable cards (>95%); utilization = mean SM util from node telemetry (>55%).
-->

![Reservation vs usage](assets/containerdays/containerdays-reservation-usage.svg)

---

@hidden
@layout image-right
## Backup: DRA ResourceClaim

@subtitle The request side of DRA

<!--
BACKUP for DRA details. DeviceClass groups devices; ResourceClaim is the workload's ticket; ResourceClaimTemplate creates one claim per pod (the mode HAMi-DRA offers for Kueue).
-->

- **DeviceClass:** devices with one resource model
- **ResourceClaim:** a workload's ticket to hardware
- **ResourceClaimTemplate:** one claim per pod

![ResourceClaim and ResourceClaimTemplate](assets/hami/dra-resource-claim.png)
