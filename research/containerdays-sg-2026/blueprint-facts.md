# Blueprint facts: HAMi neocloud section (ContainerDays SG 2026)

Paths are relative to /home/neocloud/projects/talks. Chart = references/HAMi/charts/hami (Chart.yaml:18,24 version/appVersion 2.10.0). "NOT FOUND" = searched, absent.

## 1. Components and where they run

Names use `fullname` (_helpers.tpl:13-26). If the release name contains the chart name, fullname = release name, so release `hami` gives `hami-scheduler` and `hami-device-plugin`. README.md confirms the pod names `hami-device-plugin` and `hami-scheduler` (references/HAMi/README.md:132).

- **Namespace**: the chart uses the release namespace (`hami-vgpu.namespace`, _helpers.tpl:29-33). The documented install is `helm install hami hami-charts/hami -n kube-system` (references/HAMi/README.md:123; website/docs/userguide/configure.md:65). Viettel excludes `hami-system` from Kyverno, so they ran HAMi in `hami-system` (kcd_vietnam.md:1013). **kube-system is a convention, not a chart default.**
- **Scheduler**: Deployment `{{fullname}}-scheduler` (templates/scheduler/deployment.yaml:8-10) with two containers:
  - `kube-scheduler`: runs only if `scheduler.kubeScheduler.enabled` (deployment.yaml:49; values.yaml:~130).
  - `vgpu-scheduler-extender`: command `scheduler` (deployment.yaml:85,116-117). It hosts the filter/bind extender, the `/webhook` endpoint and the metrics.
  - Ports in the extender container: `https` 9443 (deployment.yaml:181-182), `metrics` from metricsBindAddress, default :9395 (deployment.yaml:189-190; values.yaml:57).
  - Filter/bind are served on loopback `127.0.0.1:9444` (deployment.yaml:133; values.yaml extenderPort: 9444).
  - Pod labels include `app.kubernetes.io/component: hami-scheduler` and `hami.io/webhook: ignore` (deployment.yaml:34-36).
  - Website table: webhook and extender are both "Deployment (embedded in hami-scheduler Pod)" (website/docs/core-concepts/gpu-virtualization.md:68-69).
- **Mutating webhook**: MutatingWebhookConfiguration `{{fullname}}-webhook` (webhook.yaml:3,9).
  - Webhook name `vgpu.hami.io` (webhook.yaml:25), path `/webhook` (webhook.yaml:20).
  - Operations CREATE and UPDATE on pods (webhook.yaml:81-82).
  - `failurePolicy: Ignore` by default (values.yaml:223). Per values.yaml:305-308, if the webhook is blocked, pods are scheduled by the default scheduler with no GPU allocated and no error surfaced.
  - It rewrites `schedulerName` to `hami-scheduler` (default `schedulerName: "hami-scheduler"`, values.yaml:41). Pods that name their own scheduler are skipped (gpu-virtualization.md:68).
  - `forceOverwriteDefaultScheduler: true` (values.yaml:89).
  - Opt-out label: `hami.io/webhook: ignore` on namespace or pod (values.yaml:198,211; webhook.yaml:39,62).
- **Device plugin**: DaemonSet `{{fullname}}-device-plugin` (daemonsetnvidia.yaml:6-8).
  - Container `device-plugin`, command `nvidia-device-plugin --config-file=/device-config.yaml --mig-strategy=... --disable-core-limit=...` (daemonsetnvidia.yaml:111,119-122).
  - postStart runs `/k8s-vgpu/bin/vgpu-init.sh <gpuHookPath>/vgpu/` (daemonsetnvidia.yaml:114-117). This is how libvgpu lands on the host at `/usr/local/vgpu` (values.yaml:13 gpuHookPath, libPath :453-ish).
  - nodeSelector default `gpu: "on"` (values.yaml:475-476; daemonsetnvidia.yaml:378-380). The install step is `kubectl label nodes <node> gpu=on` (README.md:110).
  - `hostPID: true`, privileged (values.yaml:463,469-474).
- **vGPUmonitor**: runs as a second container `vgpu-monitor` in the **same DaemonSet** (daemonsetnvidia.yaml:241-245). It has no separate DaemonSet. Port `metrics` 9394 (daemonsetnvidia.yaml:281-282). The Service `{{fullname}}-device-plugin-monitor` (monitorservice.yaml:3-5) exposes targetPort 9394 as NodePort 31992 by default (monitorservice.yaml:19-23; values.yaml `devicePlugin.service.httpPort: 31992`).
- **HAMi-core / libvgpu.so injection**: not a pod. The device plugin's `Allocate` does the work (gpu-virtualization.md:70,163-168):
  - hostPath-mounts `/usr/local/vgpu/libvgpu.so`.
  - hostPath-mounts `/usr/local/vgpu/ld.so.preload` to `/etc/ld.so.preload`. The file contains one line, `/usr/local/vgpu/libvgpu.so`.
  - Injects env `CUDA_DEVICE_MEMORY_LIMIT_<idx>=<N>m` (from gpumem) and `CUDA_DEVICE_SM_LIMIT=<pct>` (from gpucores).
  - libvgpu overrides `dlsym` to hook specific cu*/nvml* calls (gpu-virtualization.md:71,170-180).
  - Standalone HAMi-core usage: `LD_PRELOAD=./libvgpu.so`, `CUDA_DEVICE_MEMORY_LIMIT`, `CUDA_DEVICE_SM_LIMIT` (references/HAMi-core/README.md:56,60-68).
  - Viettel deck's own wording: "HAMi-Core library injected by the container runtime" (kcd_vietnam.md:217-220); libvgpu is an `LD_PRELOAD` interposer needing glibc (kcd_vietnam.md:1073).
- **Other chart pieces**:
  - Optional mock device plugin DaemonSet (templates/device-plugin/daemonsetmock.yaml; values mockDevicePlugin.enabled: false).
  - Optional lupine remote-GPU DaemonSet (daemonsetlupine.yaml; values.yaml:597).
  - cert-gen Jobs `create` and `patch` with component `admission-webhook` (templates/scheduler/job-patch/job-createSecret.yaml:39, job-patchWebhook.yaml:39).
  - Prerequisites: Kubernetes >= 1.23, glibc >= 2.17, Helm > 3.0, NVIDIA as default runtime (README.md:99-103). The chart itself only declares `kubeVersion: ">= 1.18.0-0"` (Chart.yaml:26).

## 2. Scheduling policy

- **Helm defaults** (values.yaml:54-56):
  - `scheduler.defaultSchedulerPolicy.nodeSchedulerPolicy: binpack`
  - `scheduler.defaultSchedulerPolicy.gpuSchedulerPolicy: spread`
  - They are passed as `--node-scheduler-policy` / `--gpu-scheduler-policy` (deployment.yaml:137-138). Binary defaults are the same (cmd/scheduler/main.go:73-74).
- **Allowed values, node level**: `binpack`, `spread` only (pkg/util/types.go:70,72; `IsValidNodeSchedulerPolicy` pkg/util/util.go:349-355). Code comment: "binpack or spread. default value is binpack" (pkg/scheduler/config/config.go:67).
- **Allowed values, GPU level** (pkg/util/types.go:73-82; accepted set at pkg/util/util.go:325-326):
  - `binpack`, `spread`
  - `topology-aware`
  - `mutex`: only idle GPUs are allocated
  - `numa`: chained sort key
  - Comma-separated chains are valid, e.g. `binpack,numa`, `mutex,topology-aware` (util.go:315-318; util_test.go:93-97).
  - An unrecognised annotation value is ignored with a warning and the configured default stands (util.go:358-378).
- **Topology-aware**: setting `gpuSchedulerPolicy: topology-aware` makes the chart add env `ENABLE_TOPOLOGY_SCORE=true` to the device plugin (daemonsetnvidia.yaml:169-171). The Viettel/KCD deck says "binpack, spread, topology-aware" (kcd_vietnam.md:95,558).
- **Per-pod annotations, exact spelling** (pkg/util/types.go:87,89):
  - `hami.io/node-scheduler-policy`
  - `hami.io/gpu-scheduler-policy`
  - Also `hami.io/device-scoring-weights` (e.g. `"slot=1,core=1,memory=3"`, types.go:91; configure.md:85) and `hami.io/numa-alignment` (best-effort|strict, types.go:95; values.yaml:393-395).
  - Docs table: configure.md:83-84. YAML example: gpu-virtualization.md:197-199.
  - Workshop deck table: gpu_workshop.md:363-364; example `hami.io/gpu-scheduler-policy: spread` at gpu_workshop.md:401.
- **DOC CONFLICT**: website/docs/userguide/nvidia-device/scheduling-policy.md:74 says only node-level policy can be overridden per pod. Source (util.go:358-378), configure.md:84 and the dynamic-MIG example (userguide/nvidia-device/examples/dynamic-mig-example.md:13-14) show GPU-level per-pod override works. Trust the source.
- **DOC CONFLICT**: scheduling-policy.md:15,75 mention `numa-first` as "not yet implemented". The source uses `numa` as a sort key, not `numa-first`.
- **Node score formula** (gpu-virtualization.md, section "Node Scheduling Strategy"): `(UsedDevices/Total + UsedCompute/Total + UsedVRAM/Total) x 10`. Binpack picks the higher score, spread the lower. Binpack = free whole machines for training; spread = online inference HA (kcd_vietnam.md:533-536).

## 3. Pod resource names, type selection, compute policy

- **NVIDIA** (values.yaml:578-582; device-configmap.yaml:19-22):
  - `nvidia.com/gpu`: count
  - `nvidia.com/gpumem`: MB; hard limit
  - `nvidia.com/gpumem-percentage`
  - `nvidia.com/gpucores`: % of cores
  - `nvidia.com/priority`
  - Defaults in device-configmap.yaml:24-26: `defaultMemory: 0` (0 = 100% of device), `defaultCores: 0`, `defaultGPUNum: 1` (semantics: configure.md:32-34). `memoryFactor: 1` (device-configmap.yaml:28; configure.md:35).
  - If `gpumem`/`gpucores` is set without `nvidia.com/gpu`, the webhook adds `nvidia.com/gpu` with the default count (configure.md:34).
  - Viettel's user YAML (kcd_vietnam.md:671-673): `nvidia.com/gpu: 1`, `gpumem: 2000 # MB - a hard limit`, `gpucores: 30 # % - best effort`.
- **Ascend** (values.yaml:634-665 customresources; device-configmap.yaml:142-270). Each chip has three resources, e.g. `huawei.com/Ascend910B` is not a name; the real names are:
  - 910A: `huawei.com/Ascend910A`, `-memory`, `-core`
  - 910B2: `huawei.com/Ascend910B2`, `-memory`, `-core`
  - 910B3: `huawei.com/Ascend910B3`, `-memory`, `-core`
  - 910B4: `huawei.com/Ascend910B4`, `-memory`, `-core`
  - 910B4-1: `huawei.com/Ascend910B4-1`, `-memory`, `-core`
  - 310P: `huawei.com/Ascend310P`, `-memory`, `-core`
  - 910C: `huawei.com/Ascend910C`, `-memory`, `-core`
  - Ascend is off by default: `devices.ascend.enabled: false` (values.yaml:637). `hamiVnpuCore: false` toggles soft-partitioning (values.yaml:636).
  - The 910B4 template list (`vir05_1c_8g`, `vir10_3c_16g`) is at device-configmap.yaml:233-241.
- **Other vendors** (values.yaml; device-configmap.yaml):

| Vendor | count / memory / core |
|---|---|
| Hygon (values.yaml:521-524) | `hygon.com/hcunum` / `hygon.com/hcumem` / `hygon.com/hcucores` |
| Cambricon (:525-528) | `cambricon.com/vmlu` / `cambricon.com/mlu.smlu.vmemory` / `cambricon.com/mlu.smlu.vcore` |
| MetaX (:516-519) | `metax-tech.com/sgpu` / `metax-tech.com/vmemory` / `metax-tech.com/vcore` (plain `metax-tech.com/gpu` at device-configmap.yaml:65) |
| Kunlunxin (:538-546) | `kunlunxin.com/xpu`, `kunlunxin.com/vxpu`, `kunlunxin.com/vxpu-memory` |
| Enflame (:547-556) | `enflame.com/drs-gcu`, `enflame.com/gcu-memory`, `enflame.com/gcu-core`, `enflame.com/gcu` |
| Moore Threads (:557-560) | `mthreads.com/vgpu` (plus `mthreads.com/sgpu-memory`, `mthreads.com/sgpu-core` at device-configmap.yaml) |
| AMD (:529-533; device-configmap.yaml:127-130) | `amd.com/gpu`, `amd.com/gpumem`, `amd.com/gpucores` |
| AWS Neuron | `aws.amazon.com/neuron`, `aws.amazon.com/neuroncore` |
| Vastai | `vastaitech.com/va` |
| Biren | `birentech.com/gpu` |
| Iluvatar (values.yaml:666-680) | per-chip `iluvatar.ai/<chip>-vgpu`, `.vCore`, `.vMem` |

- **GPU type / UUID selection, NVIDIA** (pkg/device/nvidia/device.go:46-47,51,53):
  - `nvidia.com/use-gputype`: comma-separated, must match, e.g. `"A100,V100"` (userguide/nvidia-device/examples/specify-card-type-to-use.md:13; configure.md:82)
  - `nvidia.com/nouse-gputype`: exclusion list (configure.md:81)
  - `nvidia.com/use-gpuuuid` / `nvidia.com/nouse-gpuuuid` (device.go:51,53; configure.md:79-80)
  - `nvidia.com/vgpu-mode`: `hami-core` or `mig` (device.go:54; configure.md:86)
  - `nvidia.com/numa-bind` (device.go:48)
  - Node annotation `hami.io/device-cordon`: list of GPU UUIDs to exclude from new allocations without evicting (device.go:55-60).
  - Other vendors' use-type annotations were not checked. They are NVIDIA-prefixed here.
- **Compute-limit policy**: there is no pod annotation for it. NOT FOUND.
  - Mechanism 1, container env `GPU_CORE_UTILIZATION_POLICY` = `default` | `force` | `disable` (configure.md:92; const `CoreLimitSwitch` pkg/util/types.go:40; values at device.go:84-88).
    - `default`: gpucores is only a hint.
    - `force`: hard cap below gpucores.
    - `disable`: ignore gpucores.
  - Mechanism 2, cluster-wide: `devices.nvidia.gpuCorePolicy: default` (values.yaml:595; device-configmap.yaml:33). If it is not `default`, the webhook injects the env into every GPU container (device.go:396-405).
  - Mechanism 3: `devicePlugin.disablecorelimit: "false"` (values.yaml:438; passed as `--disable-core-limit`, daemonsetnvidia.yaml:121).
  - `CUDA_DISABLE_CONTROL=true` turns HAMi-core off entirely, for debugging (configure.md:93).
  - Viettel's measurement (kcd_vietnam.md:992-994): gpumem is "a real limit"; gpucores default is "only a hint" (10% and 90% ran the same speed); gpucores with `force` is "a real cap" (70% cores: run takes 1h20, not 1h). Takeaway: "promise memory, do not promise compute" (kcd_vietnam.md:966).

## 4. Quota

- **Yes, supported**: HAMi tracks ResourceQuota on the device memory and core resource names.
  - Docs page "Using Extended ResourceQuota for NVIDIA Devices" (website/docs/userguide/nvidia-device/using-resourcequota.md:2-3,9).
  - Exact syntax (using-resourcequota.md:22-34): the key must carry the `limits.` prefix:

```yaml
spec:
  hard:
    limits.nvidia.com/gpu: 2
    limits.nvidia.com/gpumem: 2000
```

  - Code: `QuotaManager` (pkg/device/quota.go:40); `managedQuotaName` only accepts keys starting with `limits.` (quota.go:292-301). `IsManagedQuota` matches only a device's **memory** or **core** resource name (quota.go:200-209).
  - So `limits.nvidia.com/gpumem` and `limits.nvidia.com/gpucores` are tracked by HAMi (core key shown for Cambricon/scheduler tests at pkg/scheduler/scheduler_test.go:2245-2246; nvidia gpumem at device_test.go:1487).
  - **The docs example includes `limits.nvidia.com/gpu: 2`, but the source only matches memory/core names.** Treat the count limit as unverified in HAMi code. [INFERENCE] enforcement of the count would come from native Kubernetes, not HAMi.
  - Counting: a 2-GPU x 2000 MB pod is charged 4000 (using-resourcequota.md:9-15). Whole-card and percentage requests are resolved against the actual device and charged (using-resourcequota.md:18). Scaled by `memoryFactor` (pkg/device/devices.go:215-219). An explicit quota of 0 is a hard block (quota.go:32-34).
  - Admission check: `fitResourceQuota` in the webhook (pkg/scheduler/webhook.go:147,285). Scheduler Fit check emits reason `ResourceQuotaNotFit` (pkg/device/common/common.go:42; nvidia/device.go:1055-1057).
  - Quotas work for other vendors too, e.g. Cambricon `limits.cambricon.com/mlu.smlu.vmemory` (cambricon/device_test.go:1806; v2.10 changelog "enforce quotas for every device backend", website/CHANGELOG.md:29).
  - Interaction with the Kubernetes quota admission controller: the native controller charges once at pod creation, so a pod can be rejected before HAMi sees it (website/docs/developers/init-container-design.md:213-217).
- **Version**: introduced in **v2.7.0** (2025-09-26): "NVIDIA Resourcequota ... #1359" (website/CHANGELOG.md:398,403). Accounting fixes in v2.10.0 (2026-08-21): clamp negative usage, all backends, explicit zero limit (CHANGELOG.md:3,29).
- **Quota metrics** (scheduler): `hami_resource_quota_used{namespace,quota_name,limit}` and `hami_resource_quota_limit{namespace,quota_name}` (cmd/scheduler/metrics.go:347-356). Docs sample: `{quota_name="nvidia.com/gpucores", namespace="default", limit="200"}` (device-allocation.md:25).
- **NOT FOUND**: a separate HAMi quota CRD. There is only the standard ResourceQuota.
- **NOT FOUND**: a quota feature in HAMi-DRA (no ResourceQuota code or doc in references/HAMi-DRA).

## 5. Metrics

**Ports**
- Scheduler: container port `metrics` = 9395 (values.yaml:57; deployment.yaml:189-190). Service port `monitor` 31993 (scheduler/service.yaml; values.yaml:284 `monitorPort: 31993`). `curl <scheduler-ip>:31993/metrics` (website/docs/userguide/monitoring/device-allocation.md:6-9).
- vGPUmonitor: container 9394 (daemonsetnvidia.yaml:281-282), NodePort 31992 (monitorservice.yaml:19-23). `curl <GPU-node-ip>:31992/metrics` (real-time-device-usage.md:6-9). Both are NodePort by default in v2.10.0 (grafana-dashboard.md:34-41).
- ServiceMonitors are available behind `prometheus.enabled` (values.yaml:684-685; device-plugin/servicemonitor.yaml:4,20; scheduler/servicemonitor.yaml).
- Workshop shows ports as :9395 scheduler (allocation) and :9394 monitor (usage) (gpu_workshop.md:535-536,545,554).

**Scheduler = ALLOCATION** (cmd/scheduler/metrics.go; not real utilization, device-allocation.md:40):
- `hami_gpu_memory_limit_bytes` (:162), `hami_gpu_core_limit_ratio` (:167)
- `hami_gpu_memory_allocated_bytes` (:172), `hami_gpu_core_allocated_ratio` (:182)
- `hami_gpu_shared_count` (:177)
- `hami_node_gpu_overview` (:187), `hami_node_gpu_memory_allocated_ratio` (:192, 0-1)
- `hami_node_gpu_mig_instance_info` (:197)
- `hami_vgpu_memory_allocated_bytes` (:390), `hami_vgpu_core_allocated_ratio` (:395), per pod
- `hami_resource_quota_used` (:348), `hami_resource_quota_limit` (:353)
- `hami_scheduler_is_leader` (:511), `hami_scheduler_cache_synced` (:516)
- `hami_scheduler_allocations_total`, `hami_scheduler_allocation_failures_total`, `hami_scheduler_bind_rollbacks_total` (pkg/metrics/scheduler.go:53-55)
- `hami_build_info` (pkg/metrics/metrics.go:30)
- Remote-GPU: `hami_remote_gpu_allocated`, `hami_remote_gpu_memory_limit_bytes`, `hami_remote_gpu_overview` (metrics.go:474-484)
- Legacy names exist behind `legacyMetrics: true` (values.yaml:682), e.g. `GPUDeviceMemoryAllocated`, `vGPUMemoryAllocated`, `QuotaUsed` (metrics.go:215-232,360,408-413). Default is false.

**vGPUmonitor = REAL USAGE** (cmd/vGPUmonitor/metrics.go):
- Host: `hami_host_gpu_memory_used_bytes` (:58), `hami_host_gpu_utilization_ratio` (:64, 0-100), `hami_host_gpu_memory_controller_utilization_ratio` (:70), `hami_host_gpu_temperature_celsius` (:76), `hami_host_gpu_power_usage_watts` (:82), `hami_host_gpu_ecc_errors_total` (:88)
- Per container: `hami_vgpu_memory_used_bytes` (:93), `hami_vgpu_memory_limit_bytes` (:99), `hami_container_device_memory_bytes` (:104), `hami_container_device_utilization_ratio` (:109)
- Docs table (real-time-device-usage.md:16-18,26-30) also lists `hami_container_last_kernel_elapsed_seconds`. v2.10.0 moved context/module/buffer sizes to `hami_vgpu_memory_context_bytes`, `hami_vgpu_memory_module_bytes`, `hami_vgpu_memory_buffer_bytes` (real-time-device-usage.md:37).
- Viettel: "per-pod GPU metrics (DCGM can't, only per physical GPU)" (kcd_vietnam.md:654,664). 2.9 renamed every metric and dashboards went empty (kcd_vietnam.md:1007,1016).
- Workshop deck lists the names without the `hami_` prefix (gpu_workshop.md:546-559).
- Old WebUI names (`hami_memory_size`, `hami_core_util`, `hami_container_vgpu_allocated`, ...) are what HAMi-WebUI queries (references/HAMi-WebUI/packages/web/projects/vgpu/metrics/query-contract.mjs:2-12; server/internal/exporter/metrics.go:84,104,149). gpu_workshop.md:634-636 says a PrometheusRule is needed to translate.
- DRA mode metrics: `hami_dra_gpu_core_limit_ratio`, `hami_dra_gpu_memory_limit_bytes`, `hami_dra_gpu_core_allocated_ratio`, `hami_dra_gpu_memory_allocated_bytes`, `hami_dra_vgpu_core_allocated_ratio`, `hami_dra_vgpu_memory_allocated_bytes` (references/HAMi-DRA/docs/MONITOR.md:113-124). The monitor serves :8080 and health :8000 (MONITOR.md:145-153; monitor-deployment.yaml:46-50). README example NodePort 31995 (README.md:107,113). **NOT FOUND**: a DRA-mode real-time-usage exporter equivalent to vGPUmonitor.

## 6. Node and device config keys

**(a) Cluster device config**: ConfigMap `{{scheduler fullname}}-device` = `hami-scheduler-device` (device-configmap.yaml:5), mounted as `/device-config.yaml`. Values:
- `devices.nvidia.deviceSplitCount: 10` (values.yaml:583; configure.md:29: "Maximum jobs assigned to a single GPU device")
- `devices.nvidia.deviceMemoryScaling: 1` (values.yaml:584; configure.md:28: >1 enables virtual device memory, experimental)
- `devices.nvidia.deviceCoreScaling: 1` (values.yaml:585)
- `preConfiguredDeviceMemory: 0` (values.yaml:588)
- `enableNumaTopology: false` (values.yaml:591)
- `gpuCorePolicy: default` (values.yaml:595)
- `libCudaLogLevel: 1` (values.yaml:596)
- `migProfileAllowlist` (device-configmap.yaml:36-60)
- Override whole file with `device-config.content` (values.yaml:687-697).

**(b) Per-node config**: ConfigMap `{{fullname}}-device-plugin` = `hami-device-plugin`, key `config.json` (device-plugin/configmap.yaml:5-12; configure.md:47). Default JSON in values.yaml `devicePlugin.nodeConfiguration.config` (values.yaml:412-436), with keys:

| key | default in chart example | meaning (source) |
|---|---|---|
| `name` | `your-node-name` (placeholder) | node name (configure.md:50) |
| `operatingmode` | `hami-core` | `hami-core` or `mig` (configure.md:51; device.go:62-65 also defines `mps`) |
| `devicememoryscaling` | 1 | overcommit ratio of device memory (configure.md:52) |
| `devicecorescaling` | not in default JSON | overcommit ratio of device core (configure.md:53; json tag device.go:125) |
| `devicesplitcount` | 10 | tasks per device (configure.md:54) |
| `preconfigureddevicememory` | 0 | MB for GPUs with no memory query (device.go:126) |
| `enablenumatopology` | false | device.go:132 |
| `migstrategy` | `none` | device.go:148 |
| `filterdevices.uuid` / `.index` | [] | devices not registered to HAMi (configure.md:55-58; device.go:135-140) |
| `enablegetpreferredallocation` | false | device.go:150 |

- Per-node values overwrite the shared ones (device.go:144 comment).
- Use an existing ConfigMap via `devicePlugin.nodeConfiguration.externalConfigName` (values.yaml:436).
- Priority: externalConfigName > config > default (values.yaml:411).
- Other chart-level keys: `devicePlugin.migStrategy: "none"` (:437), `devicePlugin.disablecorelimit: "false"` (:438), `devicePlugin.deviceListStrategy: envvar` (:440), `scheduler.nodeLockExpire: 5m` (values.yaml:172; env `HAMI_NODELOCK_EXPIRE`, deployment.yaml:107). Docs table at configure.md:71-73.
- Selecting nodes for HAMi: `global.managedNodeSelectorEnable: false`, `managedNodeSelector: {usage: gpu}` (values.yaml:16-18).

## 7. MIG

- Static strategy flag: `--mig-strategy=[none|single|mixed]`, default `none` (cmd/device-plugin/nvidia/main.go:107-111). Chart value `devicePlugin.migStrategy: "none"` (values.yaml:437). configure.md:30 documents `"none"` vs `"mixed"` (separate MIG resources).
- **Dynamic MIG**: node setting `operatingmode: mig` (website/docs/userguide/nvidia-device/dynamic-mig-support.md:44). Pod selects it with annotation `nvidia.com/vgpu-mode: "mig"` (dynamic-mig-support.md:110; configure.md:86). Optional `nvidia.com/mig-profile-preference: "4g"` (developers/dynamic-mig-migration.md:257).
  - Users keep requesting `nvidia.com/gpu` + `nvidia.com/gpumem` (dynamic-mig-support.md:102,124; dynamic-mig-migration.md:330).
  - Without the annotation a pod can land in a HAMi-core or MIG pool (dynamic-mig-support.md:124).
  - Version: first shipped in v2.5.0 (2025-02-06) (website/CHANGELOG.md:728,732). v2.10 is a reservation-first rewrite that needs HAMi v2.10.0+, Ampere/Hopper/Blackwell, NVIDIA Container Toolkit, and HAMi must be the sole MIG manager (dynamic-mig-support.md:11,23-26). It is not compatible with v2.9 `knownMigGeometries` (dynamic-mig-support.md:87,188).
  - `migProfileAllowlist` defaults per model: A30, A100 40/80GB, H100 80/94GB, H20, H200, B200, RTX PRO 6000 Blackwell (device-configmap.yaml:36-60). Example A30 profiles `1g.6gb, 2g.12gb, 4g.24gb`.
  - MIG mode change may need GPU reset or node reboot; cordon and drain first (dynamic-mig-support.md:54,217). Scheduler publishes `hami_node_gpu_mig_instance_info` (metrics.go:197).
  - Restart the scheduler and device plugin after config change (dynamic-mig-support.md:91).
- Viettel's framing: many of their GPUs (L40, L40S, A6000) have no MIG (kcd_vietnam.md:738,692); MIG is the "hard throughput isolation" option (kcd_vietnam.md:949). Comparison table: kcd_vietnam.md:572-581.

## 8. HAMi-DRA

- What it is: a Kubernetes mutating webhook that converts `nvidia.com/gpu` style requests into DRA ResourceClaims (references/HAMi-DRA/README.md:3,7).
- **Minimum Kubernetes**: **>= 1.34** with the DRA **Consumable Capacity** feature gate enabled (README.md:20). Ascend path: Kubernetes >= 1.34 with `DynamicResourceAllocation` and `DRAConsumableCapacity` (docs/ascend-dra.md:13). Prioritised fallback across DeviceClasses would use the `DRAPrioritizedList` gate (ascend-dra.md:79-80); this is a future item ("Later:", ascend-dra.md:76). Hygon: "same requirements as the main chart" (docs/hygon-hcu.md:9).
- Other prerequisites: CDI enabled in containerd/CRI-O; NVIDIA driver 440+ (README.md:21-22); cert-manager (README.md:26) or custom certs.
- Chart: `hami-dra` version/appVersion 0.2.3 (charts/hami-dra/Chart.yaml:18,24); webhook image tag `v0.2.3` (values.yaml:106). Install: `helm install hami-dra hami-dra/hami-dra` (README.md:36); not using GPU-operator containerd drivers: `--set drivers.nvidia.containerDriver=false` (README.md:47-48).
- **Supports today**:
  - NVIDIA: same resource names `nvidia.com/gpu`, `gpumem`, `gpucores` (README.md:65-67; values.yaml:14-17). DaemonSet `hami-dra-driver-kubelet-plugin` (templates/hami-dra-driver/nvidia-dra-driver-daemonset.yaml:6). DeviceClass `hami-core-gpu.project-hami.io` (templates/_helpers.tpl:227,235).
  - Hygon HCU: DeviceClass `dra.hygon.com`; needs the separate k8s-hcu-dra-driver (README.md:54-56; docs/hygon-hcu.md:5,10; values.yaml:26-30).
  - Ascend: HAMivNPUCore consumable-capacity sharing only. DeviceClass `hami-vnpu-core.project-hami.io`, driver `ascend.project-hami.io` (docs/ascend-dra.md:7,61-67; values.yaml:42-43). Chips: 910A/B2/B3/B4/B4-1/310P/910C (values.yaml:51-83).
  - Multi-vendor in one install: `deviceVendors: [nvidia, hygon, ascend]` (README.md:70-80; values.yaml:35-36).
  - Selection by pod annotations (UUID, device type) (README.md:13).
  - Optional `ResourceClaimTemplate` mode via `webhook.config.resourceClaimTemplate: true`; Kueue can admit this form but not claim-direct pods; Kueue needs `deviceClassMappings`; batch/v1 Jobs not covered yet (README.md:82-92).
  - Optional monitor (enabled by default) (README.md:14,94-113). Fake driver for testing without hardware (docs/fake-dra-driver.md).
  - Webhook failurePolicy default `Fail` (templates/webhook/mutatingwebhookconfiguration.yaml:34; values.yaml:141-143).
- **NOT FOUND**: GA/beta/alpha status statement for HAMi-DRA itself, and a ResourceQuota story for DRA mode.
- Viettel deck: "Move to DRA: keep the same isolation, swap the custom API for the standard Kubernetes one" (kcd_vietnam.md:1086). DRA ResourceClaim stable in K8s 1.34 (kcd_vietnam.md:149). Capability table (kcd_vietnam.md:572-581).

## 9. Viettel Cloud blueprint (kcd_vietnam.md)

Part 3 starts at kcd_vietnam.md:585.

- **Platform** (kcd_vietnam.md:593-623): "Viettel Cloud AI-Native" is the AI/GPU platform; AI Notebooks with fractional GPU for dev and training; also inference serving. Pools: "**H200** pool (141 GB), plus **L40, L40S, A30, A6000, ...**" (:623). Speaker note: "GPUs are MIXED: 1 pool H200 + pools L40/L40S/A30/A6000" (:599).
- **Version and clusters** (:660): "**HAMi v2.9** on **both clusters**: the H200 pool, and the mixed-GPU one". Neighbours: Slinky, Inference, KEDA (:663; note :653 "2 schedulers, no conflict").
- **Notebook sizes / SKUs**: NOT FOUND. The only size data:
  - Example request `nvidia.com/gpu: 1`, `gpumem: 2000`, `gpucores: 30` (:671-673).
  - Quote: "Our researchers do not write that - they pick the GPU size in our AI Notebooks, built on Kubeflow Notebooks" (:676).
  - A case measured at **~30% fence / 70% cores**, notebook 39 GB on a 141 GB H200 (:818). Daily pattern rows at :880-882 (notebook ~30% fixed, time-series x6 / LLM x5 / more training).
- **Quotas**: NOT FOUND as a current design. Only roadmap: "**More teams** inside Viettel, with quota per team" (:1083). (An older deck claimed per-user quota; it is not a reference: use kcd_vietnam.md only.)
- **Rollout steps**, "What It Really Took" (kcd_vietnam.md:998-1018):
  - Install is a Helm chart, not the hard part (:1003).
  - Obstacle/solution table (:1011-1016):
    1. HAMi privileged access vs Kyverno: exclude `hami-system` from the pod-security policies (:1013).
    2. `nvidia.com/gpu` is claimed by both the NVIDIA device plugin and HAMi: operator device plugin off, CDI off (:1014). Speaker note: HAMi needs the plain legacy runtime (:1005).
    3. Fractional, full-GPU and Slurm (Slinky) overlap: own pool, own scheduler, and a taint (:1015).
    4. HAMi 2.9 metrics refactor: dashboards go empty; use `hami_*`; docs fixed upstream (:1016).
  - Closing line: "It is an operations project, not a one-line install." (:1018).
- **Measured results**: 3.4x more work per GPU (:744); one pod ~18% SM, ~10 replicas to 100% SM, "~71% fewer cards, ~51% less power, ~$7k/month at an example $4/GPU-h" (:760-ish; speaker note :750). Slicing does not help when the job already fills the card: LLM one 11.6k tok/s vs four 7.3k (:983), training x4 = 0.77x (:984).
- **Operations gotchas** (:1073-1075): Alpine/musl images fail (libvgpu needs glibc, exit 127); MATLAB hangs; multi-GPU NCCL inside CUDA is fine.

## 10. DaoCloud D.run and CMB

**DaoCloud** (research/containerdays-sg-2026/case-studies.md:9-25; primary text research/containerdays-sg-2026/case-studies/daocloud.md):
- Products: D.run is the public GPU cloud for developers and small teams; DCE is the private enterprise Kubernetes platform (case-studies.md:13; daocloud.md:10).
- Scale: HAMi active on 10,000+ GPU cards, 7 D.run regions, 10+ data centers, regions up to ~3,000 GPUs (case-studies.md:14-15; daocloud.md:34,44-45).
- **SKU model**:
  - "Physical GPUs are partitioned into multiple vGPU slices with defined compute and memory" with "controlled over-subscription" (daocloud.md:39-40; case-studies.md:17).
  - "vGPU slices are exposed as standardized SKUs in a central marketplace. Users select GPU SKUs based on workload size rather than paying for a full card" (daocloud.md:41-42; case-studies.md:18).
  - Packaging was limited by whole-card allocation before HAMi (daocloud.md:13).
  - Sold-as-SKU flow in the draft: pool -> vGPU slices -> SKU catalog -> D.run marketplace / DCE quotas+RBAC (research/containerdays-sg-2026/drafts/containerdays_neocloud_a_blueprint.md:397-404).
  - Blueprint summary: analysis.md:82-89.
- **SKU sizes, SKU names, prices, over-subscription ratios**: NOT FOUND in any source.
- **Pool design (DCE)**: "central GPU pool; quotas + RBAC enforced at vGPU level (department and queue limits)" (case-studies.md:20; daocloud.md:17,53-54). Enterprises contribute and consume GPUs from a central pool for training and inference (daocloud.md:52). DaoCloud's own quota and RBAC system is integrated; this is not HAMi's quota (daocloud.md:54; analysis.md:60).
- Results: >80% average utilization per card, 20-30% lower GPU opex (case-studies.md:21). The case study gives no "before" number (drafts/containerdays_neocloud_a_blueprint.md:379).
- Quote at case-studies.md:23; DaoCloud contributed over-subscription, node config and heterogeneous hardware upstream (case-studies.md:22; daocloud.md:60-61).

**CMB, pool design** (research/containerdays-sg-2026/case-studies.md:27-56; case-studies/china-merchants-bank*.md). No explicit pool/SKU layout is documented.
- Part 1 (Jul 2026): without HAMi each hardware delivery would be its own cluster, 8+ clusters (case-studies.md:50); with HAMi, Kunlunxin, Ascend, NVIDIA, PPU, Moore Threads, MetaX run in one pool (drafts/containerdays_neocloud_b_evidence.md:246). Topology-aware paired allocation inside dual-chip modules gave 100% hardware pool utilization (case-studies.md:51); network-tier scoring cut cross-machine scheduling by 30% (case-studies.md:52). vNPU-Core granularity 1 GB memory / 1% compute (case-studies.md:53; china-merchants-bank.md:73).
- Part 2 (Sep 2026): ~10,000 heterogeneous cards, 99% under unified management (case-studies.md:31). Shared foundation: Kubernetes Scheduler, HAMi, Fluid, accelerator node pool, storage, model registry (china-merchants-bank-2.md:58). Kueue for training admission and quota; KEDA + Prometheus for inference (case-studies.md:32; china-merchants-bank-2.md:56). Avg utilization 35% -> 60%+ (case-studies.md:34).

## Verification notes

- Line numbers come from grep output; some read-tool outputs elide line numbers, so :N values in kcd_vietnam.md and a few values.yaml entries (e.g. kubeScheduler.enabled ~:130, libPath ~:453, the ~:760 "71% fewer cards" line) are approximate. Re-grep before putting a line number on a slide.
- NOT-WRITTEN notice: this content must be saved by the main agent, since no write tool was available.
