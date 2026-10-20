# GPU Sharing on Kubernetes with HAMi: 45-minute Workshop Plan

Status: draft v0.1, 2026-10-20. Owner: Reza Jelveh. Deck: `gpu_workshop.md`.

Formats this plan covers:

- **Workshop (45 min)**: hands-on, attendees follow on their laptop.
- **ContribFest (45 min cut)**: same lab, last block swapped for a first contribution. The accepted KubeCon NA 2026 ContribFest (75 min, "GPU Virtualization: First Setup and Understanding the Device Plugin / DRA") is the long version of this.

## Goal

Attendees leave with a working Kubernetes cluster where they asked for a fraction of a GPU, saw the HAMi scheduler place it, and know where to read or change the code.

## Audience and prerequisites

- Knows `kubectl`, Pods and Helm basics. No GPU or HAMi experience needed.
- Laptop with Docker (or OrbStack on macOS), `kubectl`, `helm`, `kind`, `git`, `jq`. 4 CPU and 8 GB free.
- Optional: access to a real NVIDIA GPU node (cloud VM). Only needed for the isolation demo, which the presenter runs live.
- Pre-event mail: install tools, pre-pull images, clone `Project-HAMi/hami-workshop` and `Project-HAMi/mock-device-plugin`.

## Lab tracks

Two tracks, same concepts. Pick one at the door.

- **Track A, no GPU (default)**: kind cluster, HAMi scheduler, and `Project-HAMi/mock-device-plugin`. The mock registers fake `nvidia.com/gpumem` and `nvidia.com/gpucores` from a node annotation, so the real HAMi scheduler makes real placement decisions. No memory or compute isolation is enforced.
- **Track B, real GPU (presenter + volunteers)**: follows `hami-workshop` Lab 1 (`docs/labs/online-install.md`): GPU Operator with its device plugin disabled, then HAMi. Shows `nvidia-smi` inside a Pod reporting the sliced memory limit.

The existing `hami-workshop` Lab 2 (fake-gpu-operator + OrbStack) bypasses the HAMi webhook and installs HAMi with `devicePlugin.enabled=false`, so it does not exercise HAMi scheduling. That is why Track A uses mock-device-plugin instead.

## Run of show (45 min)

- **00:00 to 05:00, Why share GPUs** (slides 2 to 4). Whole-card allocation, the 2 GB inference Pod on a 16 GB card. What HAMi adds: `gpumem`, `gpucores`, scheduler extender, device plugin, HAMi-core.
- **05:00 to 10:00, Architecture walk** (slides 5 to 6). Request, webhook, scheduler extender, node annotation `hami.io/node-nvidia-register`, device plugin, HAMi-core in the container. Hand out the lab link.
- **10:00 to 18:00, Lab 1: cluster and HAMi** (slide 7). kind cluster, `helm install hami`, check `hami-scheduler` Pod and the `hami-scheduler-device` ConfigMap.
- **18:00 to 25:00, Lab 2: fake GPUs** (slide 8). Deploy mock-device-plugin, patch the `nvidia.com/gpu` count, annotate the node with two fake A100-80GB cards, read `allocatable`.
- **25:00 to 33:00, Lab 3: share a GPU** (slides 9 to 10). Apply three Pods asking for `gpumem` 20000 and `gpucores` 30. Watch them bin-pack onto the fake cards, then a fourth Pod that does not fit stays `Pending`. Read the scheduler events and the Pod annotations HAMi writes.
- **33:00 to 38:00, Live demo on a real GPU** (slide 11). Presenter only. `nvidia-smi` in a Pod with `gpumem: 3000` shows a 3000 MiB limit. A Pod that allocates past it gets an out-of-memory error.
- **38:00 to 43:00, Contribute** (slide 12). Workshop: where to go next (DRA driver, WebUI, vendor plugins). ContribFest: pick a labelled good-first-issue, run `make test` in HAMi, open a draft PR with maintainers in the room.
- **43:00 to 45:00, Wrap and Q&A** (slide 13). Repo, Slack, community meeting, feedback form.

## Lab commands (Track A)

These are the commands on the slides. They follow the HAMi chart and the mock-device-plugin README. They have not yet been run end to end together, see "Dry run" below.

```bash
kind create cluster --name hami-lab
helm repo add hami-charts https://project-hami.github.io/HAMi/
helm install hami hami-charts/hami -n kube-system
kubectl get pods -n kube-system | grep hami

git clone https://github.com/Project-HAMi/mock-device-plugin
kubectl apply -f mock-device-plugin/k8s-mock-rbac.yaml
kubectl apply -f mock-device-plugin/k8s-mock-plugin.yaml

NODE=hami-lab-control-plane
kubectl label node $NODE gpu=on
kubectl patch node $NODE --subresource=status --type=json \
  -p '[{"op":"add","path":"/status/capacity/nvidia.com~1gpu","value":"20"}]'
kubectl annotate node $NODE 'hami.io/node-nvidia-register=[
 {"id":"GPU-MOCK-0","count":10,"devmem":81920,"devcore":100,"type":"NVIDIA-A100-SXM4-80GB","health":true,"numa":0,"mode":"hami-core"},
 {"id":"GPU-MOCK-1","index":1,"count":10,"devmem":81920,"devcore":100,"type":"NVIDIA-A100-SXM4-80GB","health":true,"numa":0,"mode":"hami-core"}]'
kubectl get node $NODE -o json | jq '.status.allocatable|with_entries(select(.key|test("nvidia.com")))'
```

Sharing Pod (based on `HAMi/examples/nvidia/default_use.yaml`):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: share-1
spec:
  containers:
  - name: app
    image: ubuntu:22.04
    command: ["bash", "-c", "sleep 86400"]
    resources:
      limits:
        nvidia.com/gpu: 1
        nvidia.com/gpumem: 20000
        nvidia.com/gpucores: 30
```

## Open items before submitting or running

1. **Dry run Track A on kind.** Open questions: does the mock plugin's health gate hold with the HAMi device plugin DaemonSet absent, and does the `gpu=on` label matter without it? Fix the commands from that run.
2. **Decide the real-GPU source** for the live demo (Vultr partnership is a candidate). Budget one T4 or L4 VM for the session plus a rehearsal.
3. **Decide hosting** for lab instructions: add a Lab 3 "Share a GPU without a GPU" to `hami-workshop` (EN + ZH pages, `examples/03-mock-gpu-sharing/`), so attendees get a stable URL.
4. **ContribFest**: ask maintainers to label 10 to 15 good-first-issues across HAMi, mock-device-plugin and hami-workshop a week before.
5. **Speakers**: confirm who presents and who helps in the room (one helper per 20 attendees).
6. **Event**: link this plan to the target CFP in the CFP list once chosen.

## Value to the community

- A no-GPU path to the real HAMi scheduler, so anyone can learn and test GPU sharing on a laptop.
- Shows that a shared GPU is a scheduling and isolation problem the CNCF stack can solve (Kubernetes device plugins, scheduler extenders, Helm, Prometheus).
- Feeds new contributors and docs fixes back into HAMi, mock-device-plugin and hami-workshop.
