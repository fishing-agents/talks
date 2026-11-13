---
theme: kubecon_na
seaborn_theme: hami
title: "HAMi"
logo: assets/brand/dynamia-logo.svg
logo_dark: assets/brand/dynamia-logo-white.png
watermark: assets/brand/cncf-logo.png
footer: "KubeCon + CloudNativeCon North America 2026 · HAMi project booth"
transition: fade
paginate: true
size: 16:9
style: |
  :root { --bg-overlay: rgba(255,255,255,0.95); }
  [data-theme="dark"] { --bg-overlay: rgba(5,34,67,0.92); }
  .layout-title { background: linear-gradient(rgba(5,34,67,0.2), rgba(5,34,67,0.2)), var(--bg-image) left top / cover no-repeat; }
  img[src$=".svg"] { max-height: 360px; }
  .layout-title .side-image { width: 170px; bottom: 40%; }
  .layout-title .side-image img { width: 170px; max-width: 170px; max-height: none; }

---

<!--
CNCF project booth loop, cut from kubecon_na_contribfest.deck.md: diagrams, charts and numbers only.
-->
@variant dark
@kicker KubeCon + CloudNativeCon North America 2026 · HAMi project booth

# HAMi

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI  -  Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

---

## Workshop lab cluster

```pdg
graph layout=row theme=hami gap=48
you "You" sub="laptop · kubectl"
group kind "kind cluster hami-lab" layout=column gap=36 {
  group top layout=row gap=40 .bare {
    sched "HAMi scheduler" sub=":9395 · real" .green
    node "hami-lab node" sub="2 × A100-40GB fake"
    plugin "mock-device-plugin" sub="gpumem · gpucores"
  }
  group bottom layout=row gap=40 .bare {
    pods "Pods" sub="share · pack · sim" .blue
    monitor "hami-mock-monitor" sub=":9394 · usage"
  }
}
plugin -> node
node -> sched "capacity"
you -> sched "kubectl apply"
sched -> pods "fit + bind" flow=forward
pods -> monitor "usage"
monitor -> you "metrics"
css { group.bare { fill: none; stroke: none; padding: 0; } }
```

---

## Allocation and usage metrics

```pdg
graph layout=row theme=hami gap=70
group alloc "Allocation · scheduler :9395" sub="what was reserved" layout=column gap=18 .blue {
  acard "Per card" sub="hami_gpu_memory_allocated_bytes\nhami_gpu_core_allocated_ratio"
  apod "Per pod" sub="hami_vgpu_memory_allocated_bytes\nhami_gpu_shared_count"
}
group usage "Usage · monitor :9394" sub="what is consumed" layout=column gap=18 .green {
  ucnt "Per container" sub="hami_vgpu_memory_used_bytes\nhami_container_device_utilization_ratio"
  ucard "Per card" sub="hami_host_gpu_memory_used_bytes\nhami_host_gpu_utilization_ratio"
}
alloc -> usage "alloc ≥ used"
```

---

## Flexible MIG on one A100

```seaborn
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = [*plt.rcParams["font.sans-serif"], "DejaVu Sans"]
plt.rcParams["patch.force_edgecolor"] = False

fg = plt.rcParams["text.color"]
dim = plt.rcParams["xtick.color"]
hami = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]  # HAMi green from seaborn_theme: hami
free = "#dfe2ec"

fig, ax = plt.subplots(figsize=(12.5, 4.2))
ax.set_facecolor("none")
fig.patch.set_alpha(0)

def card(y, blocks, title):
    ax.text(-0.3, y + 0.4, title, ha="right", va="center", fontsize=14, color=fg, fontweight="bold")
    for x0, w, colour, label in blocks:
        ax.barh(y + 0.4, w - 0.12, left=x0 + 0.06, height=0.8, color=colour)
        if label:
            ax.text(x0 + w / 2, y + 0.4, label, ha="center", va="center", fontsize=13,
                    color="white" if colour == hami else dim, fontweight="bold")

card(1.4, [(i, 1, free, "") for i in range(7)], "A100, empty")
card(0, [(0, 2, hami, "2g.10gb\nvLLM 1.7B"), (2, 3, hami, "3g.20gb\nvLLM 4B"),
         (5, 1, free, ""), (6, 1, free, "")], "A100, two Pods")
for i in range(7):
    ax.text(i + 0.5, 2.35, str(i + 1), ha="center", va="bottom", fontsize=11, color=dim)

ax.set_xlim(-2.6, 7.1)
ax.set_ylim(-0.2, 2.75)
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax.grid(False)
```

<!--
Live demo (hamidemo run pitch, A100s, 2026-11-10): the 10 GB server got 2g.10gb, then the 20 GB server binpacked onto the same A100 as 3g.20gb. HAMi creates the instances when the Pods start; nothing is pre-carved.
-->

---

## Whole GPU vs partitioned GPU

![Device Plugin vs DRA](assets/hami/device-plugin-vs-dra.png)

---

## Sharing a node with HAMi

![After HAMi](assets/hami_intro/after-hami.png)

---

## The GPU stack

```pdg
graph layout=column align=stretch gap=8 theme=hami
default group layout=row gap=10 .tier
group l5 "Kubernetes scheduling" {
  ks "kube-scheduler"
  hs "HAMi scheduler" .hami
  p "Pod"
}
group l4 "Container runtime" {
  c "containerd"
  t "NVIDIA Container Toolkit"
  hc "HAMi-Core" .hami
}
group l3 "User-space libraries" {
  cu "CUDA"
  nv "NVML"
  smi "nvidia-smi"
}
group l2 "Kernel driver" {
  ko "nvidia.ko"
  uvm "nvidia-uvm.ko"
}
group l1 "Hardware" {
  g "NVIDIA GPU"
  pc "PCIe"
  nl "NVLink"
}
legend .hami "HAMi component"
css {
  group.tier { fill: #ffffff; stroke: var(--border); title-fill: none; padding: 8px 12px; }
  node { font-weight: normal; padding: 5px 12px; }
  node.hami { fill: var(--green); stroke: var(--green); color: #ffffff; font-weight: 600; }
}
```

---

## From Pod to GPU

```pdg
graph layout=row theme=hami gap=40 steps=auto
group panels layout=row align=stretch gap=40 .bare {
group cp "Control plane" sub="decides where the Pod runs" layout=column gap=30 {
  pod "Pod" sub="nvidia.com/gpumem: 3000"
  webhook "MutatingWebhook" sub="sets schedulerName" .blue
  sched "HAMi scheduler" sub="picks a node and a card" .blue
}
group node "GPU node" sub="sets up the container, enforces limits" layout=column gap=30 .green {
  kubelet "kubelet" sub="starts the Pod"
  plugin "HAMi device plugin" sub="mounts libvgpu.so" .green
  core "HAMi-Core" sub="checks memory and kernel calls" .green
}
}
gpu "GPU" border=glow
pod -> webhook flow=forward
webhook -> sched flow=forward
sched -> kubelet "bind" flow=forward
kubelet -> plugin "Allocate()" flow=forward
plugin -> core flow=forward
core -> gpu flow=forward
css { group.bare { fill: none; stroke: none; padding: 0; } }
```

---

## HAMi components

```pdg
graph layout=row theme=hami gap=56
group cp "Control plane" layout=column gap=22 {
  api "Kubernetes API" sub="Pods · node annotations"
  hs "hami-scheduler Pod" sub="webhook + extender · :9395" .blue
}
group node "Each GPU node" layout=column gap=22 .green {
  dp "hami-device-plugin" sub="DaemonSet · registers cards" .green
  core "HAMi-core" sub="libvgpu.so in the container" .green
  mon "vGPUmonitor" sub="usage · :9394" .green
}
group obs "Observability" layout=column gap=22 {
  prom "Prometheus" sub="scrapes :9395 and :9394"
  ui "HAMi-WebUI" sub="read-only dashboards" .blue
}
dp -> api "node-nvidia-register"
api <-> hs "annotations"
dp -> core "mounts"
core -> mon "shared region"
hs -> prom "allocated"
mon -> prom "used"
prom -> ui
```

---

## `nvidia-smi` vs `lsmod`

```pdg
graph layout=column align=stretch gap=8 theme=hami
group user "User space" layout=row gap=24 .space {
  nvml "libnvidia-ml.so" sub="NVML" align-x=nvidia .blue
  libcuda "libcuda.so" sub="CUDA driver API" align-x=uvm .blue
}
group kernel "Kernel space" layout=row gap=60 .kspace {
  nvidia "nvidia" sub="core GPU driver" .green
  uvm "nvidia_uvm" sub="unified memory" .green
}
group hw "Hardware" layout=row .space {
  gpu "NVIDIA GPU"
}
nvml -> nvidia
libcuda -> uvm "ioctl"
uvm -> nvidia "depends on"
nvidia -> gpu
bracket nvml, gpu "nvidia-smi needs\nthe whole path"
bracket nvidia, uvm "lsmod checks\nonly this layer"
css {
  group.space, group.kspace { label-position: left; title-fill: none; stroke: none; }
  group.space { fill: #eff6ff; color: var(--blue); }
  group.kspace { fill: #f0fdf4; color: var(--green); }
  node.blue, node.green { accent-bar: none; }
  node.blue { color: var(--blue); }
  node.green { color: var(--green); }
}
```

---

## Topology sources

```pdg
graph layout=row theme=hami gap=56
group src "On the node" layout=column gap=14 {
  nv "NVIDIA · NVML" sub="NVLink and PCIe P2P links"
  amd "AMD · KFD topology" sub="XGMI peers, NUMA node"
  mx "MetaX · vendor plugin" sub="MetaXLink and PCIe switch"
  kl "Kunlunxin, AWS Neuron" sub="fixed board layout by index"
}
dp "Device plugin" sub="per vendor, DaemonSet" .green
anno "Node annotations" sub="register: numa, links\nscores: pair scores" border=glow
hs "hami-scheduler" sub="Filter + Score per vendor" .blue
nv -> dp
amd -> dp
mx -> dp
kl -> dp
dp -> anno "patches" flow=forward
anno -> hs "reads" flow=forward
```

---

## NUMA refit

```pdg
graph layout=row theme=hami gap=40 steps=auto
hs "hami-scheduler" sub="picks GPU-3" .blue
tm "kubelet Topology Manager" sub="CPUs on NUMA 0 · allows GPU-0..1"
dp "HAMi device plugin" sub="GPU-3 not allowed"
rf "/refit" sub="re-run the fit on GPU-0..1" .green border=glow
pod "Pod" sub="CPUs + GPU on NUMA 0" .green
hs -> tm flow=forward
tm -> dp flow=forward
dp -> rf "ask" flow=forward
rf -> pod "annotations + accounting moved" flow=forward
```

---

## Flexible MIG allocation

```pdg
graph layout=row theme=hami gap=36 steps=auto
nvml "NVML on the node" sub="profiles + legal placements"
sch "HAMi scheduler" sub="smallest profile that fits · no overlap" .blue
ann "Pod annotation" sub="hami.io/vgpu-mig-allocations"
dp "Device plugin" sub="creates GI/CI at Allocate" .green
nvml -> sch "migProfiles" flow=forward
sch -> ann "reserve" flow=forward
ann -> dp flow=forward
```

---

## Device plugin vs DRA

```pdg
graph layout=row theme=hami gap=60
group dp "Device plugin" sub="classic HAMi" layout=column gap=24 {
  dpp "HAMi device plugin" sub="reports each card 10 times" .blue
  ann "Node annotation" sub="hami.io/node-nvidia-register"
  ext "HAMi scheduler extender" sub="reads the annotation, picks a card" .blue
}
group dra "DRA" sub="HAMi-DRA, Kubernetes 1.34+" layout=column gap=24 .green {
  drv "DRA driver" sub="kubelet plugin" .green
  rs "ResourceSlice" sub="typed attributes and capacity"
  ks "kube-scheduler" sub="DRA plugin, no extender" .green
}
dpp -> ann "writes"
ann -> ext "reads"
drv -> rs "publishes"
rs -> ks "reads"
```

---

## HAMi-DRA

```pdg
graph layout=row theme=hami gap=36 steps=auto
pod "Pod" sub="nvidia.com/gpu, gpumem, gpucores"
wh "HAMi-DRA webhook" sub="rewrites the request" .blue
rc "ResourceClaim" sub="or ResourceClaimTemplate"
ks "kube-scheduler" sub="DRA allocation" .blue
core "HAMi-Core" sub="same in-container limits" .green
pod -> wh flow=forward
wh -> rc flow=forward
rc -> ks flow=forward
ks -> core flow=forward
```

---

## HAMi in production

@subtitle From CNCF case studies

::: grid {cols=4}
::: card {metric}
10,000+
GPU cards under HAMi across D.run and DCE
DaoCloud
:::
::: card {metric}
80%+
average utilization per card, 20-30% lower GPU opex
DaoCloud
:::
::: card {metric}
2x
fewer GPUs for training + inference, 700% traffic spikes handled
SNOW Corp.
:::
::: card {metric}
15x
dev pods on the same device: 2 to 30, throughput within 5%
CETC Cloud
:::
:::

---

@layout ecosystem
## Community & Adopters

#### Open Source, CNCF Backed, Production Ready
::: grid {cols=5}
::: card {metric}
5k
Github Stars
:::
::: card {metric}
700k
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
![NVIDIA](assets/ecosystem/devices/nvidia.png)

![AMD](assets/ecosystem/devices/amd.png) ![Ascend](assets/ecosystem/devices/ascend.png) ![Cambricon](assets/ecosystem/devices/cambricon.png) ![Hygon](assets/ecosystem/devices/hygon.png) ![Iluvatar](assets/ecosystem/devices/illuvitar.png)
![Metax](assets/ecosystem/devices/metax.png) ![Moore Threads](assets/ecosystem/devices/moorethreads.png) ![Kunlunxin](assets/ecosystem/devices/kunlunxin.png) ![Enflame](assets/ecosystem/devices/enflame.png)

![Biren](assets/ecosystem/devices/biren.png)![AWS](assets/ecosystem/devices/aws.png) ![VastStream](assets/ecosystem/devices/vaststream.png)
:::
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

@variant dark

# Thank you

@subtitle github.com/Project-HAMi/HAMi · project-hami.io

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI  -  Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh
