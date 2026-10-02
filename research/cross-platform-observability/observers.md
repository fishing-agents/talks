# HAMi observer inventory: what each component measures

Audit date: 2026-10-02. Metric-level companion to [inventory.md](inventory.md). It covers every component in the Project-HAMi checkouts under `references/` that exports, consumes or writes observability data. All paths are relative to `references/`. This is a static source read, not a scrape of a live cluster.

Snapshot: every repository is at its [repositories.json](repositories.json) pin except `HAMi` (`eb46ae6b4b8c`, one commit after pin `39699df26042`) and `website` (`64e9121be4c5`). The HAMi delta touches only chart helpers, the NVIDIA DaemonSet, the runtime class and the device ConfigMap. `cmd/vGPUmonitor`, `cmd/scheduler/metrics.go`, `pkg/metrics`, `pkg/monitor` and both ServiceMonitor templates are byte-identical to the pin, so the deck's pinned line anchors stay valid. The website delta is only `package.json`/lockfile.

## Observer map

|Observer|Repo / binary|Endpoint|Enabled by|Data source|Plane|
|---|---|---|---|---|---|
|vGPUmonitor|HAMi `cmd/vGPUmonitor`|`:9394/metrics`|NVIDIA device-plugin DaemonSet sidecar; ServiceMonitor needs `prometheus.enabled` + `devicePlugin.enabled` + CRD|NVML (host) + HAMi-core mmap cache (tenant) + Pod informer + MIG annotations|physical + tenant|
|scheduler collector|HAMi `cmd/scheduler`|`:9395/metrics`|always; ServiceMonitor needs `prometheus.enabled` + CRD|scheduler in-memory node/pod/quota cache (from annotations)|reservation + control-plane|
|kai-vgpu-monitor|KAI-resource-isolator `cmd/monitor`|`:9394/metrics`, `/healthz`|`monitor.enabled` (default false); ServiceMonitor `monitor.serviceMonitor.enabled` (default false)|NVML + HAMi-core cache|physical + tenant|
|vgpu-monitor|volcano-vgpu-device-plugin `cmd/vgpu-monitor`|`:9394/metrics` (hardcoded)|`monitor.enabled` (default true); no Service, no ServiceMonitor|NVML + HAMi-core cache|physical + tenant|
|HAMi-DRA monitor|HAMi-DRA `cmd/monitor`|`:8080/metrics`, `:8000/healthz,/readyz`|`monitor.enabled` (default true); no ServiceMonitor|ResourceSlice + ResourceClaim informers|reservation|
|Ascend vNPU collector|ascend-device-plugin `internal/monitor`|`:9395/metrics`|`hamiVnpuCore` or `enpu` node/global config; otherwise no server|DCMI + hami-vnpu-core shmem (core mode) / ENPU config + DCMI process memory + cgroups (ENPU mode)|physical + tenant|
|dcu-exporter|dcu-exporter `main.go`|`:16080/metrics`|always (standalone)|rocm-smi / HY-DMI via in-process `dcu-dcgm/pkg/dcgm`, kubelet PodResources, `/etc/vdev`|physical + virtual|
|dcu-dcgm API|dcu-dcgm `pkg/service`|`:16081` JSON (no `/metrics`)|separate process|rocm-smi / HY-DMI live per request|physical + virtual (pull API)|
|WebUI exporter|HAMi-WebUI `server/internal/exporter`|WebUI HTTP `/metrics`|always; 30 s refresh|Kubernetes/HAMi annotations + PromQL against external Prometheus|normalized re-export|
|Health-only|amd-device-plugin, biren-device-plugin, mock-device-plugin, k8s-dra-driver, ascend-dra-driver, dcu-vgpu-device-plugin|none|-|kubelet `ListAndWatch` health, node annotations, ResourceSlice content, logs|health/inventory|
|Producers (no endpoint)|HAMi-core, amd-hami-core, hami-vnpu-core|-|LD_PRELOAD / LD_AUDIT / runtime hook|in-process interception writing shared memory + stderr|tenant accounting input|

## 1. HAMi vGPUmonitor (NVIDIA)

### Runtime contract

- Flags: `--metrics-bind-address` default `:9394`, `--legacy-metrics` default false (`HAMi/cmd/vGPUmonitor/main.go:65-66`). Chart value `legacyMetrics` sets both scheduler and monitor.
- Registry: custom `prometheus.NewRegistry()` with `hami_build_info` plus one `ClusterManagerCollector` wrapped with constant label `zone="vGPU"` (`main.go:159-164`, `metrics.go:730`). No `go_*`/`process_*` series.
- Collection is **pull-time**: every scrape runs `nvml.Init`/`Shutdown`, iterates devices, then reads the mmap'd caches directly (`metrics.go:240-282`). No sampling interval of its own; freshness depends on HAMi-core's writers.
- Pod scope: Pods listed by label `hami.io/vgpu-node=<NODE_NAME>` (`metrics.go:486`, `pkg/util/types.go:21`) from a `spec.nodeName`-scoped informer. Both init and regular containers are matched (`metrics.go:522-525`).
- Cache discovery: `{HAMI_VGPU_CACHE_ROOT or HOOK_PATH/containers}/{podUID}_{container}/*.cache` (`pkg/monitor/nvidia/cudevshr.go:137-140, 224-256, 338-347`). The rescan runs every 5 s in the feedback loop (`feedback.go:152-171`). Directories for Pods missing from the informer are kept for `HAMI_RESYNC_INTERVAL` (default 5 m) after their last mtime (`cudevshr.go:101-112, 231-237`).
- Cache format gate: magic `19920718`. Size ≥ v1 `MinSize` with major 1 selects v1; a smaller file selects v0; anything else is an error and the container is skipped (`cudevshr.go:375-390`). HAMi-core currently writes v1.2 (`HAMi-core/src/multiprocess/multiprocess_memory_limit.h:67-68`).

### Families emitted

All labels below also carry `zone="vGPU"`. Host labels H = `node, device_index, device_uuid, device_type`. Container labels C = `namespace, pod, container, vdevice_index, device_uuid`.

|Metric|Type|Labels|Unit|Source|Declared|
|---|---|---|---|---|---|
|`hami_host_gpu_memory_used_bytes`|gauge|H|bytes|NVML `GetMemoryInfo().Used`; skipped on `NOT_SUPPORTED` (unified memory)|`metrics.go:57-61`, emit `:382`|
|`hami_host_gpu_utilization_ratio`|gauge|H|**0-100**|NVML `GetUtilizationRates().Gpu` (whole device, driver sample window)|`:63-67`, emit `:403`|
|`hami_host_gpu_memory_controller_utilization_ratio`|gauge|H|**0-100**|NVML `GetUtilizationRates().Memory`|`:69-73`, emit `:409`|
|`hami_host_gpu_temperature_celsius`|gauge|H|°C|NVML `GetTemperature(GPU)`|`:75-79`, emit `:429`|
|`hami_host_gpu_power_usage_watts`|gauge|H|W (mW/1000)|NVML `GetPowerUsage`|`:81-85`, emit `:447`|
|`hami_host_gpu_ecc_errors_total`|counter|H + `error_type` (`corrected`/`uncorrected`)|count, lifetime aggregate|NVML `GetTotalEccErrors(AGGREGATE_ECC)`|`:87-91`, emit `:472`|
|`hami_vgpu_memory_used_bytes`|gauge|C|bytes|cache: Σ `procs[].used[dev].total` over active slots|`:92-96`, emit `:573`|
|`hami_vgpu_memory_limit_bytes`|gauge|C|bytes|cache: `limit[dev]` (from `CUDA_DEVICE_MEMORY_LIMIT[_N]`)|`:98-102`, emit `:579`|
|`hami_container_device_memory_bytes`|gauge|C|bytes|**same value** as `hami_vgpu_memory_used_bytes`|`:103-107`, emit `:585`|
|`hami_container_device_utilization_ratio`|gauge|C|0-100 per process, **summed**|cache: Σ `procs[].device_util[dev].sm_util`|`:108-112`, emit `:593`|
|`hami_container_last_kernel_elapsed_seconds`|gauge|C|seconds|`now - last_kernel_time`; emitted only if > 0 (v0 caches return 0, so never)|`:113-117`, emit `:612-619`|
|`hami_mig_device_info`|gauge (info = 1)|C + `mig_uuid, profile, gpu_instance_id, compute_instance_id`|1|Pod MIG allocation annotation, not NVML|`:118-122`, emit `:626-671`|
|`hami_vgpu_memory_context_bytes`|gauge|C|bytes|Σ `used[dev].context_size`|`:123-127`, emit `:599`|
|`hami_vgpu_memory_module_bytes`|gauge|C|bytes|Σ `used[dev].module_size`|`:129-133`, emit `:603`|
|`hami_vgpu_memory_buffer_bytes`|gauge|C|bytes|Σ `used[dev].data_size`|`:135-139`, emit `:607`|
|`hami_build_info`|gauge = 1|version labels|-|build metadata|`HAMi/pkg/metrics/metrics.go:30`|

Legacy aliases (only with `--legacy-metrics`, `metrics.go:154-195`): `HostGPUMemoryUsage`, `HostCoreUtilization`, `vGPU_device_memory_usage_in_bytes`, `vGPU_device_memory_limit_in_bytes`, `Device_memory_desc_of_container` (context/module/data/offset as **label values**), `Device_utilization_desc_of_container`, `Device_last_kernel_of_container`, `MigInfo`. Labels use `nodeid, deviceidx, deviceuuid, devicetype, podnamespace, podname, ctrname, vdeviceid`.

Not exported although present in the cache: `procs[].monitorused[dev]` (NVML per-process used memory written by HAMi-core), `dec_util`/`enc_util`, `sm_limit`, `priority`, `utilization_switch`, `recent_kernel`, process PIDs.

### Where the tenant numbers come from (HAMi-core producer)

- **Memory used** = HAMi-core's own allocation accounting: interception adds and removes bytes per process slot (`HAMi-core/src/multiprocess/multiprocess_memory_limit.h:70-95`). It is not the NVML process-memory figure. NVML per-process usage goes to `monitorused` (`multiprocess_utilization_watcher.c:245-251`), which the monitor does not export.
- **SM utilization** = per-process NVML `nvmlDeviceGetProcessUtilization` samples written by an in-container watcher thread every 120 ms (`multiprocess_utilization_watcher.c:232-262`, `multiprocess_utilization_watcher.h:14-17`). The thread starts only if some device has an SM limit in (0,100] (`:322-344`). The default limit is 100 when `CUDA_DEVICE_SM_LIMIT` is unset (`multiprocess_memory_limit.c:271-273`), so it runs whenever HAMi-core is loaded. The value is per-process share of the **whole device**, summed per container by the Go reader (`HAMi/pkg/monitor/nvidia/v1/spec.go:164-173`). It is not normalized to the container's core reservation.
- **Last kernel time** = written at most once per `RECORD_KERNEL_INTERVAL` on kernel launch (`multiprocess_memory_limit.c:302-323`).
- **Consistency**: HAMi-core added a per-slot `seqlock` (`multiprocess_memory_limit.h:93`). The Go v1 overlay keeps the same size by treating that word as `unused` (`spec.go:42-50`), so reads are not seqlock-consistent snapshots.

### Feedback (control, not telemetry)

Every 5 s, `Observe` (`feedback.go:79-143`) counts containers with recent kernels per device and priority. It then writes `recent_kernel = -1` (block) and `utilization_switch` back into each container's cache. This is how priority-based time sharing works. None of it is exported as a metric. A MIG apply lock file pauses the loop (`main.go:108-124`).

### Failure semantics

- NVML init or device failures: host series are **absent** and the error is logged (`metrics.go:244-247, 345-367`). `NOT_SUPPORTED` per family is skipped silently.
- `hami_container_device_utilization_ratio`/`hami_vgpu_memory_used_bytes` depend on the watcher resolving the container's host PID (`HAMi-core/src/utils.c:122-128`, `getextrapid`). If that lookup fails (`host pid is error!`), `set_host_pid` never runs and the process slot's `hostpid` stays 0 (`multiprocess_memory_limit.c:1186`), so `find_proc_by_hostpid` never matches it (`multiprocess_memory_limit.c:1641-1646`) and the slot's `sm_util`/`monitorused` are never written. The exported value is then 0 (or stale from before the failure) while the container can still be active: **zero does not mean idle**.
- An invalid or uninitialized UUID in the cache skips that device until the next scrape (`metrics.go:552-560`).
- There is no collection-success gauge, no last-update timestamp and no per-container freshness signal. A container whose process stopped writing keeps its last cached values until the directory is removed.

## 2. HAMi scheduler collector

- `:9395/metrics` (`HAMi/cmd/scheduler/main.go:75`). It is rebuilt per scrape from the scheduler's in-memory cache: node device annotations, scheduled-Pod annotations and ResourceQuotas. No hardware is touched. `zone="vGPU"` is on every family except `hami_build_info`.
- Units: internal MiB is converted to bytes by `mibToBytes` for every `_bytes` value. The `device_memory_limit` **label** on overview families stays in MiB. Core `_ratio` families are **0-100**. AMD is normalized to percent of compute units (`cmd/scheduler/metrics.go:64-74`); others pass raw `Usedcores`/`Totalcore` through. Only `hami_node_gpu_memory_allocated_ratio` is 0-1.

|Metric|Labels (+zone)|Unit|Meaning|Declared|
|---|---|---|---|---|
|`hami_gpu_memory_limit_bytes`|node, device_uuid, device_index, device_type|bytes|registered device memory|`metrics.go:161-165`|
|`hami_gpu_core_limit_ratio`|same|0-100|registered core capacity|`:166-170`|
|`hami_gpu_memory_allocated_bytes`|+ device_cores|bytes|reserved memory on device|`:171-175`|
|`hami_gpu_shared_count`|same|count|containers sharing device|`:176-180`|
|`hami_gpu_core_allocated_ratio`|same|0-100|reserved cores|`:181-185`|
|`hami_node_gpu_overview`|+ device_cores, device_memory_limit (MiB label)|bytes|reserved memory with capacity labels|`:186-190`|
|`hami_node_gpu_memory_allocated_ratio`|node, device_uuid, device_index, device_type|**0-1**|reserved/total memory; only if total > 0|`:191-195`|
|`hami_node_gpu_mig_instance_info`|+ mig_uuid, profile, gpu/compute_instance_id, placement_start/size|1|MIG instances in use (mode `mig`, RuntimeReady)|`:196-200`|
|`hami_resource_quota_used`|namespace, quota_name, limit|device units|quota consumption; `limit` value is a label|`:347-351`|
|`hami_resource_quota_limit`|namespace, quota_name|device units|only if limit set|`:352-356`|
|`hami_vgpu_memory_allocated_bytes`|namespace, node, pod, device_uuid|bytes|per Pod/device reservation, **no container label**|`:389-393`|
|`hami_vgpu_core_allocated_ratio`|namespace, node, pod, device_uuid|0-100|per Pod/device core reservation|`:394-398`|
|`hami_remote_gpu_memory_limit_bytes`, `hami_remote_gpu_allocated`, `hami_remote_gpu_overview`|server, endpoint, device_uuid, ...|bytes / 0-1 flag|remote-GPU pool, only if backend configured|`:473-487`|
|`hami_scheduler_is_leader`|-|0/1|leader election state|`:510-514`|
|`hami_scheduler_cache_synced`|-|0/1|informer cache synced|`:515-519`|
|`hami_scheduler_allocations_total`|phase, device_type, failure_reason|counter|successful **filter** allocations only; `failure_reason` always `none`|`HAMi/pkg/metrics/scheduler.go:52`|
|`hami_scheduler_allocation_failures_total`|same|counter|filter/bind failures; reasons `no_fit, lookup, identity, lock, annotation_patch, bind, internal`|`scheduler.go:53`|
|`hami_scheduler_bind_rollbacks_total`|same|counter|bind rollbacks|`scheduler.go:54`|

Legacy aliases (`--legacy-metrics`): `GPUDeviceMemoryLimit`, `GPUDeviceCoreLimit`, `GPUDeviceMemoryAllocated`, `GPUDeviceSharedNum`, `GPUDeviceCoreAllocated`, `nodeGPUOverview`, `nodeGPUMemoryPercentage` (0-1 despite the name), `nodeGPUMigInstance`, `QuotaUsed`, `vGPUMemoryAllocated`, `vGPUCoreAllocated` (`cmd/scheduler/metrics.go:214-253, 359-363, 407-416`). Legacy core values are never AMD-normalized.

ServiceMonitors (`charts/hami/templates/scheduler/servicemonitor.yaml`, `.../device-plugin/servicemonitor.yaml`): rendered only if the `monitoring.coreos.com/v1/ServiceMonitor` API exists and `prometheus.enabled` is set; the runtime monitor also needs `devicePlugin.enabled`. Both set `honorLabels: true`, so exported `node`/`namespace`/`pod` labels win over target labels.

## 3. NVIDIA monitor ports

|Family|HAMi vGPUmonitor|KAI kai-vgpu-monitor|Volcano vgpu-monitor|
|---|---|---|---|
|`hami_host_gpu_memory_used_bytes`, `hami_host_gpu_utilization_ratio`|yes, with `node`|yes, **no `node` label**; `device_type = "NVIDIA-"+name`|no|
|memory-controller util, temperature, power, ECC|yes|**missing**|no|
|`hami_vgpu_memory_used/limit_bytes`, `hami_container_device_utilization_ratio`, `hami_container_last_kernel_elapsed_seconds`, `hami_vgpu_memory_{context,module,buffer}_bytes`|yes|yes|no|
|`hami_container_device_memory_bytes`|5 identity labels|+ `context_size, module_size, buffer_size, offset` labels|no|
|`hami_mig_device_info` / `MigInfo`|yes|**missing**|no|
|Legacy names|opt-in|opt-in|**only names, always on**, host labels `deviceidx, deviceuuid` only; `Device_memory_desc_of_container` emitted as a **counter**; 3 container descriptors absent from `Describe`|
|Pod selection|`hami.io/vgpu-node` label, node-scoped|GPU-sharing annotations, node-scoped; regular containers only|cluster-wide informer, no node filter; regular containers only|
|Cache path|`/usr/local/vgpu/containers/{uid}_{ctr}/*.cache`|`{mount}/containers/{uid}_{ctr}/usage.cache`|`/usr/local/vgpu/vgpu/containers/...`, any name containing `.cache`|
|Cache version check|magic + size + major|magic (absent = not yet initialized) + exact v0 size / major 1 + size|magic + major only, no size check|

Sources: `KAI-resource-isolator/cmd/monitor/metrics.go:53-157`, `KAI-resource-isolator/chart/kai-resource-isolator/values.yaml:34-67`, `volcano-vgpu-device-plugin/cmd/vgpu-monitor/metrics.go:84-135, 318-319`, `volcano-vgpu-device-plugin/pkg/monitor/nvidia/cudevshr.go:85-100, 235-249`.

## 4. DRA

### HAMi-DRA monitor

- `:8080/metrics` and `:8000/healthz,/readyz`. `/readyz` returns 503 until both informers sync (`HAMi-DRA/cmd/monitor/app/options/options.go:63`, `cmd/monitor/app/monitor.go:129-170`). Values are computed at scrape; `--collect-interval` (30 s) has no effect on them.
- **Legacy aliases default ON** (`options.go:67`, chart `monitor.legacyMetrics: true`). This is the opposite of classic HAMi.
- Node labels N = `nodeid, deviceuuid, deviceidx, devicename, devicebrand, deviceproductname`; Pod series add `podnamespace` (= claim namespace) and `podname` (= `reservedFor[].name`).

|Metric|Labels|Unit|Source|Declared|
|---|---|---|---|---|
|`hami_dra_gpu_memory_limit_bytes`|N|bytes|ResourceSlice capacity `memory`|`HAMi-DRA/pkg/metrics/metrics.go:22-26`|
|`hami_dra_gpu_core_limit_ratio`|N|**0-1** (cores/100)|ResourceSlice capacity `cores`|`:27-31`|
|`hami_dra_gpu_memory_allocated_bytes`|N|bytes|Σ claim `consumedCapacity[memory]`|`:32-36`|
|`hami_dra_gpu_core_allocated_ratio`|N|0-1|Σ claim `consumedCapacity[cores]`|`:37-41`|
|`hami_dra_vgpu_memory_allocated_bytes`|N + podnamespace, podname|bytes|per claim result × consumer|`:42-46`|
|`hami_dra_vgpu_core_allocated_ratio`|N + podnamespace, podname|0-1|same|`:47-51`|

Legacy: `GPUDeviceMemoryLimit`, `GPUDeviceCoreLimit`, `GPUDeviceMemoryAllocated`, `GPUDeviceCoreAllocated`, `vGPUDeviceMemoryAllocated`, `vGPUDeviceCoreAllocated` in **MB and 0-100** (`metrics.go:58-87`). These share names, but not labels, with classic HAMi legacy families.

Caveats: `deviceidx` is the position in the cached slice, not a driver index. A claim shared by several consumers yields one identical series per consumer, so summing over Pods over-counts. An unhealthy device removed from the ResourceSlice disappears from node series, and Pod series for it are dropped with a warning.

### Kubelet drivers

- `k8s-dra-driver` (`hami-kubelet-plugin`): no Prometheus endpoint. Optional gRPC health (`--healthcheck-port`, chart 51516) checks plugin registration, not GPU health. NVML XID health sits behind the alpha gate `NVMLDeviceHealthCheck` (default off). A critical XID removes the device from the republished ResourceSlice (no taint) and needs a driver restart to recover. ECC events are only logged (`cmd/hami-kubelet-plugin/device_health.go:100-177`, `driver.go:465-500`).
- `ascend-dra-driver`: no Prometheus endpoint. gRPC health is not enabled by the chart. `Device.Health` is never read or written, so there is no device-health observation. ResourceSlices are republished at startup and after Prepare/Unprepare (`cmd/ascend-dra-kubeletplugin/driver.go:75-193`).

## 5. Ascend (ascend-device-plugin + hami-vnpu-core)

`:9395/metrics` is served only if the node runs `hamiVnpuCore` or `enpu` (`ascend-device-plugin/cmd/main.go:153-165`). Plain vNPU template mode has no metrics. When both modes are on, host series come from ENPU only (`internal/monitor/metrics.go:33-35`). The collector **reuses HAMi's NVIDIA family names**, with Ascend semantics and **without `node` or `zone`** labels.

|Metric|HAMivNPUCore mode|ENPU mode|
|---|---|---|
|`hami_host_gpu_memory_used_bytes`|DCMI `MemoryInfo` (total-available, MB→bytes); **overridden by Σ Pod shmem usage** when > 0|DCMI HBM usage; omitted on error|
|`hami_host_gpu_utilization_ratio`|DCMI AICore util 0-100; error → 0|same; omitted on error|
|`hami_vgpu_memory_used_bytes`|Σ shmem `procs[].hbm_used[i]` (hook accounting, overwritten every 5 s by DCMI per-PID usage)|DCMI process memory grouped by container via `/host/proc` cgroups|
|`hami_vgpu_memory_limit_bytes`|shmem `memory_limit`|`npu_info.config` `memory-limit`|
|`hami_container_device_utilization_ratio`|**host AICore util copied per container**|not emitted|
|`hami_vgpu_memory_{context,module,buffer}_bytes`|**constant 0**|not emitted|
|`hami_enpu_memory_request_bytes`, `hami_enpu_aicore_quota_percent`, `hami_enpu_allocation_info`|-|yes|
|`hami_enpu_config_collection_success`, `hami_enpu_device_collection_success`, `hami_enpu_memory_collection_success`|-|yes (0/1)|

Declared in `internal/monitor/collector.go:13-59` (core) and `internal/monitor/enpu_collector.go:17-22` (ENPU). In core mode, DCMI errors are swallowed as zero values (`internal/monitor/dsmi.go`). ENPU omits failed series and exports explicit success gauges.

hami-vnpu-core shmem (`hami-vnpu-core/crates/limiter/src/shmem/mod.rs:39-98`): `memory_limit@0`, `memory_used@8`, `active_workers@48`, `procs[64]@1080` (80 B slots: `pid`, `hbm_used[8]`, `is_active`). It also holds scheduler state (`compute_priority`, `state`, `tokens_remaining`, worker reports) that the plugin does not read. The Go reader uses hardcoded offsets (`ascend-device-plugin/internal/monitor/registry.go`), guarded by Rust compile-time asserts.

## 6. Hygon DCU

### dcu-exporter

`:16080/metrics`, background loop every 10 s (`dcu-exporter/main.go:39, 405, 469`). Gauges are reset every cycle.

Labels: `dcu_*` = `device_id, minor_number, name, node, pcieBus_number, dcu_pod_namespace, dcu_pod_name, container`. `vdcu_*` = `vdcu_minor_number, vdcu_computer_unit, vdcu_memory_cap, device_id, minor_number, name, node, dcu_pod_namespace, dcu_pod_name, container` (`main.go:35-37`). `node` is `/etc/hostname`, not the Kubernetes node name.

|Metric|Unit|Source|
|---|---|---|
|`dcu_temp`|°C|rocm-smi temperature sensor 0|
|`dcu_power_usage`, `dcu_powercap`|W|rocm-smi average power / cap|
|`dcu_sclk`|MHz|system clock|
|`dcu_utilizationrate`|0-100|rocm-smi busy percent|
|`dcu_usedmemory_bytes`, `dcu_memorycap_bytes`|bytes|VRAM used / total|
|`dcu_pciebw_mb`|MB (not MB/s)|PCIe throughput counters|
|`dcu_compute_unit_count`|CUs|static model table (6 models; others 0)|
|`dcu_compute_unit_remaining_count`, `dcu_memory_remaining`|CUs / undocumented|DMI remaining capacity|
|`dcu_ce_count`, `dcu_ue_count` (+`block_type`)|count (gauge)|ECC per block|
|`vdcu_utilizationrate`|0-100|DMI per-vDCU busy percent|
|`vdcu_usedmemory_bytes`|bytes|DMI per-vDCU memory|
|`vdcu_temp`, `vdcu_sclk`|°C / MHz|**copied from the physical device**|

Declared at `main.go:46-175`. Workload mapping: physical devices via kubelet PodResources (`hygon.com/dcu`, keyed by PCI BDF); shared devices via `"vdev"+minor`; dynamic vDCU via `/etc/vdev/<ns>_<pod>` files. In this checkout `dcu-vgpu-device-plugin` writes `/etc/vdev/vdev<N>.conf` key:value files and advertises bus IDs and `-fake-N` IDs (`dcu-vgpu-device-plugin/internal/pkg/dcu/server.go:187-197, 394-424`), so the vDCU Pod labels are likely empty `[INFERENCE]`.

Failure semantics: a DCGM error keeps the previous values (stale). If `/etc/hostname` cannot be read, the collector goroutine exits while `/metrics` keeps serving frozen values. A malformed `/etc/vdev` file blanks every `dcu_*` series after the reset (`main.go:215-282`). There is no `up`, timestamp or error metric.

### dcu-dcgm

A gin JSON API on `:16081`, with no auth and no `/metrics`. Each request reads rocm-smi/DMI directly (`dcu-dcgm/pkg/service/router/router.go:11-148`). `/AllDeviceInfos` returns the same physical and virtual structure the exporter uses. The same unauthenticated port also exposes mutating routes (`/CreateVDevices`, `/DestroyVDevice`, clock/fan/power setters, GET `/StartVDevice`).

### dcu-vgpu-device-plugin (archived)

Writes the node annotation and the vdev config files. It has no metrics, and all devices are reported `Healthy` unconditionally.

## 7. HAMi-WebUI exporter

It runs a 30 s refresh cycle with a 60 s timeout (`HAMi-WebUI/server/internal/exporter/exporter.go:29-30, 210-295`). Inventory comes from HAMi node/Pod annotations and telemetry from PromQL instant queries against an external Prometheus. Results are staged and committed atomically; cells not set in a committed cycle are pruned.

Emitted families (`metrics.go:52-221`). Device labels: `node, provider, device_type, device_uuid, driver_version, device_no`. Container labels: `node, provider, device_type, device_uuid, pod_name, container_name, namespace_name[, container_pod_uuid]`.

|Group|Families|Unit notes|
|---|---|---|
|Capacity (HAMi)|`hami_vgpu_count`, `hami_vmemory_size`, `hami_vcore_size`, `hami_vcore_scaling`, `hami_vmemory_scaling`, `hami_core_size`|MiB; `hami_core_size` constant 100; skipped for unconfigured devices|
|Device telemetry|`hami_memory_used`, `hami_memory_size`, `hami_memory_util`, `hami_core_used`, `hami_core_util`, `hami_core_used_avg`, `hami_core_util_avg`, `hami_device_temperature`, `hami_device_memory_temperature`, `hami_device_power`, `hami_device_last_xid_error_code`, `hami_device_fan_speed_p`, `hami_device_fan_speed_r`|memory **MiB**; util 0-100; `_avg` families re-run the **same instantaneous query**, not a time average|
|Container allocation|`hami_container_vgpu_allocated`, `hami_container_vmemory_allocated`, `hami_container_vcore_allocated`, `hami_container_vcore_allocation_known`|MiB / vcore units / 0-1 known flag|
|Container usage|`hami_container_memory_used`, `hami_container_memory_util`, `hami_container_core_used`, `hami_container_core_util`|MiB (help text says MB); util 0-100|
|Health|`hami_webui_metrics_refresh_success`, `hami_webui_metrics_refresh_duration_seconds`, `hami_webui_metrics_refresh_last_success_timestamp_seconds`|0/1, s, unix s|
|Declared, never set|`hami_pool_vgpu_count`, `hami_pool_vmemory_size`, `hami_pool_vcore_size`, `hami_system_component_health`|-|

Consumed upstream series per provider:

|Provider|Device telemetry|Workload core|Workload memory|
|---|---|---|---|
|NVIDIA|`DCGM_FI_DEV_FB_USED/FREE`, `DCGM_FI_DEV_GPU_UTIL`, `_GPU_TEMP`, `_MEMORY_TEMP`, `_POWER_USAGE`, `_FAN_SPEED`, `_XID_ERRORS` (needs **dcgm-exporter**)|`avg_over_time(hami_container_device_utilization_ratio[1m])`, clamped 0-100, no card fallback|`hami_vgpu_memory_used_bytes`|
|Ascend|`npu_chip_info_hbm_used_memory`, `_hbm_total_memory`, `_utilization`, `_temperature`, `_hbm_temperature`, `_power` (needs Huawei **npu-exporter**, keyed `vdie_id`)|**unsupported**|**unsupported**|
|Cambricon (`MLU`)|`mlu_memory_used/total`, `mlu_utilization`, `mlu_temperature`, `mlu_memory_temperature`, `mlu_power_usage`, `mlu_fan_speed`|`mlu_utilization` joined to `mlu_container`; >95 % card-util fallback|`mlu_memory_utilization` (percent of allocation) joined to `mlu_container`|
|Hygon DCU|`dcu_usedmemory_bytes`, `dcu_memorycap_bytes`, `dcu_utilizationrate`, `dcu_temp`, `dcu_power_usage`|`vdcu_percent{pod_uuid,container_name}` **not emitted by dcu-exporter**|`vdcu_usage_memory_size{pod_uuid,container_name}` **not emitted by dcu-exporter**|
|Hygon HCU|`hcu_*` (exporter outside the org)|`vhcu_utilizationrate` / `hcu_utilizationrate` 4-way fallback, no card fallback|`vhcu_usedmemory_bytes` / `hcu_usedmemory_bytes`|
|MetaX|`mx_memory_used/total` (KB), `mx_gpu_usage`, `mx_chip_hotspot_temp`, `mx_chip_hbm_temp`, `mx_board_power` (mW)|`mx_gpu_usage` (GPU) / `mx_sgpu_usage` (sGPU), >95 % fallback|`mx_memory_used` / `mx_sgpu_used_memory`|
|Other|unsupported, silently skipped (not counted as degraded)|-|-|

Query sites: `exporter.go:605-711` (device + task core), `:713-745` (HCU builder), `:744-788` (conversion + fallback), `:791-811` (task memory), `:917-960` (driver_version/device_no labels).

## 8. Health-only and producer components

|Repo|Prometheus|Health signal|Scheduler-facing state|Logs|
|---|---|---|---|---|
|amd-device-plugin|none (`client_golang` indirect only)|`-pulse` (default 0 = off): AMD Device Metrics Exporter gRPC socket `/var/lib/amd-metrics-exporter/amdgpu_device_metrics_exporter_grpc.socket`, falls back to a sysfs KFD check (`internal/pkg/exporter/health.go:36-104`)|`hami.io/node-amd-register` with `devcore` = CU count; annotation health hardcoded `true` (`internal/pkg/plugin/plugin.go:247`)|glog|
|amd-hami-core|none|-|-|stderr `[HAMI-core-hip ...]`, `LIBHIP_LOG_LEVEL`; OOM line `Device %d OOM: usage + alloc > limit` (`src/multiprocess/hip_multiprocess_memory_limit.c:540`)|
|biren-device-plugin|none|`healthCheck()` stub returns true; `--pulse` + 30 s `/dev/biren` poll trigger re-registration (`pkg/brgpu/runc.go:113-160`)|`hami.io/node-biren-register`, `hami.io/node-handshake-biren` (layout string `"2026.01.02 15:04:05"` is not a valid Go reference time, `pkg/brgpu/register.go:88`)|logrus/klog|
|mock-device-plugin|none|always Healthy; consumes other vendors' node annotations|reads only|klog|
|HAMi-core|none (writes the cache vGPUmonitor reads)|-|-|stderr `[HAMI-core ...]`, `LIBCUDA_LOG_LEVEL` (default 2); `Device %d OOM %lu / %lu` (`src/allocator/allocator.c:60`)|

## Cross-observer findings

1. **One name, several meanings.** `hami_host_gpu_*`, `hami_vgpu_memory_*` and `hami_container_device_utilization_ratio` are emitted by the NVIDIA vGPUmonitor, KAI and the Ascend collector. Only HAMi's host series carry `node`, and only HAMi/KAI carry `zone`. Ascend's container "utilization" is card AICore activity, and its context/module/buffer series are constant 0. A cross-vendor PromQL `sum by (namespace)` mixes these silently.
2. **Port overlap, not name overlap.** The HAMi scheduler (`:9395`) and the Ascend node collector (`:9395`) share a port number but not a single `hami_host_gpu_*` family: the scheduler emits none (`grep '"hami_host_gpu_' cmd/scheduler/metrics.go` = 0 hits; its families are `hami_gpu_*`/`hami_vgpu_*`, listed in §2). The actual `hami_host_gpu_*` name collision is between vGPUmonitor (`:9394`), KAI (`:9394`) and the Ascend collector (`:9395`), per finding 1. The scheduler/Ascend port match is otherwise benign: separate Pods, and the Ascend plugin does not use `hostNetwork` (`ascend-device-plugin/examples/enpu/README.md:60`), so there is no bind conflict; scrape jobs must still select by Service, not by port.
3. **`_ratio` scale.** 0-100: HAMi host/container utilization, scheduler core limit/allocated, Ascend. 0-1: scheduler `hami_node_gpu_memory_allocated_ratio`, HAMi-DRA core ratios. WebUI uses `_util` with 0-100.
4. **Memory units.** Bytes: vGPUmonitor, scheduler (converted from MiB), DRA current, Ascend, dcu-exporter. MiB: WebUI families and scheduler `device_memory_limit` label values. MB: DRA legacy. KB: MetaX input. Tenant "used" means hook accounting for HAMi-core (`used.total`) and Ascend core mode, but process-level DCMI/NVML for ENPU and for HAMi-core's unexported `monitorused`.
5. **Reservation vs consumption identity.** Scheduler `hami_vgpu_memory_allocated_bytes` has labels `namespace, node, pod, device_uuid` (no container). Runtime `hami_vgpu_memory_used_bytes` has labels `namespace, pod, container, vdevice_index, device_uuid` (no node on tenant series). Joining them requires `sum by (namespace, pod, device_uuid)` on the runtime side.
6. **Container utilization is not normalized to the reservation.** The NVIDIA value is Σ per-process SM share of the whole GPU. WebUI turns it into `core_used = activity × allocatedCore / 100`, which assumes activity is relative to the allocation. The two disagree for any container with a core limit below 100.
7. **Failure signalling differs.** Explicit 0/1 health gauges: ENPU (`hami_enpu_*_collection_success`), WebUI (`hami_webui_metrics_refresh_*`), scheduler (`cache_synced`, `is_leader`). Absent series with nothing but logs: vGPUmonitor, KAI, DRA. Stale or zero values that look healthy: Ascend core mode (DCMI error → 0), dcu-exporter (frozen loop, blanked or stale gauges), Volcano (memory read failure → 0).
8. **Legacy defaults diverge.** Opt-in for HAMi scheduler/monitor and KAI; default on for HAMi-DRA; legacy-only for Volcano.
9. **WebUI depends on exporters outside Project-HAMi** for every vendor's physical telemetry (dcgm-exporter, npu-exporter, mlu/mx/hcu exporters). The only in-org runtime sources it consumes are vGPUmonitor's tenant families (NVIDIA) and dcu-exporter's physical families (DCU).
10. **Health is not a metric anywhere.** AMD/Biren annotations always say healthy. AMD can mark devices Unhealthy only through kubelet when `-pulse` > 0. The NVIDIA DRA driver removes XID-failed devices from the ResourceSlice. No component exports device health as a Prometheus series (WebUI's `hami_device_last_xid_error_code` re-exports DCGM).
