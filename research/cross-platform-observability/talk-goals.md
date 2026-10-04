# Talk goals and implementation boundaries

The audience brief calls for a portable GPU observability architecture, practical overprovisioning/noisy-neighbor/right-sizing patterns, and a connection to OpenTelemetry. The deck now follows that narrative; the detailed repository inventory is supporting appendix material.

## Claim boundaries

- Scheduling instrumentation provides cross-vendor allocation accounting for integrated HAMi-managed devices, not observation of every GPU operation or every Kubernetes device-plugin workload.
- Physical/tenant consumption and memory pressure need runtime sources. Integrated runtime collectors can reduce deployment components, but cannot eliminate vendor-specific hardware/runtime interfaces.
- A device plugin alone does not guarantee HAMi scheduler or telemetry integration.
- DCGM and vendor tools can expose workload/hardware signals. The proposed added value is correlation with reservation intent, placement decisions and application outcomes, not a claim those tools cannot detect contention or wasted capacity.
- Admission control, scheduler allocation and runtime execution are separate instrumentation points.
- OpenTelemetry transport and admission/scheduler decision spans are proposed architecture, not a verified existing HAMi integration or standardized GPU semantic convention.
- Operator patterns are proposed investigations, not production case studies, measured results or demonstrated automated right-sizing.
- NVIDIA, AMD and Ascend coverage is discussed with source-backed gaps. Intel XPU Manager is motivation from the brief, not a HAMi integration claim; Intel repositories were not part of the Project-HAMi inventory.
- Speaker Bio was supplied as an empty heading. No biography was invented.


## CFP vs. claim boundaries

The accepted CFP ("One Agent, Every GPU: Vendor-Neutral Observability from the Kubernetes Scheduler") is this talk's title and maps onto the deck by slide: "harder than CPU" (slide 3, with a CUDA context/MIG primer on 4), scheduling-layer instrumentation (slides 6, 10-11), the three patterns (12-14), OpenTelemetry + admission control (17-18). Three of its abstract sentences oversell relative to the audit and are deliberately narrowed by the claim boundaries above, not contradicted:
- "HAMi sits at the scheduling layer and sees every GPU operation" -> narrowed by boundary 1: scheduling instrumentation sees HAMi-managed allocation decisions, not GPU operations themselves; runtime consumption is a separate, vendor-specific collector (vGPUmonitor/Ascend/dcu-exporter; `observers.md` §1-6).
- "regardless of the underlying hardware" / "without per-vendor exporters" -> narrowed by boundary 2 and 3: the reservation plane is vendor-neutral; physical and tenant telemetry still needs a per-vendor collector, and WebUI's own physical panels depend on external vendor exporters (`observers.md` finding 9).
- "patterns ... that DCGM and ROCm SMI can't see" -> narrowed by boundary 4: the added value is correlating reservation intent with vendor telemetry, not a claim vendor tools are blind to contention or waste.

## Deck organization

21 main slides followed by 10 appendix slides (including the appendix divider). Flow: problem (1-5: title, one question, harder than CPU, CUDA context/MIG primer, contexts and partitions); the common view operators need (6: GPU layer of admission, usage and device, then an application layer joined through workload identity) and what DCGM exporter alone cannot answer (7, framed as complementary: WebUI consumes DCGM for physical panels); how HAMi covers runtime across vendors (8-9); how HAMi does scheduling and admission metrics (10-11); patterns (12-14); advice for building a cross-vendor platform (15-21, divider first) as the close. Metric unit differences are a one-line "Today" callout on the contract slide (19), not a standalone slide. Style remains based on snow_corp_cncf.md. Full static audit and proposed hardware validation plan remain in inventory.md and its source reports.
