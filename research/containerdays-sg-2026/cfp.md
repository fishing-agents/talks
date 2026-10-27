# ContainerDays Singapore 2026: "10x Your Neocloud's GPU Utilization with HAMi"

Talk slot: Tuesday, October 27, 2026 (same day as the 12:30 HAMi workshop, `gpu_workshop.md`).
Format: 30-minute slot (per the speaker, 2026-10-26; earlier notes said 25), Cloud Native / AI Infrastructure. Plan ~25 min of content plus Q&A.

## CFP as submitted

### Title

10x Your Neocloud's GPU Utilization with HAMi

### Abstract

DRA gives Kubernetes a way to request fractional GPUs, but it does not solve the utilization problem by itself - the device still needs virtualization and a scheduler that knows how to share it. Hardware-agnostic GPU virtualization provides that layer: one scheduling layer shares NVIDIA, AMD, Ascend, and domestic NPUs under a single pool - fractional GPUs, mixed vendors, whatever hardware the supply chain delivers.

This talk covers how vGPU interception enforces memory and compute limits, how the scheduler allocates heterogeneous devices, how DRA fits (and where it falls short), and production patterns from cloud providers running 10,000+ GPUs.

No vendor pitch. A concrete blueprint for turning a GPU box into a GPU cloud.

### Benefits

- Neocloud blueprint: heterogeneous inventory as sellable fractional GPU capacity
- How sharing works: overhead expectations, best-fit workloads
- Production patterns from 200+ adopters
- Domestic chips as first-class citizens, no vendor lock-in

### Speaker bio

Reza Jelveh is Head of Global Market at Dynamia, the company behind HAMi, the CNCF Incubation project for hardware-agnostic GPU sharing on Kubernetes (200+ adopters, 4,200+ stars). He works with neoclouds and GPU vendors across APAC on production vGPU deployments.

## Suggested wording if the event site is still editable

The submitted text says "domestic" (reads as China-specific in Singapore) and "200+ adopters" / "4,200+ stars" (see claim check). Drop-in replacements:

Abstract, first paragraph:

DRA gives Kubernetes a way to request fractional GPUs, but it does not solve the utilization problem by itself - the device still needs virtualization and a scheduler that knows how to share it. Hardware-agnostic GPU virtualization provides that layer: one scheduling layer shares NVIDIA, AMD, Ascend, and other vendors' accelerators under a single pool - fractional GPUs, mixed vendors, whatever hardware the supply chain delivers.

Benefits:

- Neocloud blueprint: heterogeneous inventory as sellable fractional GPU capacity
- How sharing works: overhead expectations, best-fit workloads
- Production patterns from adopters running 10,000+ GPUs
- Every vendor's chips as first-class citizens, no vendor lock-in

Bio: Reza Jelveh is Head of Global Market at Dynamia, the company behind HAMi, the CNCF Incubating project for hardware-agnostic GPU sharing on Kubernetes (hundreds of enterprises in production, 4,900+ stars). He works with neoclouds and GPU vendors across APAC on production vGPU deployments.

## What the talk must deliver (promised in the abstract)

1. Why DRA alone does not fix utilization (request API vs virtualization + sharing scheduler)
2. How vGPU interception enforces memory and compute limits
3. How the scheduler allocates heterogeneous devices
4. How DRA fits, and where it falls short
5. Production patterns from cloud providers running 10,000+ GPUs
6. Overhead expectations and best-fit workloads
7. Every vendor's chips as first-class citizens (submitted wording: "domestic chips"; don't say "domestic" on stage)
8. A concrete blueprint: GPU box → GPU cloud (sellable fractional capacity)
9. "No vendor pitch": show limits and trade-offs, not only wins

## Claim check against sources

| Claim | Status | Evidence |
|---|---|---|
| "10x" utilization | Holds per workload, not platform-wide | NIO CI 5% → up to 50% (CNCF headline "10x"); CETC dev pods 2 → 30 (15x); Sangfor 8+ models/GPU. Platform-wide: Ke 13% → 37%, CMB 35% → 60%+, Sangfor >3x, SNOW 2x fewer GPUs, DaoCloud >80%/card. Frame: 10x is reachable where the baseline is 5-15%. |
| "cloud providers running 10,000+ GPUs" | Holds | DaoCloud: HAMi on 10,000+ cards, 10+ DCs, 7 D.run regions. CMB ~10,000 cards (bank, not a cloud provider). |
| "200+ adopters" | Not supported by public lists | Public list (`Project-HAMi/website` `src/data/adopters.json`, 2026-10-24): **74 named organisations**. CETC study: "running in production at hundreds of enterprises", "500+ contributors from 20+ countries". On slides: "74 public adopters, hundreds in production" or "hundreds of enterprises"; only say 200+ if Dynamia has an internal count to back it. |
| "4,200+ stars" | Understated | GitHub API on 2026-10-24: **4,929 stars**, 872 forks. "4,900+ stars" or "nearly 5,000" on slides. |
| "CNCF Incubation project" | Holds | CETC + CMB-2 studies (Sep 2026): "CNCF Incubating project". Workshop deck kicker also says "CNCF Incubating project". Older studies (2025) say Sandbox. |
| "NVIDIA, AMD, Ascend, and other vendors' NPUs" (submitted: "domestic NPUs") | Holds | CETC list: NVIDIA, Ascend, Cambricon, Hygon, Iluvatar CoreX, Moore Threads, MetaX, Enflame, Kunlunxin, AWS Neuron, Vastai. AMD: in website device table (per observability research), scheduler accounting only, no first-party tenant telemetry path. |
| "Every vendor's chips as first-class citizens" (submitted: "Domestic chips") | Holds | DaoCloud uses the same phrase. CMB: Kunlunxin, Ascend, PPU, Moore Threads, MetaX in one pool. |
| "Overhead expectations" | Data exists | CETC: throughput within 5%, p95 and load time unchanged. NIO: 1/6 GPU optimal, 1/8 lowered throughput. CMB: ResNet50 +46.7% total throughput with partitioning. |
| "No vendor pitch" | Needs showing, not saying | Include limits: soft isolation is not a security boundary (CUDA_DISABLE_CONTROL, static CUDA, direct ioctl), finer is not better (NIO), MIG for hard isolation (NIO), training stays on whole cards (Ke, CMB, CETC). |

## Note on the speaker role

CFP bio: Head of Global Market at Dynamia. Workshop deck: Solution Architect, Dynamia AI. Use the CFP role on the talk deck unless told otherwise.
