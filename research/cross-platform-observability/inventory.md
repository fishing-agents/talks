# HAMi cross-platform observability inventory

Audit date: 2026-09-30. All 23 public Project-HAMi organization repositories were checked against the live GitHub listing and reviewed at the pinned local commits in [repositories.json](repositories.json). This is a static implementation/documentation inventory, not a live cluster, vendor hardware, or scrape validation. Existing checkouts were not pulled, reset or modified.

## Findings that shape the talk

- Scheduler reservations, physical device telemetry, tenant attribution and application service-level signals are distinct planes.
- NVIDIA has an in-repository NVML/shared-cache path; KAI and Volcano ports have their own versions and schemas.
- Ascend has mode-gated exporters and tenant memory visibility, but vNPU tenant utilization copies card activity. WebUI task adapters remain unsupported.
- Hygon has physical/virtual collectors, but checked-in DCU workload metric names/labels do not match WebUI expectations.
- AMD/Biren plugin integration and broad hardware scheduling support do not prove common runtime dashboard coverage.
- Classic HAMi, HAMi-DRA and WebUI metric vocabularies/units differ. Explicit unit and identity mapping is mandatory.
- Missing data, unsupported capabilities and stale caches must not be represented as healthy zero.

## Detailed evidence

- [Metric-level observer inventory](observers.md): per-component metric tables, labels, units, failure semantics.
- [Question for the HAMi team: per-tenant usage on shared AMD GPUs](hami-team-amd-tenant-telemetry.md): why AMD has no vGPUmonitor equivalent, evidence and options.
- [NVIDIA, scheduler, DRA, KAI, Volcano and mock audit](observability-nvidia-control.md)
- [AMD, Ascend, Biren and Hygon audit](observability-vendors.md)
- [Documentation, Grafana, WebUI, tutorials and workload audit](observability-docs-ui.md)
- [Repository/version manifest](repositories.json)
- [Tracked-file discovery index](search-index.json): keyword evidence, not a capability proof.
- [Metric descriptor discovery index](metric-descriptor-index.json): candidate names, not guaranteed emitted series.

## Repository-by-repository inventory

### .project

- Role: Project metadata.
- Findings: No exporter or runtime observability contract; CNCF project/governance metadata only.
- Archive status: not archived at audit time.
- Snapshot: [bc3fc9a5f707](https://github.com/Project-HAMi/.project/tree/bc3fc9a5f70755838f17c9e4f29090a677e6c8e7).
- Source-linked detail: [observability-docs-ui.md](observability-docs-ui.md).

### ai-benchmark

- Role: Application benchmarking.
- Findings: TensorFlow model benchmark timing and result output, not a Prometheus telemetry pipeline. Kubernetes GPU request examples do not establish tenant infrastructure metrics.
- Archive status: not archived at audit time.
- Snapshot: [388fc4d9a9b2](https://github.com/Project-HAMi/ai-benchmark/tree/388fc4d9a9b2c69ab3205fcf6507a1d2b43c807e).
- Source-linked detail: [observability-docs-ui.md](observability-docs-ui.md).

### amd-device-plugin

- Role: Device inventory and health.
- Findings: AMD SMI provides identity; optional AMD Device Metrics Exporter health client uses a Unix gRPC socket. No first-party Prometheus exporter. External schema and tenant attribution need validation.
- Archive status: not archived at audit time.
- Snapshot: [9a3e617def1f](https://github.com/Project-HAMi/amd-device-plugin/tree/9a3e617def1f0a22d023e1cc2a5398ebd9283a5f).
- Source-linked detail: [observability-vendors.md](observability-vendors.md).

### amd-hami-core

- Role: In-container enforcement.
- Findings: HIP interception and memory/CU enforcement with logs; no standalone metrics endpoint or published tenant telemetry schema.
- Archive status: not archived at audit time.
- Snapshot: [050cd7341dfe](https://github.com/Project-HAMi/amd-hami-core/tree/050cd7341dfe447483f087494fd0259eacd2006e).
- Source-linked detail: [observability-vendors.md](observability-vendors.md).

### ascend-device-plugin

- Role: Physical and tenant collector, mode-gated.
- Findings: HAMivNPUCore and ENPU enable :9395/metrics. Tenant memory accounting exists. vNPU tenant utilization copies physical AICore activity; context/module/buffer fields are zero placeholders. ENPU adds collection-success gauges and process/cgroup memory attribution.
- Archive status: not archived at audit time.
- Snapshot: [6f6ee0240641](https://github.com/Project-HAMi/ascend-device-plugin/tree/6f6ee0240641e9f03e6e46356910a1579b3cf276).
- Source-linked detail: [observability-vendors.md](observability-vendors.md).

### ascend-dra-driver

- Role: DRA capacity, allocation and health.
- Findings: Publishes resource capacity and claim lifecycle; optional gRPC health check disabled by default. No first-party metrics exporter found in inspected driver/chart code. Runtime core shared memory is not automatically scraped.
- Archive status: not archived at audit time.
- Snapshot: [91d82a2884b9](https://github.com/Project-HAMi/ascend-dra-driver/tree/91d82a2884b9a982cfb1844dd69dd62516d5f323).
- Source-linked detail: [observability-vendors.md](observability-vendors.md).

### biren-device-plugin

- Role: Inventory, allocation and health.
- Findings: Registers devices and HAMi node annotations; logs heartbeat/allocation and advertises device health. No first-party runtime/tenant exporter found.
- Archive status: not archived at audit time.
- Snapshot: [f0a83df3b681](https://github.com/Project-HAMi/biren-device-plugin/tree/f0a83df3b681bc3aac795eafb2232ee966c4a2dd).
- Source-linked detail: [observability-vendors.md](observability-vendors.md).

### community

- Role: Reference talks and governance.
- Findings: Talk archive and adoption narratives, not reproducible exporter/query contracts. Presentation claims were not used as proof of telemetry parity.
- Archive status: not archived at audit time.
- Snapshot: [769b5c4ff6f1](https://github.com/Project-HAMi/community/tree/769b5c4ff6f18c2abc4d7fc172796907d8c5e6fe).
- Source-linked detail: [observability-docs-ui.md](observability-docs-ui.md).

### dcu-dcgm

- Role: Vendor management/telemetry library.
- Findings: HY-DMI/ROCm-SMI bindings plus JSON HTTP API on default 16081. Physical/virtual device data, processes and events available through API; no native Prometheus exporter.
- Archive status: not archived at audit time.
- Snapshot: [e8fdd4be5e29](https://github.com/Project-HAMi/dcu-dcgm/tree/e8fdd4be5e29b5cfc5133707c7e3da24479934bb).
- Source-linked detail: [observability-vendors.md](observability-vendors.md).

### dcu-exporter

- Role: Physical and virtual exporter.
- Findings: Default :16080/metrics; polls every 10 seconds. dcu_* and vdcu_* gauge families, workload mapping via PodResources and /etc/vdev. Virtual names/labels differ from WebUI expected DCU workload queries. Several raw units and collection-failure states lack explicit contracts.
- Archive status: not archived at audit time.
- Snapshot: [30408d074cd4](https://github.com/Project-HAMi/dcu-exporter/tree/30408d074cd420729f5698710d54fb30abefb0b1).
- Source-linked detail: [observability-vendors.md](observability-vendors.md).

### dcu-vgpu-device-plugin

- Role: Archived allocator integration.
- Findings: Uses DCGM inventory and vGPU config files; no standalone metrics endpoint. Separate dcu-exporter is the collector. Archived snapshot must not be described as a current maintenance commitment.
- Archive status: archived at audit time.
- Snapshot: [30f2edfd2969](https://github.com/Project-HAMi/dcu-vgpu-device-plugin/tree/30f2edfd2969d0e9ddd3bddec21bfcf75b2201f9).
- Source-linked detail: [observability-vendors.md](observability-vendors.md).

### HAMi

- Role: Scheduler accounting plus NVIDIA runtime monitor.
- Findings: Scheduler :9395/metrics exposes allocation, quota, sharing, leader/cache and outcome metrics. NVIDIA monitor :9394/metrics uses NVML and HAMi-core shared cache. Separate ServiceMonitors are conditional on Operator CRD and chart settings. Host utilization is 0-100 despite _ratio; memory-allocation ratio is 0-1.
- Archive status: not archived at audit time.
- Snapshot: [39699df26042](https://github.com/Project-HAMi/HAMi/tree/39699df26042b3e5062a76e00b3e4f74b72ad503).
- Source-linked detail: [observability-nvidia-control.md](observability-nvidia-control.md).

### HAMi-core

- Role: CUDA runtime accounting producer.
- Findings: Writes mmap-shared usage.cache for memory/activity and process identity; logs enforcement and cache failures. No own Prometheus endpoint. Correct workload metrics require a compatible consumer, mounts and Pod identity joins.
- Archive status: not archived at audit time.
- Snapshot: [ec5d85a3d709](https://github.com/Project-HAMi/HAMi-core/tree/ec5d85a3d709e5ed138a1668ebfefd366c05ca1e).
- Source-linked detail: [observability-nvidia-control.md](observability-nvidia-control.md).

### hami-demo

- Role: NVIDIA workload demonstration.
- Findings: nvidia-smi and API checks plus a Kubernetes-inventory Plotly visualization with A100 assumptions. Not a Prometheus telemetry/dashboard reference. No vendor-neutral service-level metric contract established.
- Archive status: not archived at audit time.
- Snapshot: [814c3e81b2ba](https://github.com/Project-HAMi/hami-demo/tree/814c3e81b2ba03225dd16c3abc68a26dfc86ed34).
- Source-linked detail: [observability-docs-ui.md](observability-docs-ui.md).

### HAMi-DRA

- Role: DRA allocation monitor.
- Findings: Optional :8080/metrics, health on :8000. hami_dra_* families report ResourceSlice capacity and ResourceClaim consumed allocations; core ratios are 0-1. This is API accounting, not hardware use. No chart ServiceMonitor found.
- Archive status: not archived at audit time.
- Snapshot: [ab103e2f93d7](https://github.com/Project-HAMi/HAMi-DRA/tree/ab103e2f93d743e8140bf4431437dc86b7718a22).
- Source-linked detail: [observability-nvidia-control.md](observability-nvidia-control.md).

### hami-vnpu-core

- Role: Ascend accounting producer.
- Findings: Rust runtime interception writes per-process/device HBM and memory quota shared state. No own exporter; Ascend device plugin consumes it when configured compatibly.
- Archive status: not archived at audit time.
- Snapshot: [962cb4867ee5](https://github.com/Project-HAMi/hami-vnpu-core/tree/962cb4867ee543ab0357ed90f4c27ae18d5d2198).
- Source-linked detail: [observability-vendors.md](observability-vendors.md).

### HAMi-WebUI

- Role: Query, normalization, cache and dashboards.
- Findings: Joins Kubernetes allocation state with external vendor Prometheus series and exposes its own common hami_* families. NVIDIA, Ascend, Cambricon, Hygon and MetaX adapters differ. Ascend task adapters explicitly unsupported; DCU workload schema mismatch; some legacy provider paths retain physical-card fallback. Refresh health, coverage, unknown allocation and absent-data handling exist.
- Archive status: not archived at audit time.
- Snapshot: [846c0e2d3360](https://github.com/Project-HAMi/HAMi-WebUI/tree/846c0e2d3360cc7240bb61968e4cc7e3cea53443).
- Source-linked detail: [observability-docs-ui.md](observability-docs-ui.md).

### hami-workshop

- Role: Archived installation/tutorial material.
- Findings: Prometheus + NVIDIA DCGM + WebUI architecture and installation material. Monitoring goals are broader than concrete query/catalog examples in inspected English pages. Archived; do not treat as universal vendor contract.
- Archive status: archived at audit time.
- Snapshot: [c7da062f5e57](https://github.com/Project-HAMi/hami-workshop/tree/c7da062f5e57f7a249b13d8c39621d21337728b7).
- Source-linked detail: [observability-docs-ui.md](observability-docs-ui.md).

### k8s-dra-driver

- Role: NVIDIA DRA node lifecycle and health.
- Findings: NVML XID health observation, logs, optional gRPC health and ResourceSlice updates. No first-party Prometheus GPU telemetry endpoint found. Health publication failures can leave stale API state; recovery requires attention.
- Archive status: not archived at audit time.
- Snapshot: [ddca6be79a96](https://github.com/Project-HAMi/k8s-dra-driver/tree/ddca6be79a96dcab684b8f4617a3360c5fb23679).
- Source-linked detail: [observability-nvidia-control.md](observability-nvidia-control.md).

### KAI-resource-isolator

- Role: Optional NVIDIA runtime monitor.
- Findings: Ported HAMi monitor at default :9394/metrics uses NVML and shared cache. ServiceMonitor optional and off by default. hami_* families and opt-in legacy aliases; cache/identity compatibility required. Not KAI scheduler allocation truth.
- Archive status: not archived at audit time.
- Snapshot: [09c0bb90b360](https://github.com/Project-HAMi/KAI-resource-isolator/tree/09c0bb90b360503ac3ec5ca987d07fcae852ae0a).
- Source-linked detail: [observability-nvidia-control.md](observability-nvidia-control.md).

### mock-device-plugin

- Role: Test device-registration fixture.
- Findings: Synthetic device count, health and Allocate gRPC behavior, ordinary logs. No GPU telemetry exporter, physical runtime measurements or tenant usage.
- Archive status: not archived at audit time.
- Snapshot: [8be1424ec2e9](https://github.com/Project-HAMi/mock-device-plugin/tree/8be1424ec2e953cf07b08d6cb4c46127da5d50ff).
- Source-linked detail: [observability-nvidia-control.md](observability-nvidia-control.md).

### volcano-vgpu-device-plugin

- Role: Legacy NVIDIA runtime monitor.
- Findings: NVML/shared-cache monitor uses legacy metric names. Validate collector registration and runtime scraping. Volcano scheduler implementation is external to this repository; do not attribute its control-plane metrics to this plugin.
- Archive status: not archived at audit time.
- Snapshot: [6063efe9806e](https://github.com/Project-HAMi/volcano-vgpu-device-plugin/tree/6063efe9806ee7bd2fd966fc65f155c65c95696b).
- Source-linked detail: [observability-nvidia-control.md](observability-nvidia-control.md).

### website

- Role: Documentation, Grafana JSON and tutorials.
- Findings: Current Grafana JSON uses classic HAMi hami_* and optional NVIDIA DCGM, not automatic DRA parity. Separate allocation/runtime tables and vendor support matrix. Stale utilization design page and generic kubelet scraping wording conflict with dedicated guidance.
- Archive status: not archived at audit time.
- Snapshot: [181dbd0e830b](https://github.com/Project-HAMi/website/tree/181dbd0e830b8ca190f6170284f3238c3597732d).
- Source-linked detail: [observability-docs-ui.md](observability-docs-ui.md).

## Cross-platform capability summary

- NVIDIA: scheduler accounting and host/tenant collector code; optional external DCGM hardware panels. Validate soft-sharing/MIG behavior independently.
- Ascend: plugin host/tenant memory collector in enabled modes; tenant compute attribution is not demonstrated by the card-derived series. Legacy modes and DRA have different surfaces. External npu_chip_info_* is a separate WebUI physical contract.
- Hygon DCU: dcu_* physical and vdcu_* virtual exporter code; identity and WebUI workload compatibility gaps. HCU query adapters exist in WebUI, but HCU exporter is outside this organization inventory.
- AMD: scheduler accounting, SMI identity and external exporter health integration; no first-party tenant Prometheus path established.
- Biren: registration/capacity and health state; no first-party runtime exporter established.
- Cambricon/MetaX: WebUI has external exporter query adapters with vendor-specific units, labels and task semantics. External exporters themselves are outside this inventory.
- Iluvatar, Enflame, Kunlunxin, Mthreads, Vastai, AWS Neuron and Teco: documented scheduling/support status must not be presented as common metric parity. Exporter and tenant contracts remain unverified here.

## Known integration and documentation discrepancies

1. DCU exporter emits vdcu_utilizationrate/vdcu_usedmemory_bytes with dcu_pod_* labels; WebUI requests vdcu_percent/vdcu_usage_memory_size with pod_uuid/container_name.
2. Ascend plugin emits tenant memory families; WebUI's Ascend task compute/memory functions return errWorkloadTelemetryUnsupported.
3. Classic HAMi core/host _ratio families may be 0-100; DRA core _ratio is 0-1. WebUI memory uses MiB whereas many collector families use bytes.
4. Current website Grafana JSON uses classic hami_* families. DRA monitor has hami_dra_* and opt-in legacy names; importing the same dashboard is not evidence of DRA coverage.
5. Website utilization-design wording and broad kubelet-scraping wording lag more specific implementation/documentation.
6. Shared-cache initialization, ABI, permissions, mount paths and Pod/device identity are observability dependencies, not incidental setup details.

## Proposed validation work, not executed

For each vendor and sharing mode, record collector/driver versions and actual /metrics samples. Run two tenants on one device, drive one and idle the other, verify workload attribution against vendor ground truth. Reconcile reservations, memory consumption, physical activity and application latency without assuming equality. Test exporter failure, unsupported fields, missing series, stale cache, Pod restart and identity reuse. Bound time-series cardinality and verify scrape label collisions/replica aggregation. Do not use fabricated metric samples or tutorial screenshots as production measurement evidence.

## Slide deck and reproduction

The deck is [hami_cross_platform_observability.md](../../hami_cross_platform_observability.md). Style reference: snow_corp_cncf.md (kubecon_japan theme, dual branding, title/part dividers, cards, fade transitions); SNOW-specific branding and claims are excluded.

From the talks repository:

```bash
uv run --no-project --with-editable ./slidr python -m slidr --pdf --dist hami_cross_platform_observability.md
uv run --no-project --with-editable ./slidr --with pypdf python research/cross-platform-observability/verify.py
python3 research/cross-platform-observability/scan.py
```

Generated HTML/PDF/ZIP live in dist/ (git-ignored). Verification checks repository coverage, commit-pinned source paths/line anchors, one heading per slide, HTML/PDF page counts and nonblank PDF pages. Browser layout checks supplement this but do not validate live observability integrations.
