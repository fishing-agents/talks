---
theme: kubecon_japan
title: "One Agent, Every GPU: Vendor-Neutral Observability from the Kubernetes Scheduler"
logo: assets/brand/hami-logo.png
logo_dark: assets/brand/hami-logo.png
watermark: assets/brand/kubecon_japan/cncf_logo.svg
footer: "HAMi Cross-Platform Observability | Source audit 2026-09-30"
transition: fade
paginate: true
size: 16:9
style: |
  :root {
    --logo-hami: url("assets/brand/hami-logo.png");
    --logo-dynamia: url("assets/brand/dynamia-logo.svg");
    --logo-dynamia-white: url("assets/brand/dynamia-logo-white.png");
  }
  section::before {
    width: 24%;
    padding-bottom: 5%;
    background:
      var(--logo-hami) left center / auto 65% no-repeat,
      var(--logo-dynamia) right center / auto 58% no-repeat;
  }
  section.layout-title::before,
  section[data-theme="dark"]::before,
  [data-theme="dark"] section::before {
    background:
      var(--logo-hami) left center / auto 65% no-repeat,
      var(--logo-dynamia-white) right center / auto 58% no-repeat;
  }
  .notes { font-size: 0.55em; padding: 0.3em 0; background: none; border: none; margin-top: 1em; }
  section.layout-title footer, section.layout-title .slide-num { color: rgba(255,255,255,0.6); }
  :root { --list-style: "- "; }
---

<!--
Audience narrative supplied by Reza. Implementation audit spans all 23 public Project-HAMi repositories at pinned local commits. No GPU hardware, workloads, runtime scrape, production observations or OTLP deployment were tested. Scheduling visibility covers HAMi-managed requests and allocations, not all device-plugin workloads or GPU operations.
-->
@variant dark
@kicker Kubernetes GPU observability

# One Agent, Every GPU: Vendor-Neutral Observability from the Kubernetes Scheduler

@subtitle One workload view across heterogeneous GPUs: connect scheduling intent, runtime usage and application outcomes

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI - Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

---

<!--
The supplied brief names vendor ecosystems as motivation. Intel XPU Manager is a context example, not an audited HAMi integration or a promise of Intel runtime support. Vendor tools can have Kubernetes/workload attribution; the gap is the complete intent-to-outcome correlation, not that vendor metrics can never be attributed.
-->

## One question, several vendor dashboards

::: grid {cols=2}
::: card {tag=cyan}
### The question
Are our accelerator workloads using the capacity we reserve efficiently?
:::
::: card {tag=yellow}
### The fragmentation
NVIDIA DCGM/NVML, AMD ROCm SMI, Intel XPU Manager and Ascend tooling expose different views.
:::
::: card {tag=green}
### The missing connection
Who requested this capacity? What was allocated? Which application benefits?
:::
::: card {tag=cyan}
### The architecture
Keep vendor sensors. Add a common workload identity and scheduling-intent layer.
:::
:::

---

<!--
These are operating-model differences, not a claim that CPU observability is perfect. A device plugin has resource discovery, health and allocation interfaces; a workload telemetry contract is separate. MIG has hardware resource/isolation boundaries and must not be conflated with soft vGPU sharing.
-->

## Why GPU observability is harder than CPU

- CPU time is commonly charged to a process or cgroup.
- A device-plugin allocation grants access; it does not report executed work.
- Contexts, streams and asynchronous execution complicate attribution.
- Shared GPUs and MIG introduce multiple capacity and identity scopes.
- Device activity alone cannot explain request size or application latency.

::: notes
Source: [Kubernetes device-plugin contract](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/); [CUDA contexts](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__DRIVER.html); [MIG isolation](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/introduction.html)
:::

---

<!--
CUDA context and MIG are NVIDIA-specific examples explaining the general identity problem. A claimed utilization percentage needs a scope, sampling interval and denominator. Do not sum arbitrary GPU activity percentages or compare whole-card activity to a tenant reservation.
-->

## Contexts and partitions change attribution and scope

::: grid {cols=2}
::: card {tag=cyan}
### CUDA context
Memory and execution live in driver/runtime contexts. A Pod-to-device mapping does not reveal every operation.
:::
::: card {tag=yellow}
### MIG instance
Use instance/profile identity and partition capacity. Whole-card utilization can hide an idle or saturated slice.
:::
::: card {tag=green}
### Soft-shared vGPU
Limits and accounting depend on the runtime interposition and sharing mode.
:::
::: card {tag=red}
### Comparison rule
Compare matching physical, partition or tenant scopes with documented units.
:::
:::

::: notes
Source: [CUDA runtime/context interaction](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__DRIVER.html); [MIG guide](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/introduction.html); [MIG and accounting identities](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L118-L138)
:::

---

<!--
These are distinct signal planes. A reservation is not measured runtime consumption. The last plane is an architectural requirement, not automatically supplied by HAMi.
-->

## Four questions, four signal planes

::: grid {cols=2}
::: card {tag=cyan}
### Capacity and reservations
What can the scheduler place? Which workload owns each reservation?
:::
::: card {tag=green}
### Physical-device activity
Memory, compute, power, temperature and device errors.
:::
::: card {tag=yellow}
### Workload attribution
Which container consumes memory or compute on a shared device?
:::
::: card {tag=red}
### Application service level
Request latency, throughput, queue depth and failures.
:::
:::

::: notes
Source: [scheduler](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L157-L200); [runtime](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L53-L140)
:::

---

<!--
Admission control, scheduling and runtime are distinct stages. HAMi is not a global observer for arbitrary device-plugin allocations; coverage requires a HAMi integration. The architecture combines existing HAMi accounting with runtime sources. Admission and scheduling traces described later are proposed additions.
-->

## Instrument intent and decisions at separate stages

::: grid {cols=2}
::: card {tag=cyan}
### Admission
Requested resources, policy changes and rejection. This stage has no measured GPU usage.
:::
::: card {tag=green}
### Scheduling and allocation
Selected device, reserved capacity, no-fit failures and bind rollback.
:::
::: card {tag=yellow}
### Runtime
Measured activity, memory consumption and collector health after the workload starts.
:::
::: card {tag=red}
### Application
Latency, throughput, queue depth and errors. Connect to device observations through workload identity.
:::
:::

::: notes
Source: [scheduler capacity](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L157-L200); [scheduling outcome counters](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/pkg/metrics/scheduler.go#L29-L55); [tenant runtime metrics](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L92-L140)
:::

---

<!--
The scheduler uses backend device metadata. Core semantics still require vendor review. Do not interpret every suffix _ratio as a normalized 0-1 value.
-->

## Scheduler observability is cross-vendor accounting

- Device limits, allocated memory, allocated cores and sharing count.
- Container reservations and namespace quotas.
- Leader state, cache synchronization and bounded failure reasons.
- AMD compute-unit reservations receive percentage normalization.
- These describe **placement and reservation**, not measured accelerator work.

::: notes
Source: [AMD normalization](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L64-L74); [allocation families](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L157-L200); [outcome counters](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/pkg/metrics/scheduler.go#L29-L55)
:::

---

<!--
Scheduler reservation labels are namespace,node,pod,device_uuid; runtime labels include namespace,pod,container,vdevice_index,device_uuid. A common recording-rule layer must reconcile these scopes. The scheduler iterates container/device allocations without container labels in the new family, so multi-container same-device emission/aggregation must be validated. Never perform an arbitrary direct division. Runtime memory_limit_bytes has the same labels as memory_used_bytes and supports a scoped NVIDIA memory-use/limit comparison, subject to scrape freshness and positive limits.
-->

@layout image-right

## Reservation and consumption answer different questions

::: grid {cols=2}
::: card {tag=cyan}
### Reserved memory
`hami_vgpu_memory_allocated_bytes`

Scheduler reservation at Pod/device scope.
:::
::: card {tag=green}
### Consumed memory
`hami_vgpu_memory_used_bytes`

Runtime accounting at container/vdevice scope.
:::
:::

![HAMi WebUI overview: Memory Alloc 77.8% reserved vs Memory Usage 10.5% consumed; the Alloc Rate trend line stays flat near 80 while Usage Rate oscillates 10-45](assets/hami/webui-overview-cropped.png)

::: notes
Source: [workload allocations](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L389-L455); [tenant runtime metrics](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L92-L140). Screenshot: [Project-HAMi/website docs, userguide/hami-webui-user-guide.md#L45](https://github.com/Project-HAMi/website/blob/181dbd0e830b8ca190f6170284f3238c3597732d/docs/userguide/hami-webui-user-guide.md#L45), CC BY 4.0, live cluster not independently verified by this audit.
:::

---

<!--
HAMi monitor is NVIDIA-specific; the existence of scheduler backends does not make this collector hardware-neutral. Shared-memory accounting and NVML process correlation need validation for the chosen sharing mode.
-->

## NVIDIA has the clearest in-repository runtime path

::: grid {cols=2}
::: card {tag=green}
### Physical device
NVML supplies used memory, GPU activity, memory-controller activity, temperature, power and ECC.
:::
::: card {tag=cyan}
### Shared workload
HAMi-core accounting supplies container memory and activity. Metrics carry namespace, pod, container and device UUID.
:::
:::

::: notes
Source: [runtime metric contract](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L53-L140); [NVML collection](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L264-L278)
:::

---

<!--
This replaces the unsupported universal-sensor claim. No per-vendor exporter is required for the scheduler allocation families themselves. Cross-vendor measured consumption still requires vendor-capable runtime collection; that collector can be integrated rather than a separately deployed exporter. Intel is not in the audited parity claims.
-->

## A common view has explicit coverage

::: grid {cols=2}
::: card {tag=green}
### NVIDIA
Scheduler accounting plus NVML/shared-runtime collector code. Sharing mode still matters.
:::
::: card {tag=yellow}
### Ascend
Mode-gated tenant memory collector. vNPU tenant activity repeats card activity; WebUI task gap remains.
:::
::: card {tag=yellow}
### AMD
Allocation and plugin-health integration; first-party tenant runtime parity is not established.
:::
::: card {tag=red}
### Other accelerators
Require a compatible backend and telemetry adapter. A device plugin alone is insufficient.
:::
:::

::: notes
Source: [scheduler capacity](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L157-L200); [provider adapters](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/exporter.go#L605-L709); [Ascend tenant semantics](https://github.com/Project-HAMi/ascend-device-plugin/blob/6f6ee0240641e9f03e6e46356910a1579b3cf276/internal/monitor/collector.go#L124-L167)
:::

---

<!--
The deck describes source contracts, not inferred Prometheus naming conventions. Validate representative real samples before writing recording rules.
-->

## The same suffix can hide different units

- Runtime host GPU activity is described as **0-100**, despite `_ratio`.
- Scheduler memory-allocation ratio is explicitly **0-1**.
- Scheduler byte families convert internal **MiB to bytes**.
- WebUI physical memory families use **MiB**, not bytes.
- Normalize units at the boundary, before aggregation.

::: notes
Source: [0-100 contract](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L63-L72); [MiB conversion](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L116-L120); [0-1 contract](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L191-L195); [WebUI MiB](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/metrics.go#L68-L91)
:::

---

<!--
PORTABLE PATTERN, NOT A MEASURED RESULT. For the NVIDIA runtime families, max_over_time(hami_vgpu_memory_used_bytes[1h]) divided by hami_vgpu_memory_limit_bytes is an illustrative same-label use/limit ratio. The window is an example, not an operational recommendation. Validate scrape coverage, series uniqueness, Pod restarts and limits. Current limit differs from historical limits if reconfigured. Map workload reservations separately before saying allocation efficiency. Memory pressure needs consumption/limit, memory errors and/or allocator signals; reservations alone are not measured pressure.
-->

## Pattern 1: detect persistent overprovisioning

- Compare reserved memory with observed memory over a representative window.
- Require fresh, supported runtime data and a positive limit.
- Separate idle periods, model loading and steady-state demand.
- Rank sustained headroom alongside pending or rejected workloads.
- Treat low compute activity as a separate signal, not proof of reclaimable memory.

::: notes
Source: [tenant runtime metrics](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L92-L140); [workload allocations](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L389-L455)
:::

---

<!--
PORTABLE INVESTIGATION PATTERN, NOT A PROVEN CAUSAL DETECTOR. Start with hami_gpu_shared_count, workload/device allocation mapping, runtime memory/activity and application latency. Sharing count and scheduler annotations alone cannot prove contention. Ascend vNPU card-derived activity is insufficient for tenant compute attribution. MIG isolation boundaries change which resources can contend. DCGM and vendor tools can provide valuable workload and hardware data; do not claim this pattern is beyond them when enriched with Kubernetes state.
-->

## Pattern 2: investigate noisy-neighbor candidates

- Identify co-located tenants and the physical or slice identity they share.
- Correlate rising application latency with sibling activity and memory pressure.
- Check CPU, network, queueing and thermal throttling as alternatives.
- Repeat with controlled sibling load or isolated placement.
- Card-wide activity cannot identify which tenant caused contention.

::: notes
Source: [scheduler capacity](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L157-L200); [tenant runtime metrics](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L92-L140)
:::

---

<!--
PORTABLE PATTERN, NOT AN AUTOMATED HAMi RIGHT-SIZER. GPU memory is not inferred from activity. Percentiles alone can miss startup peaks and short out-of-memory events. On shared GPUs, activity may be measured against full device capacity rather than the reserved fraction; normalize explicitly. Changes can affect contention or application throughput. No fabricated improvement percentages or production case study are supplied.
-->

@layout image-right

## Pattern 3: right-size with workload evidence

- Measure startup peaks and steady-state demand across the workload lifecycle.
- Segment by model, batch size, request load and sharing mode.
- Choose memory headroom from peaks and failure risk.
- Tune compute limits only after normalizing quota and activity semantics.
- Canary the new request; compare latency, failures and placement outcomes.

![HAMi WebUI workload detail: gpu-burn Pod at Compute Power Limit 0.5, GPU Compute Utilization spiking past 100 on a 0-180 axis while Memory Utilization oscillates 10-90%](assets/hami/webui-workload-detail.png)

::: notes
Source: [tenant runtime metrics](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L92-L140); [scheduling outcome counters](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/pkg/metrics/scheduler.go#L29-L55). Screenshot: [Project-HAMi/website docs, userguide/hami-webui-user-guide.md#L57](https://github.com/Project-HAMi/website/blob/181dbd0e830b8ca190f6170284f3238c3597732d/docs/userguide/hami-webui-user-guide.md#L57), CC BY 4.0, live cluster not independently verified by this audit.
:::

---

<!--
PROPOSED DASHBOARD DESIGN. Allocation packing describes reservation density. Workload efficiency requires consumption and useful application output. Show capability/freshness alongside numbers and avoid equating 100 percent activity with useful computation. Panels are not claimed as deployed or demonstrated.
-->

## The operator view joins intent, activity and outcome

::: grid {cols=2}
::: card {tag=cyan}
### Allocation
Reserved/total memory, sharing count, placement failures and pending demand.
:::
::: card {tag=green}
### Runtime
Consumption/limit, scoped activity, memory errors and freshness.
:::
::: card {tag=yellow}
### Application
Latency, throughput, queue depth and error rate, by stable workload identity.
:::
::: card {tag=red}
### Confidence
Measured or derived? Supported on this vendor/mode? Current or stale?
:::
:::

---

<!--
REFERENCE ARCHITECTURE, NOT AN EXISTING HAMi OTLP INTEGRATION. OpenTelemetry Collector contrib has a Prometheus receiver; deployment/component versions, enrichment and target discovery must be validated. The proposed architecture preserves vendor/runtime sources and adds intent correlation. Existing metric units do not automatically conform to OTel semantic conventions. Do not claim one Prometheus receiver somehow removes hardware-specific sensors.
-->

## OpenTelemetry can carry the combined model

::: grid {cols=2}
::: card {tag=cyan}
### Existing inputs
HAMi Prometheus allocation metrics plus compatible runtime metrics.
:::
::: card {tag=green}
### Collector pipeline
A Prometheus receiver can scrape, enrich and export metrics through OTLP.
:::
::: card {tag=yellow}
### Additional instrumentation
Proposed spans/events for admission, allocation and bind decisions.
:::
::: card {tag=cyan}
### Common attributes
Workload identity, device/slice identity, scope, unit, source and freshness.
:::
:::

::: notes
Source: [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/); [Prometheus receiver](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/prometheusreceiver)
:::

---

<!--
PROPOSED INSTRUMENTATION. Do not invent current HAMi admission latency histograms, GPU execution spans or trace-context propagation. Existing bounded outcome counters do not carry per-Pod trace correlation. Pod UID can be available at later lifecycle stages; a CREATE admission request may precede stable Pod UID assignment. Use admission request identity initially and reconcile once the object exists. Cardinality/security budgets need explicit design. The scheduler does not intercept CUDA calls.
-->

## Admission telemetry records intent, not GPU work

- Record requested resources, policy decisions and rejection reasons.
- Emit separate scheduler events for reservation, no-fit and bind rollback.
- Correlate runtime and application signals after the workload starts.
- Use stable workload/device identity; avoid PID and request-level metric labels.
- Proposed `hami.*` attributes are custom, not standard OTel conventions.

::: notes
Source: [scheduling outcome counters](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/pkg/metrics/scheduler.go#L29-L55)
:::

---

<!--
PROPOSAL: this is a recommended normalization contract, not an implemented universal HAMi API. Preserve raw vendor metrics and document conversions.
-->

## A cross-platform contract we should build

::: grid {cols=2}
::: card {tag=cyan}
### Stable identity
Cluster, node, vendor, physical device, slice, workload UID and container.
:::
::: card {tag=green}
### Explicit semantics
Reservation vs consumption; bytes vs MiB; ratio vs percent; physical vs slice vs tenant.
:::
::: card {tag=yellow}
### Capability and freshness
Measured, derived, unsupported or stale. Export the collection timestamp and error state.
:::
::: card {tag=red}
### Bounded cost
Avoid PID-level history by default. Control label churn and query fan-out.
:::
:::

---

<!--
PROPOSED TEST PLAN. No workload was deployed as part of this static inventory. Choose representative sharing modes and vendor-specific ground truth. Never present illustrative numbers as measurements.
-->

## Validation before a live cross-platform demo

- Reserve two workloads on one device; verify allocation identities.
- Drive one workload while the other is idle; inspect tenant attribution.
- Compare physical usage, slice usage and application latency.
- Stop the exporter; verify missing or stale does not become healthy zero.
- Restart a Pod; confirm old identity and time series expire correctly.

---

<!--
The user goals emphasize transferable architecture over a product pitch. Current implementation and proposals stay distinct. No production results or universal hardware support are asserted. Vendor telemetry can already expose many relevant signals; the contribution is the scheduling-intent/runtime/application correlation and the explicit capability contract. Speaker Bio was empty in the supplied brief; existing speaker attribution is retained without inventing biography.
-->

## Take away a workload-centric observability model

- Scheduling supplies ownership, intent and allocation decisions.
- Runtime sensors supply consumption and device behavior.
- Their correlation enables overprovisioning and contention investigations.
- OpenTelemetry can transport the model and decision events.
- The pattern applies to other schedulers and device integrations.

---

# Appendix: Source-backed platform inventory

@subtitle Collector details, integration gaps and scrape contracts

---

<!--
The Ascend plugin exposes /metrics only in HAMivNPUCore or ENPU modes. vNPUCore has tenant memory accounting, but its tenant utilization repeats physical AICore activity. Context/module/buffer values are zero placeholders. WebUI's task metric adapters explicitly return unsupported even though the plugin emits some task memory series. This is an integration gap, not absence of all Ascend observability.
-->
## Ascend: exporter support depends on mode

- HAMivNPUCore and ENPU modes expose `:9395/metrics`.
- Tenant memory comes from shared accounting or DCMI process attribution.
- vNPU tenant utilization repeats **physical AICore activity**.
- Context/module/buffer memory fields are zero placeholders.
- WebUI physical NPU adapters exist; task adapters remain unsupported.

::: notes
Source: [mode gate](https://github.com/Project-HAMi/ascend-device-plugin/blob/6f6ee0240641e9f03e6e46356910a1579b3cf276/cmd/main.go#L154-L165); [tenant semantics](https://github.com/Project-HAMi/ascend-device-plugin/blob/6f6ee0240641e9f03e6e46356910a1579b3cf276/internal/monitor/collector.go#L124-L167); [WebUI gap](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/exporter.go#L687-L709)
:::

---

<!--
The audited dcu-exporter emits vdcu_utilizationrate and vdcu_usedmemory_bytes with PodResources workload labels. WebUI's DCU workload queries instead expect vdcu_percent and vdcu_usage_memory_size with pod_uuid/container_name. These contracts do not match at the pinned versions. Physical telemetry queries align more closely. New HCU adapters are separate and their exporter is outside this organization inventory.
-->
## Hygon: physical exporter, workload contract mismatch

- DCU exporter serves `/metrics` on default port **16080**.
- Physical and virtual gauges poll DCGM every **10 seconds**.
- Exporter: `vdcu_utilizationrate`, `vdcu_usedmemory_bytes`.
- WebUI expects `vdcu_percent`, `vdcu_usage_memory_size` and different labels.
- Validate or bridge the workload contract before demoing WebUI trends.

::: notes
Source: [exported virtual families](https://github.com/Project-HAMi/dcu-exporter/blob/30408d074cd420729f5698710d54fb30abefb0b1/main.go#L144-L177); [polling and endpoint](https://github.com/Project-HAMi/dcu-exporter/blob/30408d074cd420729f5698710d54fb30abefb0b1/main.go#L405-L471); [compute query](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/exporter.go#L696-L701); [memory query](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/exporter.go#L791-L811)
:::

---

<!--
Negative findings are scoped to audited first-party code. They do not mean vendor monitoring software does not exist. See the vendor report for exact health paths and source evidence.
-->

## AMD and Biren: scheduling does not prove metric parity

::: grid {cols=2}
::: card {tag=yellow}
### AMD
ROCm/AMD plugin health integration exists. Scheduler reservations are visible. No AMD-specific WebUI telemetry adapter in the reviewed switch.
:::
::: card {tag=red}
### Biren
Device registration, allocation and health logic need a separate exporter contract. No Biren WebUI telemetry branch in the reviewed switch.
:::
:::

::: notes
Source: [AMD accounting](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/scheduler/metrics.go#L64-L74); [implemented provider branches](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/exporter.go#L605-L684)
:::

---

<!--
Adapters exist, but the first-party Project-HAMi organization snapshot does not contain every vendor exporter. Cambricon and some other legacy task paths retain a card-utilization fallback, which must not be described as direct per-container measurement.
-->

## Cambricon and MetaX use external metric contracts

::: grid {cols=2}
::: card {tag=cyan}
### Cambricon
WebUI queries `mlu_*` series and joins container mapping on UUID. Workload attribution inherits exporter semantics.
:::
::: card {tag=green}
### MetaX
WebUI queries `mx_*` physical and workload series. GPU and sGPU paths have different identity labels and assumptions.
:::
:::

::: notes
Source: [provider queries](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/exporter.go#L687-L709); [conversion and fallback](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/exporter.go#L744-L788); [workload memory](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/exporter.go#L791-L811)
:::

---

<!--
The documentation report lists documented vendors and the corresponding source paths. No universal exporter or per-tenant metric contract is inferred from a resource-name entry.
-->

## Other scheduling backends remain evidence gaps

- HAMi documents more hardware than WebUI has telemetry adapters.
- Iluvatar, Enflame, Kunlunxin, Mthreads and other backends need exporter-by-exporter review.
- Check physical health, runtime usage and workload attribution independently.
- Label an unverified capability **unknown**, not zero or supported.

---

<!--
NVIDIA and HCU task activity conversions explicitly exclude elastic borrowing; other vendor paths differ. Physical-card activity must not substitute for an individual tenant on a shared card.
-->

## WebUI is a normalization layer with boundaries

- Uses Kubernetes allocation state plus Prometheus vendor queries.
- Re-exports common `hami_memory_*`, `hami_core_*` and container families.
- Marks unknown core allocation instead of manufacturing capacity.
- Exposes refresh health and last-success timestamp.
- Common names do not guarantee common measurement semantics.

::: notes
Source: [refresh health](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/metrics.go#L44-L49); [known/unknown and usage](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/metrics.go#L163-L180); [semantics](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/exporter.go#L744-L788)
:::

---

<!--
HAMi-DRA implements an optional allocation monitor on :8080/metrics. It watches ResourceSlices and ResourceClaims and reports consumed capacity, not actual hardware use. Its current core ratio families are normalized 0-1, unlike classic HAMi percentage-style core accounting. The NVIDIA kubelet DRA driver handles device health through logs/ResourceSlice changes; this is not a GPU Prometheus exporter.
-->
## DRA has a distinct allocation monitor

- HAMi-DRA serves allocation metrics at `:8080/metrics`.
- Capacity comes from ResourceSlices; reservations from ResourceClaims.
- Current families use `hami_dra_*` names and core ratios **0-1**.
- Kubelet-driver health and Prepare/Unprepare are a separate surface.
- Runtime device and tenant telemetry still require their own collectors.

::: notes
Source: [DRA descriptors](https://github.com/Project-HAMi/HAMi-DRA/blob/ab103e2f93d743e8140bf4431437dc86b7718a22/pkg/metrics/metrics.go#L21-L52); [normalization](https://github.com/Project-HAMi/HAMi-DRA/blob/ab103e2f93d743e8140bf4431437dc86b7718a22/pkg/metrics/collector.go#L27-L116); [endpoint setup](https://github.com/Project-HAMi/HAMi-DRA/blob/ab103e2f93d743e8140bf4431437dc86b7718a22/docs/MONITOR.md#L1-L67)
:::

---

<!--
These are checked-in template conditions, not a claim that Prometheus Operator is installed in any cluster. Confirm effective release values and ServiceMonitor selector matching.
-->

## Scrape configuration is part of the contract

- HAMi provides separate scheduler and runtime ServiceMonitors.
- Chart rendering requires the ServiceMonitor CRD and `prometheus.enabled`.
- Runtime monitor also requires the device plugin to be enabled.
- Both templates set `honorLabels: true`.
- Verify target selection, labels and actual series after installation.

::: notes
Source: [scheduler scrape](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/charts/hami/templates/scheduler/servicemonitor.yaml#L1-L23); [runtime scrape](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/charts/hami/templates/device-plugin/servicemonitor.yaml#L1-L23)
:::

---

<!--
Review the documentation report for legacy dashboard references. A successful HTTP scrape does not prove the query expected by a panel returns data.
-->

## Version skew can silently break dashboards

- Current `hami_*` names coexist with opt-in legacy descriptors.
- Names and labels changed together: `deviceuuid` versus `device_uuid`.
- Some older guides expect legacy families; current Grafana JSON uses `hami_*`.
- Pin exporter, scheduler, WebUI and dashboard versions together.
- Test missing series as well as successful queries.

::: notes
Source: [legacy runtime descriptors](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L142-L194); [current NVIDIA selector](https://github.com/Project-HAMi/HAMi-WebUI/blob/846c0e2d3360cc7240bb61968e4cc7e3cea53443/server/internal/exporter/exporter.go#L713-L715)
:::
