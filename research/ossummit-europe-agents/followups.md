# Agents talk: research follow-ups

Not for the deck yet. Open questions to investigate before talking about them publicly.

## CUDA_DISABLE_CONTROL=true opts a container out of HAMi-core enforcement

Source: [HAMi device plugin `Allocate`](https://github.com/Project-HAMi/HAMi/blob/eb46ae6b4b8c2ee83c5cae566c85c7a0e5bb77b9/pkg/device-plugin/nvidiadevice/nvinternal/plugin/server.go#L1430-L1447) (HAMi `eb46ae6`). Tests: `alloc_refactor_test.go`, `TestAllocate_MultiContainer_CUDA_DISABLE_CONTROL_*`.

Observed in code: if a container's env sets `CUDA_DISABLE_CONTROL=true`, the device plugin skips the read-only `/etc/ld.so.preload` mount, so `libvgpu.so` (HAMi-core) is never preloaded. The container still gets the GPU device, but without the memory and core limits.

To research:

- Who can set it: any pod author with create rights. Is there an admission check in HAMi's webhook? If not, block it with a ValidatingAdmissionPolicy or Kyverno rule for untrusted namespaces.
- Does the scheduler still account the container's `gpumem`/`gpucores` reservation while the runtime does not enforce it? What does vGPUmonitor report for it?
- Intended use case (debugging, trusted system pods?) and whether upstream documents it.
- Related bypasses of user-space enforcement: statically linked CUDA binaries ignore `ld.so.preload`; direct ioctls on `/dev/nvidia*` skip `libcuda`. Confirm which still respect limits.
- Consequence for the threat model: HAMi soft slicing is a resource and fairness control for trusted workloads, not a security boundary between untrusted tenants.
