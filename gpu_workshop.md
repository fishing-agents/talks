---
theme: kubecon_japan
title: "Share a GPU on Kubernetes: HAMi Hands-on Workshop"
logo: assets/brand/dynamia-logo.svg
logo_dark: assets/brand/dynamia-logo-white.png
footer: "HAMi GPU Workshop"
transition: fade
paginate: true
size: 16:9

---

<!--
45 minute workshop. Plan and run of show: gpu_workshop_plan.md.
Track A (no GPU) uses Project-HAMi/mock-device-plugin. Commands not yet dry-run end to end.
-->
@variant dark
@side-image assets/qr-hami-repo.png
@kicker Hands-on workshop, 45 minutes

# Share a GPU on Kubernetes

@subtitle Fractional GPUs with HAMi, on your laptop

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI - Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

---

## What you will do today

::: grid {cols=3}
::: card {tag=cyan}
### Build
A kind cluster with the HAMi scheduler.
:::
::: card {tag=green}
### Share
Ask for 20 GB and 30% of a GPU and watch Pods pack onto one card.
:::
::: card {tag=yellow}
### Contribute
Find where the code lives and pick a first issue.
:::
:::

No GPU needed. Track B with a real GPU runs on the presenter's screen.

---

<!--
00:00 to 05:00. Keep it short, the lab is the point.
-->

## Kubernetes hands out whole GPUs

- `nvidia.com/gpu: 1` means one full card, even for a 2 GB model.
- Other Pods wait while most of the card's memory sits idle.
- Time-slicing shares a card but sets no memory limit per Pod.
- MIG gives hard partitions, on some cards only, with fixed sizes.

---

## What HAMi adds

::: grid {cols=2}
::: card {tag=cyan}
### Ask for a slice
`nvidia.com/gpumem` in MB and `nvidia.com/gpucores` in percent, next to `nvidia.com/gpu`.
:::
::: card {tag=green}
### Schedule by slice
A scheduler extender places Pods by free memory and cores per card.
:::
::: card {tag=yellow}
### Enforce in the container
HAMi-core limits memory and compute inside the container.
:::
::: card {tag=red}
### Many vendors
NVIDIA, Ascend, Cambricon, Hygon, Iluvatar, MetaX and more.
:::
:::

CNCF project: [github.com/Project-HAMi/HAMi](https://github.com/Project-HAMi/HAMi)

---

<!--
05:00 to 10:00. Walk the path once, then refer back to it during Lab 3.
-->

## The path of a GPU request

1. Pod asks for `gpu`, `gpumem`, `gpucores`.
2. HAMi webhook routes it to `hami-scheduler`.
3. The scheduler extender reads cards from the node annotation `hami.io/node-nvidia-register`.
4. It picks a card and writes the choice as Pod annotations.
5. The device plugin mounts the card and HAMi-core sets the limits.

---

## Two tracks, same scheduler

::: grid {cols=2}
::: card {tag=cyan}
### Track A: no GPU
kind + HAMi + mock-device-plugin. Fake cards from a node annotation. Real scheduling, no isolation.
:::
::: card {tag=green}
### Track B: real GPU
GPU Operator with its device plugin off, then HAMi. Limits visible in `nvidia-smi`.
:::
:::

Lab guide: [github.com/Project-HAMi/hami-workshop](https://github.com/Project-HAMi/hami-workshop)

---

<!--
10:00 to 18:00. Helpers walk the room. Common issue: image pulls on conference wifi, so pre-pull in the setup mail.
-->

## Lab 1: cluster and HAMi

```bash
kind create cluster --name hami-lab
helm repo add hami-charts https://project-hami.github.io/HAMi/
helm install hami hami-charts/hami -n kube-system
kubectl get pods -n kube-system | grep hami
kubectl get cm hami-scheduler-device -n kube-system -o yaml | head -40
```

Done when `hami-scheduler` is `Running`.

---

<!--
18:00 to 25:00. Explain the three pieces: config block, count resource, annotation.
-->

## Lab 2: two fake A100 cards

```bash
kubectl apply -f mock-device-plugin/k8s-mock-rbac.yaml
kubectl apply -f mock-device-plugin/k8s-mock-plugin.yaml
NODE=hami-lab-control-plane
kubectl patch node $NODE --subresource=status --type=json \
  -p '[{"op":"add","path":"/status/capacity/nvidia.com~1gpu","value":"20"}]'
kubectl annotate node $NODE 'hami.io/node-nvidia-register=[...]'
kubectl get node $NODE -o json | jq '.status.allocatable'
```

Expect `nvidia.com/gpumem: 163840` and `nvidia.com/gpucores: 200`.

---

<!--
25:00 to 33:00. Apply share-1..3 first, then share-4 asking for 50000.
-->

## Lab 3: share a GPU

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
    nvidia.com/gpumem: 20000
    nvidia.com/gpucores: 30
```

- Apply `share-1` to `share-3`. All three run.
- Apply `share-4` with `gpumem: 50000`. Where does it go?

---

## Read what the scheduler decided

```bash
kubectl get pods -o wide
kubectl describe pod share-4 | tail -5
kubectl get pod share-1 -o json | jq '.metadata.annotations'
```

- Which card did each Pod get?
- How much memory is left per card?
- What breaks if you ask for `gpucores: 80` four times?

---

<!--
33:00 to 38:00. Presenter only, real NVIDIA node. Run nvidia-smi in a gpumem 3000 Pod, then an allocation past the limit.
-->

## Live: limits on a real GPU

::: grid {cols=2}
::: card {tag=cyan}
### Ask
`nvidia.com/gpumem: 3000`
:::
::: card {tag=green}
### See
`nvidia-smi` in the Pod shows 3000 MiB total.
:::
:::

Going over the limit returns out of memory inside the Pod, not on the node.

---

## Next step: contribute

::: grid {cols=3}
::: card {tag=cyan}
### Code
HAMi scheduler and device plugins. `make test`.
:::
::: card {tag=green}
### Labs
New pages and fixes in hami-workshop, EN and ZH.
:::
::: card {tag=yellow}
### Devices
Mock support for more vendors in mock-device-plugin.
:::
:::

Look for `good first issue` labels. Maintainers are in the room.

---

@variant dark

# Thank you

@subtitle github.com/Project-HAMi/HAMi · project-hami.io

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI - Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh
