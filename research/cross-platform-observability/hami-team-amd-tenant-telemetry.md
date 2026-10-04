# Question for the HAMi team: per-tenant usage on shared AMD GPUs

Raised while preparing the "One Agent, Every GPU" observability talk. Static source review at the pinned commits in [repositories.json](repositories.json); nothing here was tested on AMD hardware.

## The question

On NVIDIA, vGPUmonitor reports each container's GPU memory use against its limit and its share of SM time, joined to Pod names. On AMD, HAMi schedules and enforces memory limits on shared GPUs, but nothing reports per-container usage. Is that intended, and is an AMD equivalent planned?

Device telemetry (DCGM on NVIDIA, the AMD Device Metrics Exporter on AMD) is enough when a Pod owns a whole GPU or a hardware partition. With HAMi soft sharing, several Pods share one GPU, and device telemetry has one number per card and no knowledge of each Pod's limit.

## What exists today

| | NVIDIA | AMD |
|---|---|---|
| Limit enforcement in the container | HAMi-core (CUDA hooks) | amd-hami-core (HIP hooks via `LD_AUDIT`) |
| Per-process memory accounting | Yes, shared cache | Yes, shared cache `/tmp/hipdevshr.cache` by default |
| Cache reachable from the node | Yes: the device plugin sets `CUDA_DEVICE_MEMORY_SHARED_CACHE` and mounts a per-container host directory ([server.go](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/pkg/device-plugin/nvidiadevice/nvinternal/plugin/server.go#L1395-L1424)) | No: the plugin sets only `HIP_DEVICE_MEMORY_LIMIT` and `LD_AUDIT` ([plugin.go](https://github.com/Project-HAMi/amd-device-plugin/blob/9a3e617def1f0a22d023e1cc2a5398ebd9283a5f/internal/pkg/plugin/plugin.go#L773-L780)); the cache stays at the container-local default ([libamvgpu.h](https://github.com/Project-HAMi/amd-hami-core/blob/050cd7341dfe447483f087494fd0259eacd2006e/src/include/libamvgpu.h#L51-L58)) |
| Per-process compute samples | Yes, NVML samples written by HAMi-core's watcher | No: `multiprocess_utilization_watcher.c` exists but is not in the build ([CMakeLists.txt.hip](https://github.com/Project-HAMi/amd-hami-core/blob/050cd7341dfe447483f087494fd0259eacd2006e/CMakeLists.txt.hip#L56-L70)) |
| Node collector exporting tenant metrics | vGPUmonitor `:9394` ([metrics.go](https://github.com/Project-HAMi/HAMi/blob/39699df26042b3e5062a76e00b3e4f74b72ad503/cmd/vGPUmonitor/metrics.go#L92-L140)) | None |
| Device telemetry | NVML in vGPUmonitor; optional dcgm-exporter | AMD Device Metrics Exporter (external) |

For comparison, Ascend took the in-plugin route: `ascend-device-plugin` reads hami-vnpu-core's shared memory and exports the same `hami_vgpu_memory_*` names on `:9395`.

## Health integration notes

The only use of the AMD Device Metrics Exporter is a health check in `amd-device-plugin` ([health.go](https://github.com/Project-HAMi/amd-device-plugin/blob/9a3e617def1f0a22d023e1cc2a5398ebd9283a5f/internal/pkg/exporter/health.go#L36-L104)):

- It runs only when `-pulse` > 0; the default is 0 ([main.go](https://github.com/Project-HAMi/amd-device-plugin/blob/9a3e617def1f0a22d023e1cc2a5398ebd9283a5f/cmd/k8s-device-plugin/main.go#L109)).
- It keeps one field per GPU (healthy or not) and reports it only to the kubelet. The node annotation the scheduler reads always says healthy ([plugin.go](https://github.com/Project-HAMi/amd-device-plugin/blob/9a3e617def1f0a22d023e1cc2a5398ebd9283a5f/internal/pkg/plugin/plugin.go#L247)).
- Results are keyed by the exporter's `gpu.Device`, but looked up by the plugin's device ID, which is `<id>#<splitIdx>` ([plugin.go](https://github.com/Project-HAMi/amd-device-plugin/blob/9a3e617def1f0a22d023e1cc2a5398ebd9283a5f/internal/pkg/plugin/plugin.go#L478)). Unless the exporter uses the same format, every lookup misses and the sysfs fallback decides health. Not verified against a running exporter.

## Questions

1. Is per-tenant usage on shared AMD GPUs on the roadmap? If so, a collector inside `amd-device-plugin` (as Ascend did) or vendor backends in vGPUmonitor?
2. Should the plugin mount the HIP shared cache per container on the host, as the NVIDIA path does, so a node collector can read it? Is the cache layout stable enough to be read from outside?
3. For compute: is building the utilization watcher planned, or should per-tenant compute come from AMD SMI per-process data (if its fields support it)?
4. Health: should exporter health also reach the scheduler annotation, and is the device-ID key mismatch above real?

## Smallest useful step

Export `hami_vgpu_memory_used_bytes` and `hami_vgpu_memory_limit_bytes` for AMD containers with the same labels as NVIDIA. That needs the host-mounted cache (question 2) and a reader; compute can follow. It would let one dashboard compare reservation and use across NVIDIA, Ascend and AMD.

## Until answered, the talk says

AMD has scheduler reservations in HAMi and device telemetry from AMD's exporter, but no per-tenant usage; this is presented as a contribution opportunity, not a limitation by design.
