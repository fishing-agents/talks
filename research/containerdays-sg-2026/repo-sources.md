# Reusable material already in this repo

Everything below can be lifted into the ContainerDays talk deck. Paths relative to repo root.

> **Source rule:** `kcd_vietnam.md` (KCD Vietnam 2026, Viettel Cloud) is the source for our own measurements. Do NOT use `drawings.md` (a chart scratchpad copied from it, not data), `hami_intro.md` or `hami_enterprise.md` (older decks) as references.

## Own measurements (kcd_vietnam.md, Viettel Cloud)

- Two real jobs each held a whole H200 (141 GB): time-series inference used 1 GB, SM 16-18%; YOLO11 training used 39 GB → ~100 GB free.
- Throughput: native 20.7 req/s per card @ p95 160 ms → HAMi + KEDA 71.1 req/s (10 replicas) = 3.4x per card; SM 18% → 31% → 54% → 100% at 1/2/5/10 replicas, same latency. Same 71 req/s natively needs ~3.4 cards → ~71% fewer cards, ~51% less power, ~$7k/month at $4/GPU-h (example).
- Bigger batches did not help: batch 32 → 512, GPU still 7-10%.
- Notebook capping: 70% cores → 1h00 → 1h20 (+20 min, on purpose).
- One H200 across a day: notebook fixed ~30%; morning time-series x6; office hours LLM inference x5 (<20B); night more training.
- Stability (hidden backup slide): epoch-time CV 1% alone, 19% shared no cap, 9% shared with `force` cap. Caveat: cap isolates stability, not throughput; for hard throughput isolation use MIG.
- Charts for all of the above are seaborn blocks in `kcd_vietnam.md` (copy as-is).

## HAMi mechanism slides

- `ossummit_korea.md` (~line 253): compute slicing mechanisms per vendor (interception token bucket vs MPS/CU masking vs hardware-fenced vXPU/vDCU vs no hook point).
- `ossummit_korea.md` (~line 504): three pieces needed: capacity reporting, allocation, enforcement; DRA as the clean path.
- `ossummit_korea.md` (~line 770) / `coscup_2026.md` (~line 393): consumable resources (MiB, % of SMs); nvidia-smi in the pod shows the slice; same semantics on DRA since v2.8.
- `gpu_workshop.md` (~line 208): component list: scheduler extender, webhook, device plugin, HAMi-core (`libvgpu.so`), vGPUmonitor.
- `gpu_workshop.md` (~line 346): `libvgpu.so` via `ld.so.preload`.
- `gpu_workshop.md` (~line 428): "One isolation layer, several scheduling brains" + `assets/containerdays/containerdays-scheduling-brains.svg`; KAI resource-isolator delivers the same libvgpu.so.
- `gpu_workshop.md` (~line 502): DRA: HAMi-DRA mutating webhook rewrites `nvidia.com/gpu` into ResourceClaims; K8s 1.34+ with DRA Consumable Capacity + CDI; ResourceClaimTemplate mode for Kueue.
- Comparison tables MIG vs HAMi vs NVIDIA DRA: `coscup_2026.md` (~line 376), `kcd_vietnam.md` (~line 572).

## DRA images

- `assets/hami/device-plugin-vs-dra.png`
- `assets/hami/dra-resource-slice.png`
- `assets/hami/dra-resource-claim.png`
- `assets/hami/dra-feature-timeline.png`

## ContainerDays assets

- `assets/containerdays/containerdays-lab-architecture.svg`
- `assets/containerdays/containerdays-scheduling-brains.svg`
- `assets/containerdays/containerdays-reservation-usage.svg`
- `assets/containerdays/containerdays-webui-overview.png`, `containerdays-webui-nodes.png`
- `assets/qr-hami-repo.png` (title slide side image in the workshop deck)

## Other research

- `research/cross-platform-observability/`: allocation != usage; HAMi-DRA metrics are accounting; vendor telemetry gaps.
- `research/ossummit-europe-agents/followups.md`: `CUDA_DISABLE_CONTROL` bypass; soft slicing is not a security boundary.
- `kcd_vietnam.md`: Viettel Cloud AI notebook production blueprint.
- `snow_corp_cncf.md`: earlier SNOW Corp deck.

## Deck conventions (workshop deck, same event)

- `theme: kubecon_japan`, `footer: "ContainerDays 2026 Singapore"`, `paginate: true`, `size: 16:9`, `transition: fade`
- Title slide: `@variant dark`, `@side-image assets/qr-hami-repo.png`, kicker "ContainerDays 2026 Singapore · CNCF Incubating project", custom `.layout-title` gradient via `style:` block.
