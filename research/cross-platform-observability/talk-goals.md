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

The accepted CFP ("One Agent, Every GPU: Vendor-Neutral Observability from the Kubernetes Scheduler") is this talk's title and maps onto the deck by slide: "harder than CPU" (slides 3-7: GPU terms, why GPU usage is hard to attribute, queued GPU work, how vGPUmonitor works on NVIDIA, three scopes), scheduling-layer instrumentation (slides 8, 12-13), the three patterns (14-16), OpenTelemetry + admission control (19: proposed admission and scheduler events card). Three of its abstract sentences oversell relative to the audit and are deliberately narrowed by the claim boundaries above, not contradicted:
- "HAMi sits at the scheduling layer and sees every GPU operation" -> narrowed by boundary 1: scheduling instrumentation sees HAMi-managed allocation decisions, not GPU operations themselves; runtime consumption is a separate, vendor-specific collector (vGPUmonitor/Ascend/dcu-exporter; `observers.md` §1-6).
- "regardless of the underlying hardware" / "without per-vendor exporters" -> narrowed by boundary 2 and 3: the reservation plane is vendor-neutral; physical and tenant telemetry still needs a per-vendor collector, and WebUI's own physical panels depend on external vendor exporters (`observers.md` finding 9).
- "patterns ... that DCGM and ROCm SMI can't see" -> narrowed by boundary 4: the added value is correlating reservation intent with vendor telemetry, not a claim vendor tools are blind to contention or waste.

## Deck organization

21 main slides followed by 10 appendix slides (including the appendix divider); two more slides are kept in the source with `@hidden`. Slide titles use plain language and fit on one line. Flow: problem (1-7: title; one question, many dashboards; GPU terms in one minute covering CUDA context/SM/NVML/MIG; why GPU usage is hard to attribute (dot diagram); queued GPU work blurs who used it (illustrative seaborn timeline, not a measurement); how vGPUmonitor works on NVIDIA (dot data flow); same GPU, three different scopes); the common view operators need (8: GPU layer of admission, usage and device, then an application layer joined through workload identity) and what DCGM alone cannot answer (9, framed as complementary: WebUI consumes DCGM for physical panels); NVIDIA has the fullest usage data and what HAMi covers for each vendor (10-11); what the HAMi scheduler reports and reserved is not the same as used (12-13); patterns: find unused reservations, track down noisy neighbors, right-size GPU requests (14-16); advice for platform builders (17-21, divider first: operator dashboard, OpenTelemetry, one metric contract for every vendor, takeaway) as the close. Appendix (22-31): what each vendor provides, then Ascend, Hygon, AMD and Biren, Cambricon and MetaX, other vendors, WebUI, DRA, Prometheus scraping, mismatched versions. Hidden: "Admission telemetry records intent, not GPU work" (its admission point stays visible as the "Admission and scheduler events" card on slide 19) and "Validation before a live cross-platform demo" (no GPU capacity, so no demo). Metric unit differences are a one-line "Today" callout on the contract slide (20), not a standalone slide. Graphs are conceptual and labeled as such. Style remains based on snow_corp_cncf.md. Full static audit and proposed hardware validation plan remain in inventory.md and its source reports.
