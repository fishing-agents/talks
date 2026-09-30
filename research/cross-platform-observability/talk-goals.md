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

## Deck organization

20 audience-facing slides followed by 10 appendix slides (including divider). Style remains based on snow_corp_cncf.md. Full static audit and proposed hardware validation plan remain in inventory.md and its source reports.
