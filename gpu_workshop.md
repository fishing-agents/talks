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

# Why GPUs need virtualization

---

## The GPU challenge

::: grid {cols=2}
::: card {tag=red}
### Supply side
- Many vendors: NVIDIA, AMD, Huawei Ascend, Cambricon, Hygon and more
- Each has its own device plugin, metrics and tools
- Hard to manage as one pool
:::
::: card {tag=yellow}
### Demand side
- GPUs are scarce and expensive
- Inference workloads are small and bursty
- Whole-card allocation leaves memory idle
:::
:::

---

## Kubernetes counts GPUs as whole units

- `nvidia.com/gpu: 1` means one full card, even for a 2 GB model.
- The device plugin API advertises a count. It has no notion of memory or compute share.
- Time-slicing shares a card but sets no memory limit per Pod.
- MIG gives hard partitions, on some cards only, with fixed profiles.

---

## What is HAMi

Heterogeneous AI Computing Virtualization Middleware

- Ask for a slice: `nvidia.com/gpumem` (MB) and `nvidia.com/gpucores` (%) next to `nvidia.com/gpu`
- Schedule by slice: a scheduler extender places Pods by free memory and cores per card
- Enforce in the container: HAMi-core limits memory and compute, no code changes
- Many vendors under one model: NVIDIA, Ascend, Cambricon, Hygon, Iluvatar, MetaX, AMD and more
- CNCF Incubating project, Apache 2.0

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

```json
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
- `hami_gpu_memory_allocated_bytes`
- `hami_gpu_core_allocated_ratio`
- `hami_node_gpu_memory_allocated_ratio`
- `hami_gpu_shared_count`
- `hami_vgpu_memory_allocated_bytes`
- `hami_resource_quota_used`
:::
::: card {tag=green}
### vGPUmonitor :9394, usage
- `hami_vgpu_memory_used_bytes`
- `hami_vgpu_memory_limit_bytes`
- `hami_container_device_utilization_ratio`
- `hami_host_gpu_utilization_ratio`
- `hami_host_gpu_memory_used_bytes`
- `hami_container_last_kernel_elapsed_seconds`
:::
:::

Same labels: `node`, `device_uuid`, `namespace`, `pod`. Join them in PromQL.

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

## Applicable scenarios

::: grid {cols=2}
::: card {tag=green}
### Online inference
Many low-traffic services share one card.
:::
::: card {tag=cyan}
### A/B testing
Original and candidate model on one GPU.
:::
::: card {tag=yellow}
### Mixed train and infer
Inference first, training fills the gaps.
:::
::: card {tag=red}
### Small model pipelines
Embedding, reranker and generator share cards.
:::
:::

---

@variant dark

# Thank you

@subtitle github.com/Project-HAMi/HAMi · project-hami.io · lab: github.com/fishing-agents/hami-workshop

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI - Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh
