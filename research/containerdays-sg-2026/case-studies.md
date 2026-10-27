# HAMi CNCF case studies: per-study notes

Source listing: https://www.cncf.io/case-studies/?_sft_lf-project=hami
Read: 2026-10-24. 11 case study pages, 10 organisations (China Merchants Bank has two).
All numbers below are as stated by the case study; units and measurement method noted where given.

---

## 1. DaoCloud (Dec 2, 2025)

https://www.cncf.io/case-studies/daocloud/

- **Type:** GPU cloud provider. D.run = public GPU cloud for developers/small teams; DCE = private K8s platform for enterprises.
- **Region:** Mainland China + Hong Kong. 7 active D.run regions, 10+ data centers.
- **Scale:** HAMi active on **10,000+ GPU cards** (DaoCloud-operated + customer-owned). Single regions up to ~3,000 GPUs.
- **HAMi use:**
  - vGPU slicing with defined compute + memory; **controlled over-subscription**
  - vGPU slices exposed as **standardized SKUs in a central marketplace**; users pay by workload size, not full card
  - Non-NVIDIA GPU vendors supported under the same abstraction ("first-class citizens")
  - DCE: central GPU pool; **quotas + RBAC enforced at vGPU level** (department and queue limits)
- **Results:** **>80% average GPU utilization per card**; **20-30% lower GPU-related opex**; faster regional expansion / cluster delivery.
- **Other:** One of HAMi's earliest contributors (over-subscription, node config, heterogeneous hardware upstream).
- **Quote (paraphrase for stage):** with HAMi's unified vGPU abstraction, D.run manages NVIDIA and other vendors' GPUs at scale (Captain, AI/LLM Infra Product Lead). Verbatim wording in case-studies/daocloud.md; don't quote it on stage.
- **Talk relevance:** this IS the neocloud blueprint (SKUs, marketplace, over-subscription, multi-region).
- Note: case study calls HAMi "CNCF Sandbox" (pre-incubation).

## 2. China Merchants Bank, part 2 (Sep 7, 2026)

https://www.cncf.io/case-studies/china-merchants-bank-2/

- **Type:** Bank, private platform. **~10,000 heterogeneous accelerator cards.** 99% of accelerator compute under unified management.
- **Stack:** Kubernetes, **Kueue** (training admission/quota), **KEDA + Prometheus** (inference autoscaling), **HAMi** (shared accelerator allocation), **Fluid** (dataset/model/checkpoint cache), Twinkle on Ray (multi-tenant LoRA training), vLLM/SGLang on Ray (inference).
- **Results (internal consistent before/after method):**
  - Avg accelerator compute utilization **35% → 60%+**
  - Inference cost per 1M tokens (input+output) **-60%+**
  - 5 LoRA tenants share 1 base model: **5x training density, -80% accelerator usage** (8 tenants validated)
- **Lessons:**
  - Same control plane, different policies: Kueue for training, KEDA for inference
  - Inference elasticity depends on model load speed (Fluid)
  - "Compute sharing and model sharing solve different problems" (HAMi vs Twinkle)
  - "The improvement ... cannot be attributed to any single component"
- **Quote:** "The real challenge was not a lack of accelerator capacity, but finding a way to use our existing heterogeneous resources more effectively." (PeiXiang Tan)
- States HAMi and Fluid are **Incubating** projects.

## 3. China Merchants Bank, part 1 (Jul 2, 2026)

https://www.cncf.io/case-studies/china-merchants-bank/

- **Hardware mix:** Kunlunxin, multiple Ascend models, NVIDIA, PPUs, Moore Threads, MetaX, others.
- **Without HAMi:** each hardware delivery would get its own K8s cluster → **8+ separate clusters**, each with own device plugin, scheduling policy, monitoring, runbooks.
- **Topology-aware scheduling:** supernode (dual-chip module) architecture. Odd-card allocation across modules caused **driver errors**; cross-module latency higher. Enhanced HAMi device plugin + scheduler to enforce **paired allocation within a module** → **100% hardware pool utilization** (previously parts unusable).
- **Network topology:** 3 tiers (same node / same LEAF / cross LEAF) scoring → **cross-machine scheduling -30%**. Controller-UID deterministic hashing to keep a batch's pods together.
- **vNPU-Core (user-space partitioning):** token bucket for compute quota + user-space memory management. Granularity **1 GB memory / 1% compute**.
- **Benchmark:** ResNet50 inference, batch 32: single-card throughput **64.6 → 94.8 images/s (+46.7%)** with finer partitioning.
- **Open issues (their roadmap):** reduce performance variability of Ascend vnpu-core under multi-workload; vNPU monitoring.
- **Use case for sharing:** risk control and customer service models are small.

## 4. Sangfor (Sep 8, 2026)

https://www.cncf.io/case-studies/sangfor/

- **Type:** Enterprise cloud + security vendor; internal AI platform for 2,000+ R&D engineers (AI coding, digital employees, customer service, sales agents).
- **Stack:** Kubernetes + **Volcano** (job scheduling) + HAMi (GPU virtualization); NVIDIA + Ascend.
- **Before:** 1 card = 1 model; small models used **15-20%**; GPUs scaled faster than business.
- **Pattern:** large/small model co-location on one card (e.g. large model 70%, rest to small models).
- **Results:** GPU utilization **>3x**; **models per GPU 1 → 8+**; inference that needed 3 GPUs fits on 1-2; external model invocation cost **400K → 200K RMB/month** (combined with smart routing); failure recovery ~1 h → <10 min; 3x peak traffic success 95%+.
- **Granularity claims:** memory 256 MB (also says 1 MB elsewhere), compute 1%.
- **Lessons:**
  - "GPU Sharing Matters More Than Adding GPUs"
  - "GPU sharing without smart scheduling leads to suboptimal placement; scheduling without GPU virtualization leaves nothing to schedule."
  - Kubernetes is becoming the AI resource control plane
- **Future:** join HAMi **DRA** ecosystem; extend Ascend support.
- **Quote:** "HAMi's Kubernetes-native integration means zero migration cost." (Jia Haojie, Chief Architect of Cloud AI)

## 5. SNOW Corp. (May 5, 2026)

https://www.cncf.io/case-studies/snow-corp/

- **Type:** Consumer GenAI (NAVER subsidiary), **South Korea**. SNOW, EPIK, B612; **200M+ users**.
- **Scale:** **1,000+ A100s**, 1,200+ AI workflows, 400+ models. Multi-region on-prem K8s + CSP bursting.
- **HAMi use:** trainer and inference engine **share one GPU within the same pod** (sequential train-to-inference pipelines). Unblocked the K8s migration without re-architecture.
- **KEDA:** custom "consumer saturation" metric (`unacked_messages / active_consumers`, threshold ~0.7) to scale ahead of ~60 s model warm-up.
- **Results:** handled **700% viral traffic spikes** ("Ghibli filter" trend, 3x traffic in 3 hours); **2x fewer GPUs** for training + inference pipelines; MTTR -91% (2 h → 10 min); surge errors -85%; avg GPU usage time -55%; USD 17.4M estimated savings vs on-demand cloud (USD ~45/h per A100).
- **Attribution:** most cost savings are KEDA autoscaling; HAMi credited for GPU sharing and avoiding re-architecture.

## 6. NIO (Mar 17, 2026)

https://www.cncf.io/case-studies/nio/

- **Type:** Autonomous driving. ~600 GPUs / ~80 nodes; HAMi on 50-70 nodes (~400-560 GPUs).
- **Partly public cloud with time-based billing** → wasted GPU-hours = direct cost.
- **Workloads and baselines:**
  - CI/testing: mostly CPU (compile, fetch, preprocess); GPU util **5-10%** on full GPUs
  - Simulation: low compute, not latency-sensitive
  - Small inference: needs 1/4 or 1/2 GPU
- **Hybrid strategy (important):**
  - **MIG:** algorithm development, strong isolation
  - **HAMi:** CI, selected inference and simulation
  - **Time-slicing:** contention-tolerant workloads
  - Large training: full GPUs
- **Resource design:** VRAM is the primary constraint (OOM can't be deferred; compute shortage can).
- **Finding:** **finer is not better** — ~1/6 GPU optimal for simulation; 1/8 added scheduling/virtualization overhead and reduced throughput.
- **Results:** CI util **5% → 30-50%** ("~4x" in text, "10x" in headline box); simulation GPU-hours **-30%**; simulation end-to-end 3 days → 2 days.
- **Ops lessons:** validate performance on version upgrades (phased, mixed versions allowed); blue-green style device plugin upgrades for inference; **some compiler/library features (pointer/address analysis) conflict with GPU interception**.
- Acknowledges HAMi "introduces some overhead compared to full GPU allocation."

## 7. Ke Holdings (Feb 5, 2026)

https://www.cncf.io/case-studies/ke-holdings-inc/

- **Type:** Housing platform, centralized ML platform team (AIStudio).
- **Scale:** 5 clusters, public (Volcano Engine, Tencent, Alibaba) + private (~1,000 NVIDIA GPUs); thousands of GPUs (H200, H20, V100, 4090, H100, A100); **10,000+ pods**; 10M+ requests/day.
- **Baseline:** overall GPU utilization **13%**.
- **Dual-cluster design:**
  - GPU clusters (native NVIDIA device plugin, H200/H100): large LLM + training, whole GPUs
  - vGPU clusters (HAMi, H20/V100/A100/4090): small model inference, typically **1-2 GB VRAM per service**
- **Results:** utilization **13% → 37% (~3x)**; zero downtime during transition.
- **Future:** Ascend and other non-NVIDIA; topology awareness, card-type and UUID allocation.

## 8. Zhuoyu Technology (Sep 29, 2026)

https://www.cncf.io/case-studies/zhuoyu-technology/

- **Type:** Autonomous driving systems; "driving cloud", 10+ teams.
- **Primarily a Koordinator story.** HAMi-Core (libvgpu.so) provides runtime compute + memory isolation under Koordinator's Device Share.
- **Flow:** pod requests gpu-core + gpu-memory-ratio → koord-scheduler Device Share binds slice → koordlet injects env via NRI → HAMi-Core intercepts CUDA, enforces limits.
- **Baseline:** Codespaces (dev envs) + small-model inference **<15%** util on whole cards.
- **Results:** 100+ ElasticQuotas; 300K-800K pods/day; **GPU allocation >95%**; **utilization >55% overall, ~60% on shared inference**; **Codespaces need ~60% fewer whole cards**.
- **Measurement definitions (useful):** allocation = scheduled cards / schedulable cards; utilization = mean SM util from node telemetry.
- Upstream Koordinator PRs: scheduler awareness of HAMi-Core availability (#2577), vGPU allocation/utilization metrics (#2578).

## 9. CETC Cloud (Sep 8, 2026)

https://www.cncf.io/case-studies/cetc-cloud/

- **Type:** Portable intelligent knowledge base appliance (edge / on-site), 8 heterogeneous GPUs in one device.
- **Workloads:** text generation (long-running, latency-sensitive), embedding (bursty bulk import), rerank (frequent, short), knowledge processing (batch), dev pods (interactive).
- **Design:** resource profiles per workload type, not one fixed ratio. Text generation keeps **4 GPUs exclusive**; embedding + rerank 8 GB VRAM quota each; dev pods share via HAMi.
- **Results:**
  - Dev capacity **2 → 30 concurrent dev pods (15x)** on the same device
  - Embedding: whole 64 GB card → **8 GB allocation**; **56 GB (87.5%) VRAM reclaimed**; **20% compute allocated, 80% freed**
  - **Token throughput within 5%** of whole-card; **p95 latency and model load time essentially identical**
- **Lessons:** start from workload profiles, not a preset partition ratio; dev environments are a major consumer of shared GPUs.
- **HAMi facts stated:** "now a CNCF Incubating project"; supports NVIDIA, Ascend, Cambricon, Hygon, Iluvatar CoreX, Moore Threads, MetaX, Enflame, Kunlunxin, AWS Neuron, Vastai; integrates Volcano, Kueue, Koordinator, vLLM, KAI Scheduler; **500+ contributors from 20+ countries/regions**; production at **hundreds of enterprises**.

## 10. SF Technology (Sep 18, 2025)

https://www.cncf.io/case-studies/sf-technology/

- **Type:** Logistics (SF Express tech arm).
- **Product:** in-house **EffectiveGPU** built on HAMi (adds cross-node scheduling, adaptive scheduling for non-NVIDIA accelerators, memory over-subscription, preemption/recovery).
- **HAMi capabilities used:** device virtualization, hard isolation, heterogeneous (Ascend, Baidu Kunlun, Sunway), **priority-based compute preemption** (low priority suspended while high priority computes), scheduler extender + webhook for kube-scheduler and Volcano, zero app changes.
- **Results:**
  - Production inference: **65 services on 28 GPUs** (saved 37)
  - Test cluster: **19 services on 6 GPUs** (saved 13)
  - "Up to 57% GPU savings", "up to 100% utilization improvement", **0 changes** to driver/kernel/image/source.

## 11. PREP EDU (Aug 20, 2025)

https://www.cncf.io/case-studies/prep-edu/

- **Type:** EdTech, **Vietnam**, on-prem. RTX 4070 + RTX 4090; RKE2 + NVIDIA GPU Operator.
- **Baseline:** GPU util **10-20%** with static allocation.
- **Prior attempt:** other sharing solutions without isolation → resource conflicts, memory allocation issues, **app crashes**.
- **HAMi use:** per-service limits by NLP token length; GPU-type pinning via annotations; **UUID pinning**; coexists with GPU Operator (containerd).
- **Results:** 1 year in production; HAMi manages **90% of GPU infra**; **memory-conflict crashes eliminated**; "50% reduction in GPU management pain points".
- **Quote:** "Deployment is practically 'plug-and-play' a Helm chart and a couple of labels." (Vu Hoang Tran)
- **Talk relevance:** small APAC on-prem team, consumer GPUs — relatable for SG audience.
