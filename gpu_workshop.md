---
theme: kubecon_japan
title: "GPU Virtualization: First Setup and Understanding the Device Plugin / DRA"
logo: assets/brand/dynamia-logo.svg
logo_dark: assets/brand/dynamia-logo-white.png
footer: "HAMi ContribFest"
transition: fade
paginate: true
size: 16:9
style: |
  section.lab h1 { font-size: 3em; }

---

<!--
75 min ContribFest. Plan: gpu_workshop_plan.md. Lab guide: fishing-agents/hami-workshop docs/labs/contribfest.md.
Lab commands and outputs on these slides are from a run on 2026-10-20 (kind 0.33, HAMi chart 2.10.0, hami-mock-monitor 86adb51).
-->
@variant dark
@side-image assets/qr-hami-repo.png
@kicker KubeCon ContribFest · CNCF Incubating project

# GPU Virtualization with HAMi

@subtitle First setup, the device plugin, and the road to DRA

@speaker name="Xiao Zhang" role="HAMi Maintainer, CEO Dynamia AI" github=github.com/wawa0210
@speaker name="Mengxuan Li" role="HAMi Maintainer, Chief Architect" github=github.com/archlitchi
@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI - Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

---

## Today: 75 minutes, four labs

::: grid {cols=4}
::: card {tag=cyan}
### Lab 1
Install HAMi on kind with two fake GPUs.
:::
::: card {tag=green}
### Lab 2
Share a GPU. Read what the scheduler decided.
:::
::: card {tag=yellow}
### Lab 3
Observe allocation and usage metrics.
:::
::: card {tag=red}
### Lab 4
Open a draft PR with a maintainer.
:::
:::

Lab guide: **github.com/fishing-agents/hami-workshop** → Labs → ContribFest

<!--
Ask who has setup.sh already done. Helpers raise hands so people know who to ask.
-->

---

## Get ready while we talk

```bash
git clone https://github.com/fishing-agents/hami-workshop
cd hami-workshop/examples/contribfest
git clone https://github.com/fishman/hami-mock-monitor
./setup.sh        # about 3 minutes
```

Needs Docker, kind, kubectl, helm, jq. No GPU.

---

# Why HAMi

---

## The Problem

@subtitle One GPU per task is the default

Kubernetes allocates GPUs atomically: one whole device, one task.

- A 1 GB task blocks an 80 GB device
- Most GPUs sit idle most of the time
- DRA (Dynamic Resource Allocation) is stable, but still work in progress
- No advanced scheduling yet: no binpack, no spread, no topology

![Device Plugin vs DRA](assets/hami/device-plugin-vs-dra.png)

---

## What is HAMi

@subtitle Before: one GPU, one task

<!--
GPUs are expensive and often underutilized. HAMi is a heterogeneous GPU sharing framework for Kubernetes. It slices GPUs and shares them across workloads, without rewriting your stack.
-->

![Before HAMi](assets/hami_intro/before-hami.png)

---

## What is HAMi
@transition none

@subtitle After: one GPU, many tasks

![After HAMi](assets/hami_intro/after-hami.png)

---

@layout compare

## The GPU Challenge

@subtitle What breaks, what HAMi needs to solve

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

---

## Architecture

1. **Mutating webhook**: routes GPU Pods to `hami-scheduler`
2. **Scheduler extender**: `Filter`, score, `Bind` against per-card state
3. **Device plugin**: registers cards, implements `Allocate`
4. **HAMi-core**: `libvgpu.so` in the container, enforces limits
5. **vGPUmonitor**: per-container usage metrics

Code: `cmd/scheduler`, `cmd/device-plugin`, `cmd/vGPUmonitor`, `pkg/device/<vendor>`

---

## Where the scheduler gets its cards

The device plugin reads the GPUs (NVML) and writes them to the node:

```text
hami.io/node-nvidia-register: [
 {"id":"GPU-mock-0","index":0,"count":10,"devmem":40960,
  "devcore":100,"type":"NVIDIA-A100-SXM4-40GB","health":true}, ...]
```

- `count`: how many Pods may share the card
- `devmem` in MB, `devcore` in percent
- The mock device plugin skips NVML. You write this annotation yourself.

---

## Lab setup: real scheduler, fake GPUs

::: grid {cols=2}
::: card {tag=cyan}
### mock-device-plugin
Turns the node annotation into `gpumem` and `gpucores` capacity. Part of the HAMi chart: `mockDevicePlugin.enabled=true`.
:::
::: card {tag=green}
### hami-mock-monitor
Serves the vGPUmonitor metrics from a load source. Completes the bind the mock plugin skips.
:::
:::

You do not get isolation inside the container. That part needs HAMi-core and a real GPU.

---

@variant dark
<!--
~15:00. Target: 10 minutes. Helpers check everyone gets gpumem=81920.
-->

# Lab 1: Install HAMi

@subtitle docs/labs/contribfest.md → Lab 1

---

## Lab 1: what setup.sh does

```bash
kind create cluster --name hami-lab
helm install hami hami-charts/hami -n kube-system --version 2.10.0 \
  --set devicePlugin.enabled=false --set mockDevicePlugin.enabled=true
kubectl patch node $NODE --subresource=status --type=json \
  -p '[{"op":"add","path":"/status/capacity/nvidia.com~1gpu","value":"20"}]'
kubectl annotate node $NODE "hami.io/node-nvidia-register=$(cat fake-gpus.json)"
```

Done when allocatable shows `gpu: 20`, `gpumem: 81920`, `gpucores: 200`.

---

# How a GPU request is placed

---

## Asking for a slice

```yaml
resources:
  limits:
    nvidia.com/gpu: 1          # number of cards
    nvidia.com/gpumem: 15000   # MB per card
    nvidia.com/gpucores: 30    # % of each card
```

Also: `nvidia.com/gpumem-percentage`, and annotations to pick or avoid card types (`nvidia.com/use-gputype`, `nvidia.com/nouse-gputype`).

---

## Filter, score, bind

- **Filter** calls `Fit()` for each card: enough memory, cores and share slots left?
- **Score** applies the node and GPU policies: `binpack`, `spread`, topology-aware, NUMA
- **Bind** writes the decision on the Pod and takes the node lock `hami.io/mutex.lock`

```text
hami.io/vgpu-devices-allocated: GPU-mock-1,NVIDIA,15000,30:;
hami.io/bind-phase: allocating
```

Code: `pkg/scheduler/scheduler.go`, `pkg/device/nvidia/device.go`

---

## The device plugin's job

- Kubelet calls `Allocate` with the device IDs it picked from the count resource.
- HAMi's plugin ignores that choice and reads the Pod annotation instead.
- It mounts the chosen card, sets `CUDA_DEVICE_MEMORY_LIMIT` and `CUDA_DEVICE_SM_LIMIT`, and injects HAMi-core.
- It sets `bind-phase=success` and releases the node lock.

The mock plugin does not finish this step. hami-mock-monitor's `completeBinds` does it for the lab.

---

@variant dark
<!--
~30:00. Target: 12 minutes. Ask: why is too-big pending when 3 x 15000 < 81920?
-->

# Lab 2: Share a GPU

@subtitle docs/labs/contribfest.md → Lab 2

---

## Lab 2: three Pods, two cards

```bash
kubectl apply -f share.yaml -f too-big.yaml
kubectl get pods
kubectl get events --field-selector involvedObject.name=too-big | tail -1
```

```text
share-1   1/1   Running   GPU-mock-1,NVIDIA,15000,30
share-2   1/1   Running   GPU-mock-0,NVIDIA,15000,30
share-3   1/1   Running   GPU-mock-1,NVIDIA,15000,30
too-big   0/1   Pending   2/2 CardInsufficientMemory
```

45000 MB fits the node total, but no single 40960 MB card.

---

## Lab 2: change the policy

```yaml
metadata:
  annotations:
    hami.io/gpu-scheduler-policy: binpack   # or spread
```

- `binpack`: both Pods on `GPU-mock-0`. Frees whole cards for big jobs.
- `spread`: one Pod per card. Less contention.

---

# Observability: reserved is not used

---

## Two metric sources

::: grid {cols=2}
::: card {tag=cyan}
### Scheduler :9395, allocation
- `gpu_memory_allocated_bytes`
- `gpu_core_allocated_ratio`
- `node_gpu_memory_allocated_ratio`
- `gpu_shared_count`
- `vgpu_memory_allocated_bytes`
- `resource_quota_used`
:::
::: card {tag=green}
### vGPUmonitor :9394, usage
- `vgpu_memory_used_bytes`
- `vgpu_memory_limit_bytes`
- `container_device_utilization_ratio`
- `host_gpu_utilization_ratio`
- `host_gpu_memory_used_bytes`
- `container_last_kernel_elapsed_seconds`
:::
:::

All names start with `hami_`. Same labels: `node`, `device_uuid`, `namespace`, `pod`. Join them in PromQL.

---

## Units and scopes

- Memory: bytes. Cores: percent of one whole card, 100 = full card.
- `hami_container_device_utilization_ratio` is the container's share of the card, so containers on one card sum to the host value.
- Allocated ratio is 0 to 1. Utilization ratios are 0 to 100.
- Real vGPUmonitor also reports temperature, power, ECC errors and time since last kernel. Use the last one to find idle reservations.

---

## Without a GPU: hami-mock-monitor

Reads only what HAMi writes to the API (Pod allocation, node registration) and fills in usage from a load source:

- `seed`: a sine curve per container, repeatable
- `static`: fixed values
- `vllm`: scrapes a vLLM `/metrics` endpoint. Running requests / max seqs = load.

Utilization = load × allocated cores. A container at full load on 30 cores reports 30.

github.com/fishman/hami-mock-monitor

---

@variant dark
<!--
~45:00. Target: 12 minutes. The sim oscillates over 2 minutes, give it time.
-->

# Lab 3: Observe

@subtitle docs/labs/contribfest.md → Lab 3

---

## Lab 3: allocated vs used

```bash
./metrics.sh scheduler | grep node_gpu_memory_allocated_ratio
./metrics.sh monitor   | grep host_gpu_utilization_ratio
```

From our run, with `share-1` and `share-3` on `GPU-mock-1`:

```text
hami_node_gpu_memory_allocated_ratio{device_uuid="GPU-mock-1"} 0.73
hami_host_gpu_utilization_ratio{device_uuid="GPU-mock-1"}      24.0
```

73% of memory is reserved. 24% of compute is busy.

---

## Lab 3: an inference load

```bash
kubectl apply -f sim.yaml     # llm-d-inference-sim, 0 to 5 requests over 2 min
watch -n 5 "./metrics.sh monitor | grep 'pod=\"sim\"'"
```

```text
hami_container_device_utilization_ratio{pod="sim"} 26.4
```

Moves between 0 and 33 (its `gpucores`). Memory stays at 0.9 × limit, because vLLM preallocates its KV cache.

---

## Live: isolation on a real GPU

::: grid {cols=2}
::: card {tag=cyan}
### Ask
`nvidia.com/gpumem: 3000`
:::
::: card {tag=green}
### See
`nvidia-smi` in the Pod reports 3000 MiB total.
:::
:::

Allocating past the limit fails inside the Pod with out of memory. Neighbours keep running.

<!--
Presenter only, real NVIDIA node. Pre-recorded fallback if the node is down.
-->

---

# The road to DRA

---

## Device plugin vs DRA

::: grid {cols=2}
::: card {tag=yellow}
### Device plugin
- Count of identical devices
- HAMi adds memory and cores via extended resources and annotations
- Needs a scheduler extender
:::
::: card {tag=green}
### Dynamic Resource Allocation
- ResourceClaims with device attributes
- Consumable capacity: memory and cores as first-class claims
- kube-scheduler does the placement
:::
:::

---

## HAMi-DRA

- A mutating webhook that turns `nvidia.com/gpu`, `gpumem`, `gpucores` requests into ResourceClaims.
- Users keep the same Pod spec. The cluster moves to DRA underneath.
- Multi-vendor: NVIDIA, Hygon, Ascend.
- Requires Kubernetes 1.34+ with DRA consumable capacity and CDI in the runtime.

github.com/Project-HAMi/HAMi-DRA

---

@variant dark
<!--
~62:00. Target: 10 minutes. Maintainers walk the room.
-->

# Lab 4: Contribute

@subtitle docs/labs/contribfest.md → Lab 4

---

## Lab 4: pick one

::: grid {cols=3}
::: card {tag=cyan}
### HAMi
`make test`. Start in `Fit`, `Filter`, `Bind`. `git commit -s`.
:::
::: card {tag=green}
### Mocks
Complete the bind in mock-device-plugin. More vendors in hami-mock-monitor. A lab Grafana dashboard.
:::
::: card {tag=yellow}
### DRA and docs
HAMi-DRA webhook, lab fixes, Chinese pages.
:::
:::

Look for `good first issue`. Open a draft PR before you leave.

---

# Bring your own scheduler

@subtitle HAMi with Volcano and KAI Scheduler

<!--
Reference section, not a hands-on lab: both paths need a real NVIDIA GPU. Sources: project-hami.io tutorials Lab 8 (Volcano vGPU, verified 2026-06-08) and Lab 12 (KAI Scheduler on GKE), plus docs/userguide/kai-scheduler.
-->

---

## Three ways to use HAMi

::: grid {cols=3}
::: card {tag=cyan}
### Standard HAMi
HAMi scheduler extender + HAMi device plugin.
`nvidia.com/gpu`, `gpumem`, `gpucores`
:::
::: card {tag=green}
### Volcano vGPU
Volcano `deviceshare` + volcano-vgpu-device-plugin.
`volcano.sh/vgpu-number`, `vgpu-memory`, `vgpu-cores`
:::
::: card {tag=yellow}
### KAI Scheduler
KAI GPU sharing + kai-resource-isolator.
`gpu-memory` or `gpu-fraction` annotation
:::
:::

All three use **HAMi-core** in the container for isolation. One device-plugin path per GPU node.

---

## Volcano: batch semantics on shared GPUs

```yaml
# volcano-scheduler.conf, second tier
- name: deviceshare
  arguments:
    deviceshare.VGPUEnable: true
    deviceshare.SchedulePolicy: binpack
```

```bash
kubectl apply -f https://raw.githubusercontent.com/Project-HAMi/volcano-vgpu-device-plugin/v1.11.0/volcano-vgpu-device-plugin.yml
```

- No HAMi install needed. The node shows `volcano.sh/vgpu-number` and `vgpu-memory`.
- Volcano 1.9 to 1.15 with plugin v1.11.0.

---

## Volcano: gang jobs and queue caps

```yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
spec:
  schedulerName: volcano
  minAvailable: 2          # both workers or none
  queue: vgpu-queue
  tasks:
  - replicas: 2
    template:
      spec:
        containers:
        - resources:
            limits:
              volcano.sh/vgpu-number: 1
              volcano.sh/vgpu-memory: 2000
              volcano.sh/vgpu-cores: 30
```

- Gang that does not fit: PodGroup stays `Inqueue`, `NotEnoughResources`.
- Queue `capability` caps vGPU memory per team, even when the node has room.

---

## KAI Scheduler: HAMi-core for hard isolation

```bash
helm install kai-scheduler oci://ghcr.io/nvidia/kai-scheduler --version v0.17.0 \
  --set global.gpuSharing=true --set binder.plugins.hamicore.enabled=true \
  -n kai-scheduler --create-namespace
helm install kai-resource-isolator oci://docker.io/projecthami/kai-resource-isolator \
  --version 1.0.0-chart -n kai-resource-isolator --create-namespace
```

- KAI keeps its own scheduling and queues. It adds HAMi-core only for memory isolation.
- KAI injects `CUDA_DEVICE_MEMORY_LIMIT`. The isolator injects `libvgpu.so` with a webhook.
- Cooperative sharing becomes a hard memory cap.

---

## KAI Scheduler: request a slice

```yaml
metadata:
  labels:
    kai.scheduler/queue: default-queue
  annotations:
    gpu-memory: "4096"        # MiB, no suffix
spec:
  schedulerName: kai-scheduler
```

- `nvidia-smi` in the Pod shows about 4096 MiB. KAI rounds to a two-decimal fraction: 4096 on a 15360 MiB T4 becomes 0.27, about 4147 MiB.
- Opt out: `kai-resource-isolator.io/inject: "false"`.

---

## Which path when

- **Standard HAMi**: many vendors, memory and core slices, binpack and spread per GPU, the metrics from Lab 3.
- **Volcano vGPU**: training and batch jobs that need gang scheduling and team queues.
- **KAI Scheduler**: clusters already on KAI that want a hard memory cap.

Hands-on guides: project-hami.io → Tutorials → Lab 8 (Volcano vGPU), Lab 12 (KAI Scheduler on GKE)

---

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

---

@variant dark

# Thank you

@subtitle github.com/Project-HAMi/HAMi · project-hami.io · lab: github.com/fishing-agents/hami-workshop

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI - Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh
