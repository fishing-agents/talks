<!-- source: https://www.cncf.io/case-studies/zhuoyu-technology/
     published: 2026-09-29T11:00:00+00:00
     fetched: 2026-10-24 -->

# Zhuoyu Technology

## How Zhuoyu Technology Pushed GPU Allocation Above 95% on Kubernetes with Koordinator
Zhuoyu Technology’s driving cloud runs its autonomous-driving data pipelines on Kubernetes and gives algorithm and data engineers GPU-backed development environments (internally called Codespaces). Under the default scheduler, bursty multi-tenant submissions, GPU/CPU fragmentation, and distributed jobs that could not start all their pods together capped both allocation and utilization. The team extended the scheduler with Koordinator’s ElasticQuota, Reservation, Device Share, and Gang Scheduling, pairing Device Share with HAMi for runtime GPU isolation. With those in place, the platform governs 100+ ElasticQuotas and schedules 300K–800K pods per day. GPU allocation now exceeds 95%, overall utilization exceeds 55%, and Codespaces need roughly 60% fewer whole GPU cards.

#### About Zhuoyu Technology
Zhuoyu Technology supplies autonomous-driving systems and self-developed core components. Around a closed data loop, it built a driving cloud whose data production, model training, model evaluation, and model inference stages form a continuously iterating “data flywheel,” shared by more than ten algorithm, data, and platform teams. Koordinator has been the platform’s core scheduling engine for two years, handling multi-tenant governance and denser GPU packing.

### Challenge
Four problems dominated production:
- Unfair multi-tenant contention. Bursty submissions and hard ResourceQuota limits caused failed launches and low allocation; teams had no weighted borrowing across quotas.
- Stranded GPUs. CPU-only pods consumed CPU/memory on GPU nodes and left expensive GPUs unschedulable, while GPU jobs often left nearly half of a node’s CPU/memory idle.
- Low GPU utilization. Codespaces used daily by algorithm and data engineers, together with small-model inference, often ran below 15% utilization when given whole cards—idle most of the time during debugging, with per-request demand far smaller than a full card.
- Distributed deadlocks. Distributed jobs need multiple pods ready together; pod-by-pod scheduling left some pods holding resources while their peers stayed Pending.

#### Why Kubernetes and Koordinator
Native Kubernetes offers hard ResourceQuota, pod-by-pod binding, and whole-device GPU allocation—but not weighted borrowing across tenants, GPU-aware reservation of leftover CPU/memory, fractional GPU sharing, or all-or-nothing binding for distributed jobs. Koordinator adds those four as scheduler extensions without changing the cluster API, while HAMi-Core enforces runtime compute and memory limits for shared GPUs. The team turns production findings into upstream fixes: since 2023, more than ten of its pull requests have merged into Koordinator, including scheduler awareness of HAMi-Core availability on nodes ( #2577 ) and vGPU allocation and utilization metrics ( #2578 ).

### Solution: ElasticQuota for fair borrowing
A two-level tree separates quota-groups (by GPU type or business criticality) from leaf business quotas. Groups do not borrow from each other and are pinned to nodes via labels. Within a group, leaf quotas can borrow idle capacity beyond their guaranteed Min; when demand conflicts, Max determines each share. If quota A’s Max is twice quota B’s, A receives roughly twice the borrowed capacity. An auto-labeling burst can use only idle GPUs in its group, never GPUs protected for another training group. Each GPU business quota is also split into .gpu and .cpu, so CPU pods cannot exhaust GPU scheduling capacity. Idle resources therefore flow among businesses within a controlled pool, while protected pools remain isolated.
Figure 1: Quota-groups isolate resource pools; leaf quotas borrow within a group and split GPU and CPU demand. Reservation to raise GPU-node packing safely
On 8-GPU / 224-CPU nodes, Reservation holds CPU/memory for GPU pods so CPU workloads can fill leftover capacity without blocking later GPU placements—effectively carving out a virtual CPU pool (about 112 cores / 500Gi, tuned to GPU job shapes) without buying more CPU-only machines.
Figure 2: Reservation protects CPU/memory for GPU pods while CPU workloads fill leftover capacity.
Device Share + HAMi for GPU slicing and isolation
Fractional GPUs follow a four-step path: the pod requests gpu-core and gpu-memory-ratio; koord-scheduler’s Device Share plugin binds a slice; koordlet injects device env vars into the CRI Runtime via NRI rather than into the container; HAMi-Core (libvgpu.so, mounted by hami-daemon) intercepts CUDA API calls and enforces memory and compute limits before forwarding them to the NVIDIA driver. Co-located tasks stay within their assigned limits, allowing Codespaces and small-model inference to share cards instead of holding them.
Figure 3: Device Share places a GPU slice; HAMi-Core intercepts CUDA API calls and enforces runtime limits.

### Impact
Gang Scheduling for all-or-nothing jobs
The workload controller creates Head and Worker pods with the same gang name and min-available count. Koord-scheduler recognizes those annotations, selects a node for each pod, and holds it at the Permit stage instead of binding it immediately. Once enough gang members have valid placements to meet min-available, the scheduler releases the group for binding. If the threshold is not met before the timeout, it rolls back all assumed pods. A distributed job therefore either secures enough resources to start or releases its temporary reservations, preventing some pods from occupying GPUs while their peers remain pending.

#### Results
| Metric | Results |
| ElasticQuota objects | 100+ per cluster |
| Scheduling throughput | 300K~800K pods/day |
| GPU allocation | > 95% |
| GPU utilization | > 55% overall; ≈ 60% on shared inference |
| Codespace GPU cards | ≈ 60% fewer whole cards |
How these are measured. GPU allocation is scheduled GPU cards divided by schedulable GPU cards, excluding failed devices. GPU utilization is mean SM utilization reported by node telemetry, measured across the cluster and separately on shared-inference nodes. Codespace savings compare whole-card demand before and after Device Share.

#### Looking Ahead
Compute demand grows with the business, and scheduler throughput and precision increasingly bound the whole pipeline’s SLA. Four priorities follow: ElasticQuota reclaim that respects the atomicity of distributed jobs, workload-level queuing to tame Pending spikes, scheduler sharding to break the serial-scheduling ceiling, and multi-cluster / hybrid-cloud scheduling for bursty AI demand. The team will evaluate relevant Koordinator community features against these production scenarios and report the results back to the community.
Projects used
By the numbers
95%
GPU allocation
55%+
overall GPU utilization
~60%
fewer whole GPU cards for Codespaces
Share
