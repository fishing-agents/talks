# Cross-case analysis for the talk

Sources: `case-studies.md` (11 CNCF case studies, 10 organisations), own measurements from the KCD Vietnam 2026 talk (`../../kcd_vietnam.md`).

## 1. Whole-card baselines: 5-20%, everywhere

| Org | Workload | Whole-card utilization |
|---|---|---|
| NIO | CI/testing | 5-10% |
| Ke Holdings | whole platform | 13% |
| Zhuoyu | dev envs (Codespaces), small inference | <15% |
| Sangfor | small models | 15-20% |
| PREP EDU | inference | 10-20% |
| CETC Cloud | embedding model | 12.5% of VRAM (8 GB of 64 GB) |
| Own measurement (H200) | time-series inference | 1 GB of 141 GB, SM 16-18% |

Slide use: "Seven organisations measured the same waste."

## 2. Multipliers: per-workload vs platform

| Org | Metric | Before → After | Factor |
|---|---|---|---|
| CETC | dev pods per device | 2 → 30 | 15x |
| NIO | CI GPU utilization | 5% → 30-50% | 4-10x |
| Sangfor | models per GPU | 1 → 8+ | 8x |
| Own (H200) | req/s per card @ p95 160 ms | 20.7 → 71.1 | 3.4x |
| Sangfor | GPU utilization | baseline → | >3x |
| Ke | platform utilization | 13% → 37% | 2.8x |
| SNOW | GPUs for train+inference | 2 → 1 | 2x |
| CMB | avg accelerator utilization | 35% → 60%+ | 1.7x |
| DaoCloud | avg per-card utilization | → >80% | (no baseline given) |
| Zhuoyu | allocation / utilization | → >95% / >55% | (no baseline given) |

Message: 10x is real where the baseline is 5-15% (CI, dev, notebooks, embedding, small inference). Whole platforms land at 2-3x because training already uses its cards.

## 3. What production users chose not to share

| Workload | Whole card | HAMi slice | MIG | Time-slicing |
|---|---|---|---|---|
| Large training | Ke, CMB, NIO, CETC | | | |
| Large LLM serving | CETC (text gen, 4 GPUs), Ke (H200/H100 cluster) | | | |
| Small / bursty inference | | Ke, Sangfor, DaoCloud, SF, PREP, NIO | | |
| Dev envs / notebooks | | CETC, Zhuoyu, own Viettel notebook | NIO (algorithm dev, strong isolation) | |
| CI / testing | | NIO, SF test cluster | | |
| Embedding / rerank | | CETC | | |
| Simulation | | NIO | | |
| Contention-tolerant | | | | NIO |

Rule of thumb: share what is small, bursty, interactive or latency-tolerant; keep big training and big LLMs on whole cards; MIG where you need hard isolation.

## 4. Sharing always comes with a scheduler

| Org | Scheduler / control | Role of HAMi |
|---|---|---|
| Sangfor | Volcano (gang, LWS) | GPU virtualization |
| SF Technology | kube-scheduler + Volcano | extender + webhook + isolation |
| Zhuoyu | Koordinator (ElasticQuota, Reservation, Gang, Device Share) | HAMi-Core isolation only |
| CMB | Kueue (training), KEDA (inference) | accelerator allocation |
| SNOW | KEDA (custom saturation metric) | GPU sharing in-pod |
| DaoCloud | own quota + RBAC | vGPU slices + over-subscription |

Quote (Sangfor): "GPU sharing without smart scheduling leads to suboptimal placement; scheduling without GPU virtualization leaves nothing to schedule."

Workshop deck already has this framing: `assets/containerdays/containerdays-scheduling-brains.svg` ("One isolation layer, several scheduling brains").

## 5. Overhead and granularity

- CETC: embedding at 8 GB / 20% compute → token throughput within 5%; p95 and load time essentially unchanged.
- NIO: 1/6 GPU best for simulation; 1/8 added scheduling + virtualization overhead, lower throughput. "Finer is not better."
- CMB: ResNet50 bs32, single card 64.6 → 94.8 img/s (+46.7%) with finer partitioning (more concurrent work).
- NIO: VRAM is the hard constraint (OOM can't wait); compute shortage can be absorbed by scheduling delay.
- Own (Viettel notebook): capping to 70% cores cost +20 min on a 1 h training run; jitter (epoch-time CV) 1% alone, 19% shared without cap, 9% with `force` cap.

## 6. Heterogeneous hardware = fewer clusters

- CMB: without HAMi, each accelerator delivery would be its own cluster → 8+ clusters, each with own plugin, scheduler policy, monitoring, runbooks.
- CMB topology: supernode paired allocation (odd cards across modules → driver errors) → 100% pool usable; 3-tier network scoring → cross-machine -30%.
- DaoCloud: NVIDIA + other vendors' accelerators under one abstraction; proprietary vGPU licensing avoided.
- SF: Ascend, Kunlun, Sunway.
- Vendor mechanism map (from `ossummit_korea.md` speaker notes): NVIDIA/Ascend no hardware compute cap → user-space interception (token bucket, 1%); AMD CU masking and NVIDIA MPS → hardware-honoured static caps; Kunlunxin vXPU / Hygon vDCU → hardware-fenced, coarse; DeepX/Axelera → no hook point.

## 7. Neocloud blueprint (DaoCloud D.run)

1. Slice cards into vGPU units with defined memory + compute
2. Package slices as SKUs in a marketplace; users buy by workload size
3. Controlled over-subscription to lift cluster utilization
4. Quotas + RBAC at vGPU level for enterprise tenants
5. One abstraction over NVIDIA + other vendors' cards; regions of up to ~3,000 GPUs; 7 regions, 10+ DCs
6. Results: >80% avg utilization per card, -20-30% GPU opex

Add from other cases: per-tenant accounting/observability (CMB, NIO roadmap), blue-green device plugin upgrades (NIO), proactive scaling on saturation (SNOW).

## 8. Honest limits (for "no vendor pitch")

- Soft isolation is a resource/fairness control for trusted workloads, not a security boundary: `CUDA_DISABLE_CONTROL=true` skips libvgpu.so preload; statically linked CUDA and direct `/dev/nvidia*` ioctls bypass the preload (`../ossummit-europe-agents/followups.md`).
- Interception can conflict with toolchains doing pointer/address analysis (NIO).
- Upgrades need performance validation; phased rollout (NIO).
- Allocation is not utilization: scheduler/DRA metrics are accounting, live usage needs a runtime collector (`../cross-platform-observability/`).
- Per-tenant telemetry is uneven across vendors (AMD: no first-party tenant path).
- DRA in production: no case study runs it yet (Sangfor lists it as future work). HAMi-DRA exists (v2.8+ semantics; webhook rewrites `nvidia.com/gpu` into ResourceClaims; K8s 1.34+ with consumable capacity gate).

## 9. APAC angle

SNOW Corp (Korea, 1,000+ A100s), PREP EDU (Vietnam, on-prem RTX), DaoCloud (Hong Kong regions), own Viettel Cloud work (Vietnam). Rest are China.
