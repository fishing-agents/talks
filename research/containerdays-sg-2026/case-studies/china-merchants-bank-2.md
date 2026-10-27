<!-- source: https://www.cncf.io/case-studies/china-merchants-bank-2/
     published: 2026-09-08T00:00:00+00:00
     fetched: 2026-10-24 -->

# China Merchants Bank
China Merchants Bank is one of China’s leading commercial banks and has invested extensively in cloud native technologies, artificial intelligence, and digital infrastructure. As AI adoption expanded across more financial use cases, its platform needed to support large-model training, fine-tuning, online inference, and other AI workloads across nearly 10,000 heterogeneous accelerator cards.
At this scale, simply adding accelerator cards would not solve the platform-efficiency problem. Training requires stable capacity and high throughput, inference must respond quickly to changing traffic, and multi-tenant fine-tuning must isolate tenant state without repeatedly loading the same large base model. The bank needed to use existing capacity more efficiently while preserving workload isolation, operational control, and the ability of training and inference to evolve independently.
The bank built a unified control plane on Kubernetes while preserving two decoupled execution paths. Both workload types run in Pods managed by Kubernetes Deployments and use Ray as the distributed runtime: Twinkle handles multi-tenant training, while vLLM or SGLang serves online inference.
At the workload-control layer, Kueue manages training queues, quotas, and admission; Prometheus and KEDA scale inference services from live demand signals; HAMi schedules and allocates shared accelerator capacity; and Fluid accelerates access to datasets, model weights, and checkpoints.
After the redesign, average accelerator compute utilization across the platform increased from 35% to more than 60%. For comparable models and services, inference cost per 1M tokens (input and output combined) fell by more than 60%. In the default configuration, five LoRA tenants share one base-model instance, increasing training density fivefold and reducing base-model replicas from five to one.
“The real challenge was not a lack of accelerator capacity, but finding a way to use our existing heterogeneous resources more effectively. Training and inference share the same infrastructure, but they require very different operating policies.”
— PeiXiang Tan, AI Infrastructure Architect, China Merchants Bank
| Field | Value | Field | Value |
| Industry | Financial Services | Location | China |
| Platform | Enterprise AI training and inference | Scale | Nearly 10,000 heterogeneous accelerator cards |
Projects used: Kubernetes, Kueue, KEDA, Prometheus, HAMi, Fluid, and Twinkle

# By the Numbers
| 35% → 60%+ | 60%+ | 5× |
| Average accelerator compute utilization | Lower cost per 1M tokens (input and output combined) | Higher multi-tenant training density |

# Challenge
The issue was not simply low utilization. Training and inference consume the same resources in fundamentally different ways.

## Training Needs Stable, Predictable Resources
Distributed training jobs are typically long-running and throughput-oriented. They can begin useful work only after all required workers and accelerator cards are ready. Without quota-aware admission, some Pods may start early and hold capacity idle while waiting for the remaining resources. At the same time, datasets and model weights must move between centralized storage and compute nodes; when data is not ready, allocated accelerators wait.

## Inference Must Follow Traffic
Online inference behaves in the opposite way. Request volume changes with business traffic, and response latency matters more than batch throughput. Reserving accelerator cards for peak load leaves capacity idle during quiet periods. Scaling down reduces waste, but when traffic returns, new replicas must reload model weights before they can serve requests. If startup time is slow or unpredictable, the platform team must keep extra replicas running, which raises the unit cost per token.

## Fine-Tuning Needs Isolation Without Duplicating the Base Model
LoRA fine-tuning updates only a small set of parameters, yet the conventional one-tenant-per-deployment model still loads a complete base-model runtime for every tenant. Five tenants fine-tuning the same model therefore create five copies of the base model even though only their smaller adapters differ. Tenant state is isolated, but memory is consumed repeatedly and runtime initialization is duplicated.
A shared compute pool therefore requires distinct workload policies and separate mechanisms for physical accelerator sharing and model-runtime reuse.

# Solution

## Why a Composable Cloud Native Stack
China Merchants Bank pursued an in-house platform strategy, using Kubernetes as the foundation and combining several CNCF projects into a unified training-and-inference capability. This approach lets training and inference use the engines and policies best suited to each workload while sharing the control plane, resource layer, data path, and monitoring system.
The decision rested on three principles:
· Independent evolution: Training frameworks, inference engines, and models change at different rates and should not be tightly coupled.
· Hardware flexibility: Kubernetes and HAMi provide a common management entry point for shared, heterogeneous accelerator cards, reducing dependence on a single vendor’s closed stack.
· Open integration: Kueue, KEDA, Prometheus, HAMi, and Fluid connect through Kubernetes-native interfaces without requiring one product to own the entire model lifecycle.
The shared foundation is built largely from CNCF-hosted projects. Kubernetes, KEDA, and Prometheus are Graduated projects. Kueue is maintained by Kubernetes SIG Scheduling. HAMi and Fluid are Incubating projects.

## Implementation and Collaboration
Through close collaboration with the bank’s data center and other internal teams, China Merchants Bank brought 99% of its accelerator compute resources under unified management through this framework and achieved strong operational results.

## Architecture: Shared Infrastructure, Decoupled Runtimes
Figure 1. Kubernetes-native unified training and inference architecture.
The architecture shares resources at the infrastructure layer while treating training and inference separately at runtime.
At the workload layer, the Training API submits work to Pods managed by the Training Deployment, where Twinkle runs training on Ray. The Inference Gateway routes online requests to Pods managed by the Inference Deployment, where vLLM or SGLang serves inference on Ray.
Both paths rely on the same underlying capabilities. Kueue and KEDA handle training admission and inference elasticity, respectively. Kubernetes Scheduler and HAMi place Pods and allocate accelerator capacity. Fluid provides access to data and models, while Prometheus collects operational metrics. Beneath that layer, a shared accelerator node pool and Fluid Cache Runtime connect to object storage and the model registry.
| Dimension | Training path | Inference path |
| Demand pattern | Long-running, batch-oriented, throughput-sensitive | Bursty, latency-sensitive, request-driven |
| Entry point | Training API | Inference Gateway |
| Primary control | Kueue admission and quota management | Prometheus metrics and KEDA autoscaling |
| Runtime | Twinkle on Ray | vLLM or SGLang on Ray |
| Shared foundation | Kubernetes Scheduler, HAMi, Fluid, accelerator node pool, storage, and model registry | Kubernetes Scheduler, HAMi, Fluid, accelerator node pool, storage, and model registry |
| Primary outcome | Higher multi-tenant training density | Lower inference cost per token |
The improvement in accelerator utilization cannot be attributed to any single component; it comes from the interaction of admission, scheduling, allocation, data access, and runtime reuse.

## Training Path: Multi-Tenant Training with Twinkle on Ray
Training requests pass admission control before compute and data resources are provisioned:
| Training API |
| → Kueue admission and quota |
| → Kubernetes Scheduler |
| → HAMi accelerator allocation |
| → Fluid dataset and checkpoint access |
| → Twinkle on Ray |
| → Checkpoint and model registration |
Kueue first decides whether a job can enter the cluster based on queues and quotas, preventing some Pods from starting early and then waiting indefinitely for the remaining resources. After admission, Kubernetes Scheduler selects the nodes and HAMi assigns the required accelerator capacity. Through Kubernetes-native data abstractions and compute-side caching, Fluid reduces repeated reads from centralized storage so accelerators spend less time waiting.
Twinkle runs inside the Training Pod and executes training on Ray, with support for Transformers or Megatron backends. In multi-tenant LoRA scenarios, tenants share one base-model instance while retaining separate adapters, training configurations, and state. By default, five tenants share one base model. Compared with separate deployments, the number of base-model replicas falls from five to one and the accelerator resource usage is reduced by 80%.
As a result, the number of concurrent training tenants supported by one base-model instance increases fivefold. The platform has validated eight concurrent tenants and uses five tenants by default in production.
After training, Twinkle passes checkpoints to the downstream model-management process. Fluid accelerates checkpoint movement between storage and compute, while the model registry records the model version, adapter, and tokenizer for evaluation and deployment.

## Inference Path: Elastic Serving with KEDA, HAMi, and Fluid
The inference path begins with an online request:
| Inference Gateway |
| → vLLM or SGLang on Ray |
| → Prometheus service and demand metrics |
| → KEDA scaling decision |
| → Kubernetes Scheduler and HAMi allocation |
| → Fluid model-cache access |
Prometheus collects QPS, request-queue depth, inference latency, and other key metrics exposed by the serving framework. KEDA uses these signals to decide when to add or remove replicas. When the service scales out, Kubernetes schedules new Pods, HAMi allocates suitable accelerator resources, and Fluid supplies cached model weights.
Each component removes a different source of overhead:
· KEDA adjusts the replica count in response to demand, reducing idle capacity during quiet periods.
· HAMi allocates accelerator capacity in fine-grained units for workloads that can share it, preventing small or volatile services from monopolizing a full card.
· Fluid caches model weights near compute, shortening the time required to load a new replica.
· Prometheus supplies the real-time metrics that allow scaling decisions to reflect actual demand and service objectives.
Demand-driven elasticity, fine-grained accelerator allocation, and faster model loading work together to lower inference cost.

## A Unified Model Lifecycle
Although training and inference use different operating policies, they connect through the same model lifecycle:
| Training |
| → Checkpoint |
| → Evaluation and registration |
| → Production deployment |
| → Online monitoring |
| → Iterative optimization |
Training data and checkpoints reside in object storage or dataset storage, with Fluid providing unified access and caching. Twinkle produces model or adapter checkpoints, which are evaluated and registered in the model registry. Inference services then load the selected version through Fluid. Prometheus continues to collect production metrics, informing capacity changes and the next iteration of the model.
Unified training and inference therefore means more than placing both workloads in the same Kubernetes cluster. It means sharing resource management, data movement, model versions, and online feedback.

# Impact
| Metric | Result |
| Average accelerator compute utilization | 35% → 60%+ |
| Inference unit cost | More than 60% lower per 1M tokens (input and output combined) |
| Multi-tenant training density | 5× higher; 80% lower accelerator resource usage in the five-tenant configuration |
| Base-model replicas | Reduced from five to one for five default LoRA tenants |
| Concurrency validation | Eight tenants validated; five tenants used by default in production |
Table 2. Key outcomes reported by the platform team.

## Average Accelerator Compute Utilization: 35% → 60%+
Using the same internal measurement method before and after the redesign, average accelerator compute utilization across nearly 10,000 heterogeneous cards increased from 35% to more than 60%. Kueue reduced premature and fragmented resource reservation by training jobs, HAMi improved allocation granularity, and Fluid shortened waits for data and model weights. The result reflects improvements across the entire resource path.

## Inference Cost per 1M Tokens: Down 60%+
Under comparable model and service conditions, the cost of processing one million tokens, counting input and output combined, decreased by more than 60%. Unit cost is a more useful measure than total spend because it reflects efficiency as business volume grows.

## Accelerator Resource Usage: Down 80%
Using a DeepSeek base model, Twinkle’s default configuration allows five LoRA tenants to share one base-model instance. Reducing base-model replicas from five to one cuts accelerator resource usage for this setup by 80%, while increasing training density fivefold.
“Through close collaboration with our data center and other internal teams, we brought 99% of our accelerator compute resources under unified management through this framework. The results were measurable: average accelerator compute utilization increased from 35% to more than 60%, while inference cost per one million tokens decreased by more than 60%.”
— MeiQing Zhang, Head of the Architecture Management Team, China Merchants Bank

## Lessons Learned

### Preserve Different Operating Policies Under One Control Plane
Training and inference both require unified resource management, but they should not use the same policy. Queue- and quota-based admission through Kueue is well suited to training workloads, while metric-driven scaling through KEDA is well suited to online inference. Unified training and inference should standardize the shared infrastructure without erasing the differences between workloads.

### Inference Elasticity Depends on Fast Model Readiness
A scale-out command does not make inference capacity immediately available. A new replica can accept requests only after its model weights are loaded. Model-loading speed is therefore part of inference elasticity, not merely a storage optimization. Fluid’s compute-side cache shortens that loading time.

### Compute Sharing and Model Sharing Solve Different Problems
HAMi determines how physical accelerator capacity is allocated. Twinkle determines how multiple LoRA tenants reuse one base model. The first reduces wasted compute capacity; the second removes redundant runtimes. Neither replaces the other.

### Use Consistent Metrics to Measure Benefits Accurately
Accelerator compute utilization, cost per token, and training density measure different problems. Defining the scope and method for each metric makes results easier to verify and more useful to other organizations.

## Why This Matters
In this architecture, Kubernetes does more than run AI containers. It connects job admission, event-driven elasticity, accelerator allocation, data acceleration, and observability. Training and inference can each select an appropriate runtime while reusing the same infrastructure capabilities.
CNCF projects provide neutral, composable infrastructure interfaces. The bank can upgrade a training framework or inference engine without replacing the resource and data layers beneath it. It can also add or change accelerator types without rewriting the entire training and inference workflow.
Measurement note: Results are presented using the bank’s internally consistent before-and-after methodology and the comparable model and service conditions stated above.

# Future Plans
The next phase focuses on four areas:
· Dynamic multi-tenant concurrency: Move beyond the fixed five-tenant default by adjusting Twinkle concurrency according to model size, LoRA configuration, memory pressure, and service objectives, building on the platform’s validation of up to eight concurrent tenants.
· Unit-cost-based capacity management: Combine accelerator utilization, training queue state from Kueue, latency signals from Prometheus, and token cost to guide capacity allocation between training and inference.
· Serverless AI workloads with KEDA: Extend KEDA’s event-driven autoscaling toward a serverless operating model for AI workloads, allowing inference services to scale down to zero where service objectives permit and scale back up from live demand signals, while using Fluid caching to reduce model-readiness delays during scale-out.
· Broader hardware and runtime support: Expand HAMi-based support for heterogeneous accelerators and add more training and inference backends without coupling the two workload paths, while contributing production experience upstream.
Share
