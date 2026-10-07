---
theme: ossummit_europe
seaborn_theme: ossummit_europe
title: Designing Permissioned AI Agents That Can Run Offline
logo: assets/brand/dynamia-logo.svg
logo_dark: assets/brand/dynamia-logo-white.png
watermark: assets/brand/ossummit_europe/watermark.svg
footer: "Permissioned AI Agents Offline"
transition: fade
paginate: true
size: 16:9
---

<!--
- Not about one agent framework: about the boundary around agents
- Running examples: notmutt (MCP server, deny by default) and HAMi (GPU slices per agent)
-->
@variant dark
@kicker Open Source Summit Europe 2026 - Open AI & Data

# Designing Permissioned AI Agents That Can Run Offline

@subtitle Layer the limits; keep the decisive ones out of the agent's reach

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI - Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh

---

# Part 1: The Boundary Problem

@subtitle Agents now read files and call tools

---

<!--
- Chat was harmless: the human copied the answer
- Now the agent holds the keys: files, tools, state, other services
-->

## Agents Left the Chat Window

::: grid {cols=2}
::: card {tag=cyan}
### {icon:file-text cls=accent-primary} Read files

Mail, documents, code, config. Whatever the process can open.
:::
::: card {tag=green}
### {icon:wrench cls=accent-primary} Call tools

MCP servers, shell commands, REST APIs.
:::
::: card {tag=yellow}
### {icon:pencil cls=accent-contrast} Change state

Send, delete, tag, deploy. Some of it cannot be undone.
:::
::: card {tag=red}
### {icon:network cls=accent-secondary} Coordinate services

One agent drives several services, each with its own credentials.
:::
:::

---

<!--
- Cloud design: model, data and keys all meet at a third party
- Broad API keys: one token, every operation
- Offline is not an edge case: planes, factories, privacy rules
-->

## Where Cloud-Hosted Agents Break

::: grid {cols=2}
::: card {tag=red}
### {icon:cloud-upload cls=accent-secondary} Private data leaves the device

Every prompt carries context to someone else's server.
:::
::: card {tag=yellow}
### {icon:key cls=accent-contrast} Broad API keys

One token authorizes every operation the API has.
:::
::: card {tag=cyan}
### {icon:eye-off cls=accent-primary} Little visibility

The user cannot see what the agent is allowed to do.
:::
::: card {tag=green}
### {icon:wifi-off cls=accent-primary} No network, no agent

Nothing works when the connection drops or is cut on purpose.
:::
:::

---

<!--
OpenClaw started bulk-deleting the inbox of Meta's AI alignment director after context compaction dropped her "confirm before acting" instruction; she had to run to her Mac mini to stop it: https://www.businessinsider.com/meta-ai-alignment-director-openclaw-email-deletion-2026-2. A mail tool that exposes delete, with no declared capabilities, leaves you to hand-roll the harness: staging, sandboxing, review. The tool itself has no boundary.
-->

## MCP Plugins: Do Not Trust the Tool

@subtitle You do not know if it wipes your mail

::: grid {cols=2}
::: card {tag=red}
### {icon:trash-2 cls=accent-secondary} Unknown destructive power

- OpenClaw started deleting a Meta AI director's inbox, ignoring her confirm-first rule
- Your MCP tool may expose the same delete: you do not know
:::
::: card {tag=yellow}
### {icon:shield-alert cls=accent-contrast} You build the harness

- LLM tries to break your system
- You hand-roll guards: staging, sandboxing, review
:::
:::

**You can audit a plugin, but a defensive security posture is better.**

---

<!--
- The core assumption of this talk
- An agent with write access to its own config will eventually widen its own grant
- Harnesses are useful: just do not bet on them
- Tool-side enforcement is the tool maker's job; you will never get it from every tool, so it is no guarantee either
- Hence layers: the harness, the tool where you control it, and always the sandbox, credentials and network around it
-->

## Assume Every Tool Is Hostile

@subtitle If it can reach the config, it will change it

- Every tool is risky by default, including the ones you wrote.
- An agent that can open its config file will find a way to rewrite its own limits.
- Build harnesses around agents, but assume they will break.
- Tools that enforce limits help, but you cannot count on every tool doing it.
- So layer it: in the agent, in the tool where you can, and **around the tool** always.

---

<!--
- Say this out loud: every later slide is a mitigation against this adversary
- The agent is not malicious by design: it goes rogue. A wrong assumption, prompt injection, a bad tool result, a context-compaction slip or poisoned model weights all get you there
- They are all part of the threat, but we do not need a separate defense for each: whatever the cause, the result is the same rogue agent, and the same boundaries contain it
- Second adversary: the model server itself. vLLM has had remote-code-execution bugs; a crafted request can turn it into attacker code on the GPU
- Out of scope is a decision, not a claim that those threats do not exist
- Name the actual threat before picking controls. If the agent's code ran on the inference GPU, you would need a Kata VM, and then GPU passthrough and GPU segmentation for VMs: costly and constrained (one whole GPU per VM, no live migration, minutes to boot, a privileged launcher, per the gpucellpool and KubeSwift docs; we have not evaluated them ourselves). But the threat is code execution by the agent, and that code never needs a GPU. Keep agent code on CPU nodes and the whole GPU-in-a-VM problem disappears
- So what if the weights are poisoned: the model itself cannot execute tools. A poisoned model only makes bad proposals; the harness and tool server still decide, inside the same boundaries
- OpenShell passes GPUs into sandboxes (CDI, device plugin, VFIO for microVMs): a different threat model, where the agent's own tools run CUDA. Ours does not, so we skip that cost
-->

## Threat Model

@subtitle Who we defend against, and what we protect

::: grid {cols=3}
::: card {tag=red}
### {icon:skull cls=accent-secondary} Adversary

- The agent running rogue: a wrong assumption, prompt injection or poisoned weights
- Whatever the cause, it runs any code inside its sandbox
- A model server taken over through its API
:::
::: card {tag=cyan}
### {icon:lock cls=accent-primary} Assets

- Workspace, secrets and the grant
- Model weights, other tenants' prompts and KV cache
- The node and the cluster
:::
::: card {tag=yellow}
### {icon:circle-slash cls=accent-contrast} Out of scope

- A malicious cluster admin
- Hardware and firmware attacks
:::
:::

@tiny The threat model also tells you what to skip: agent code never needs the GPU, so agent sandboxes need no GPU passthrough.

---

<!--
- When people talk about agent sandboxes, it is everything or nothing: either a bare container, or Kata for everything
- Responsibility decides the boundary. Ask what each component does, and what it can do when it goes rogue
- The model only produces text: a poisoned or injected model makes bad proposals, it does not execute anything. It needs a gateway, not a VM
- The supervisor or harness decides and holds the keys: it must stay trusted and out of the agent's reach. OpenShell: "The supervisor is trusted and makes the decisions. The sandbox shares the boundary with the untrusted agent, so it never makes policy decisions."
- The tool sandbox runs agent code: that is where the strong boundary goes. Per command (Sandlock: Landlock, seccomp, about 5 ms) or a VM when the threat is the kernel
- agent-sandbox: "Isolation depth is a deployment choice." OpenShell: "The runtime's job is to build the boundary and prove it's in place. It never decides whether a request is allowed."
- gpucellpool (interesting, not evaluated by us) says in its own docs that even a VM around a GPU is "layered isolation, not tenant isolation"
- Sandlock talk by Cong Wang, Wednesday 17:25, Panorama Hall: "You do not need a hypervisor to stop rm -rf ~. You need a policy."
-->

## Isolation Is Not All or Nothing

@subtitle Responsibility decides the boundary, not Kata everywhere

| Component | Its job | If it goes rogue | Boundary |
|---|---|---|---|
| Model | Proposes text | Bad proposals, nothing runs | Gateway; no tools, no egress |
| Harness, supervisor | Decides, holds keys | Must stay trusted | Out of the agent's reach |
| Tool sandbox | Runs agent code | Anything inside the box | Per-command policy, or a VM |
| Tool server | Talks to mail, APIs | Its own credential scope | Narrow keys, own identity |

@tiny "Isolation draws the boundary. Policy decides what happens inside it." Cong Wang, Sandlock, OSS Europe 2026

::: notes
Source: [agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox/blob/42679cc/site/content/docs/_index.md); [OpenShell architecture](https://github.com/NVIDIA/openshell/blob/8aa5846d7/docs/about/architecture.mdx); [Sandlock](https://github.com/multikernel/sandlock)
:::

---

# Part 2: Layers the Agent Cannot Reach

@subtitle Deny by default, then defend around the tool

---

<!--
- The model only proposes; the tool server decides
- So a poisoned or injected model cannot act on its own: it can only propose
- Sandlock's Execute-Only Agents pattern goes further: the planner has network but no data, the executor has data but no network, so no stage holds both secrets and a way out
- The tool server holds the grant; the agent cannot see or edit it
- Destructive changes wait for a human
-->

## Separate Reasoning From Action

@subtitle The model proposes, the tool server decides

```seaborn
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
coral, green, teal, _, navy = sns.color_palette()[:5]
dim = plt.rcParams["xtick.color"]
fig, ax = plt.gcf(), plt.gca()
fig.set_size_inches(11, 4.2)
fig.patch.set_alpha(0)
ax.set_xlim(0, 11); ax.set_ylim(0, 4.2); ax.axis("off")

def box(x, y, w, h, text, c=green, fill=0.12, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.15",
                                ec=c, fc=(*c[:3], fill), lw=2, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=15)

def arrow(a, b, label="", c=dim, ls="-", dx=0, dy=0.18):
    ax.annotate("", b, a, arrowprops=dict(arrowstyle="-|>", color=c, lw=2, ls=ls,
                                          mutation_scale=20, shrinkA=0, shrinkB=0))
    if label:
        ax.text((a[0] + b[0]) / 2 + dx, (a[1] + b[1]) / 2 + dy, label,
                ha="center", va="bottom", fontsize=13, color=c)

box(0.2, 2.5, 2.0, 1.0, "Agent")
box(0.2, 0.5, 2.0, 1.1, "Grant\n(read-only)", c=coral)
box(3.9, 1.5, 2.6, 1.2, "Tool server\nchecks the grant", c=navy, fill=0.08)
box(8.4, 2.7, 2.4, 1.1, "Mail, files,\nservices")
box(8.4, 0.3, 2.4, 1.1, "Human\napplies", c=coral)
arrow((2.2, 3.0), (3.9, 2.4), "asks", dy=0.12)
arrow((2.2, 1.05), (3.9, 1.8))
arrow((6.5, 2.4), (8.4, 3.2), "reads", dx=-0.1, dy=0.12)
arrow((6.5, 1.8), (8.4, 0.9), "staged writes", dx=0.2, dy=0.15)
arrow((9.6, 1.4), (9.6, 2.7))
```

---

<!--
- Same ideas in any tool server: notmutt is just where I tried them
- Data the tool never loads cannot leak; a typo in the grant fails loudly instead of widening it
-->

## Deny by Default

@subtitle The tool serves nothing until you grant it

- Start from an empty grant: nothing is visible until you name it.
- Never load data the tool does not need; then it cannot leak.
- A misspelled grant stops the server instead of silently widening it.

---

<!--
- notmutt is my mail client; its MCP server is built this way
- The grant sits in config, destructive actions wait for a human
- Nice when you wrote the server; most MCP servers you run, you did not
-->

@layout image-right

## One MCP Server Built This Way

@subtitle notmutt, a terminal mail client

- Nothing is visible until the config grants it.
- The agent can stage changes; only I apply them.

![notmutt](assets/notmutt.png)

---

<!--
- The same-disk caveat generalized: whatever defines the boundary must be physically out of reach
- Kubernetes gives you the primitives: separate service accounts, read-only mounts, no write RBAC on the ConfigMap
-->

## Keep the Grant Out of Reach

@subtitle The agent must not be able to edit its own limits

::: grid {cols=2}
::: card {tag=red}
### {icon:file-lock cls=accent-secondary} Config owned by someone else

Another user, a read-only mount, or a separate container. Never a file the agent can write.
:::
::: card {tag=yellow}
### {icon:hard-drive cls=accent-contrast} No shared disk

An agent that can read the maildir does not need the MCP server.
:::
::: card {tag=cyan}
### {icon:key-round cls=accent-primary} Keys stay outside

A host-side proxy swaps a placeholder for the real token. The agent never holds the key.
:::
::: card {tag=green}
### {icon:boxes cls=accent-primary} Separate identities

Model, tool server and destructive tools each run with their own account and permissions.
:::
:::

---

<!--
- notmutt is the nice case: the server itself enforces the grant
- In practice you run MCP servers you did not write, and yours has bugs too
- So treat the server like the agent: assume it can do something destructive
-->

## Assume the MCP Server Breaks Too

@subtitle Defensive design around the tool

- The server is code: bugs, a bad update, or a tool you did not write.
- Give it the narrowest credentials; read-only where reads are enough.
- Run destructive tools in a VM or a separate account, with a backup first.
- Keep writes reversible: stage, review, apply, and keep the undo.
- Cap how much one call may touch: a hundred messages, not the mailbox.

---

<!--
- Surveyed in github.com/fishman/awesome-agent-sandbox
- Same ideas keep showing up, independent of the isolation level
- yolobox says it plainly in its README: protects against accidents, not container escapes
- drydock: only a git diff leaves the VM; nothing reaches origin until you approve it (unless you turn on --auto-approve)
- Defaults differ: yolobox, microsandbox and matchlock let traffic out unless told otherwise; check before trusting
- Sandlock (Cong Wang, OSS Europe 2026): Landlock, seccomp-bpf and seccomp user notification, rootless, about 5 ms per command, so confinement can wrap every command. One sandbox per session means the union of all permissions; pytest, pip install and the LLM call each need different ones
-->

## Agent Sandboxes Already Do This

@subtitle Three isolation levels, the same rules

::: grid {cols=3}
::: card {tag=green}
### {icon:cpu cls=accent-primary} Process

Landlock, seccomp, bubblewrap. Starts in milliseconds, cheap enough per command. Sandlock, `srt` (Claude Code's sandbox), nono, ai-jail.
:::
::: card {tag=yellow}
### {icon:box cls=accent-contrast} Container

Docker or rootless Podman; dropped capabilities and egress proxy are opt-in. yolobox: protection from accidents, not container escapes.
:::
::: card {tag=cyan}
### {icon:server cls=accent-primary} MicroVM

Firecracker or libkrun. Vendors claim sub-second boot. smolvm, microsandbox, matchlock.
:::
:::

- Keys stay on the host; a proxy injects them per request (matchlock, nono, drydock).
- The stricter tools deny egress by default, with an allowlist (srt, smolvm, drydock).
- Only a diff leaves the sandbox, after you approve it (drydock).

::: notes
Source: [awesome-agent-sandbox](https://github.com/fishman/awesome-agent-sandbox); [srt](https://github.com/anthropics/sandbox-runtime/tree/v0.0.78); [yolobox](https://github.com/finbarr/yolobox); [matchlock](https://github.com/jingkaihe/matchlock); [drydock](https://github.com/sricola/drydock)
:::

---

<!--
- agent-sandbox (SIG Apps) v1.0.x (v1.0.5 now) is what OpenShell builds on for Kubernetes; OpenSandbox can use it as an optional provider; it orchestrates, the RuntimeClass isolates
- Its managed NetworkPolicy blocks private ranges and cloud metadata but allows the whole public internet; its router is allow-all by default, and TokenReview only authenticates
- OpenShell on k8s needs a CNI that enforces NetworkPolicy (ingress and egress); without one, sandboxes bypass the supervisor. agent-sandbox's own example says it bluntly: "On a cluster whose CNI ignores NetworkPolicy this file is decoration"
- Kelos's Claude Code image runs with --dangerously-skip-permissions in ordinary pods: isolation is whatever the cluster gives it
-->

## Agent Sandboxes on Kubernetes

@subtitle Three layers, each one can be missing

- **Runtime isolation:** gVisor or Kata, picked by RuntimeClass.
- **Orchestration:** `kubernetes-sigs/agent-sandbox` v1.0.x: Sandbox, SandboxTemplate, SandboxWarmPool. Default egress: public internet.
- **Policy:** OpenShell (default-deny egress, credentials injected at the proxy), agentgateway (tool authorization).
- A NetworkPolicy on a CNI that ignores it is decoration.
- Kelos runs Claude Code with `--dangerously-skip-permissions` in ordinary pods.

::: notes
Source: [agent-sandbox threat model](https://github.com/kubernetes-sigs/agent-sandbox/blob/42679cc/docs/security/threat_model.md); [OpenShell runtimes](https://github.com/NVIDIA/openshell/blob/8aa5846d7/docs/how-it-works/sandboxes/runtimes.mdx); [agentgateway](https://github.com/agentgateway/agentgateway); [Kelos entrypoint](https://github.com/kelos-dev/kelos/blob/main/claude-code/kelos_entrypoint.sh)
:::

---

<!--
- The model needs text, not your filesystem: the harness reads a file through a tool and sends the contents as a prompt
- So the code lives only in the sandbox; inference runs on GPU nodes with no volumes and no egress
- Keep the GPU out of the sandbox: GPU passthrough into a VM exists (gpucellpool, KubeSwift; not evaluated by us) but costs a whole GPU per VM, no live migration and a privileged launcher, and widens the host surface with /dev/vfio
- Stricter variant: harness in its own pod, sandbox only executes commands through an exec API
- Caveat: code sent as context is in the prompt; if that is confidential, run inference on hardware you own
-->

## Keep Inference Away From the Code

@subtitle The model needs text, not your filesystem

```seaborn
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
coral, green, teal, _, navy = sns.color_palette()[:5]
dim = plt.rcParams["xtick.color"]
fig, ax = plt.gcf(), plt.gca()
fig.set_size_inches(12, 4.2)
fig.patch.set_alpha(0)
ax.set_xlim(0, 12); ax.set_ylim(0, 4.2); ax.axis("off")

def box(x, y, w, h, text, c=green, fill=0.12, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.15",
                                ec=c, fc=(*c[:3], fill), lw=2, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=15)

def arrow(a, b, label="", c=dim, ls="-", dx=0, dy=0.18):
    ax.annotate("", b, a, arrowprops=dict(arrowstyle="-|>", color=c, lw=2, ls=ls,
                                          mutation_scale=20, shrinkA=0, shrinkB=0))
    if label:
        ax.text((a[0] + b[0]) / 2 + dx, (a[1] + b[1]) / 2 + dy, label,
                ha="center", va="bottom", fontsize=13, color=c)

def pool(x, w, label):
    ax.add_patch(FancyBboxPatch((x, 0.2), w, 3.8, boxstyle="round,pad=0,rounding_size=0.2",
                                ec=dim, fc="none", lw=1.2, ls="--"))
    ax.text(x + w / 2, 3.75, label, ha="center", va="top", fontsize=12, color=dim)

pool(0.1, 3.0, "CPU pool, Kata VMs")
pool(4.5, 3.0, "Gateway pool")
pool(8.9, 3.0, "GPU pool")
box(0.3, 1.5, 2.6, 1.3, "Agent sandbox\nharness, tools,\n/workspace")
box(4.7, 1.5, 2.6, 1.3, "Model gateway\nroutes, tokens,\nbudgets", c=navy, fill=0.08)
box(9.1, 1.5, 2.6, 1.3, "vLLM\nno volumes,\nno egress")
arrow((2.9, 2.15), (4.7, 2.15), "HTTPS +\ntoken", dy=0.08)
arrow((7.3, 2.15), (9.1, 2.15), "mTLS", dy=0.08)
ax.annotate("", (10.4, 1.5), (1.6, 1.5), arrowprops=dict(arrowstyle="-|>", color=coral, lw=2,
            ls="--", mutation_scale=20, connectionstyle="arc3,rad=0.35"))
ax.text(6.0, 0.4, "blocked", ha="center", fontsize=13, color=coral)
```

---

<!--
- In-cluster NetworkPolicy is enforced by the kernel of the node the pod runs on: a sandbox that roots its node can turn it off
- So the boundary that protects model serving must live outside the cluster: separate subnets or VLANs per node pool, cloud or hardware firewall
- Gateway: Envoy, agentgateway or LiteLLM in front of vLLM. vLLM's own --api-key is weak and vLLM has had remote-code-execution CVEs, so it should only ever see the gateway
- OpenShell hides the key but removed its inference router in 0.1.0: "Provider attachment does not select or rewrite a model." Hiding the key and limiting what the key can do are two jobs; the gateway does the second
- Side doors: service account token, cloud metadata (169.254.169.254), kubelet 10250, NodePorts, vLLM multi-node ports (ZMQ, NCCL, Ray), open DNS
-->

## Segment the Model Network

@subtitle The sandbox reaches the gateway, and nothing else

::: grid {cols=2}
::: card {tag=red}
### {icon:network cls=accent-secondary} Subnets and a firewall

One subnet per node pool. The firewall sits outside the cluster, so it holds even if a sandbox owns its node.
:::
::: card {tag=yellow}
### {icon:box cls=accent-contrast} A VM per sandbox

Kata on separate nodes. A container escape does not land on a node that can reach the GPUs.
:::
::: card {tag=cyan}
### {icon:shield cls=accent-primary} Default-deny NetworkPolicy

Sandboxes may only call the gateway; vLLM only accepts the gateway. Needs a CNI that enforces it.
:::
::: card {tag=green}
### {icon:filter cls=accent-primary} Model gateway

Inference routes only, a token per sandbox, token budgets, mTLS to vLLM. Admin endpoints stay unreachable.
:::
:::

@tiny Close the side doors too: no service account token, no cloud metadata endpoint, no kubelet, no vLLM multi-node ports.

---

# Part 3: Least Privilege for Compute

@subtitle One device, several agents

---

<!--
Hermes and OpenClaw can reason and use tools. Running them at the edge is hard: not because of the models, but because of the compute underneath. Limited memory, tight power budgets, unattended operation, no elastic scaling. To run agents at the edge, fix the compute layer first.
Small models make this more feasible every month, especially for tool calls: most agent invocations are narrow, repetitive "pick a tool, fill the arguments" steps, not open conversation. NVIDIA's position paper argues small language models are sufficient and cheaper for many agentic invocations, with a larger model only where general reasoning is needed: https://arxiv.org/abs/2506.02153. Google's FunctionGemma is a 270M Gemma 3 fine-tuned for function calling, runs on a Jetson Nano or a phone, and went from 58% to 85% on their Mobile Actions eval after fine-tuning: https://blog.google/innovation-and-ai/technology/developers-tools/functiongemma/. Pattern: a small local model routes and calls tools; a bigger local model handles the hard cases. Smaller models also mean more agents per GPU slice.
-->

## Edge Agents, Starved Compute

@subtitle Offline means the model runs on hardware you own

::: grid {cols=2}
::: card {tag=red}
### {icon:memory-stick cls=accent-secondary} Limited memory

A Jetson has 4-128 GB of unified memory, shared with the OS. One agent stack can eat it all.
:::
::: card {tag=yellow}
### {icon:zap cls=accent-contrast} Tight power budgets

No 300 W data-center GPU at the edge. Jetson Orin runs at 7-60 W, often on battery or solar.
:::
::: card {tag=cyan}
### {icon:user-x cls=accent-primary} Unattended

No cluster admin on call. It has to work after setup.
:::
::: card {tag=green}
### {icon:scale cls=accent-primary} No elastic scaling

Cloud load grows: add GPUs. Edge load grows: nothing to add. The deployed box is all you get.
:::
:::

---

<!--
GPUs are expensive and often underutilized. HAMi is a heterogeneous GPU sharing framework for Kubernetes, a CNCF Incubating project. It slices GPUs and shares them across workloads, without rewriting your stack.
-->

## What is HAMi

@subtitle Before: one device, one task

![Before HAMi](assets/hami_intro/before-hami.png)

---

## What is HAMi
@transition none

@subtitle After: one device, many agents

![After HAMi](assets/hami_intro/after-hami.png)

---

<!--
Without isolation, one workload can grab all memory and OOM-kill the other tasks on the same device. HAMi enforces memory when it hijacks the runtime calls: every task sees only its own slice. Footnote: the limit is enforced inside the container, so it stops accidents and greedy agents, not a determined attacker. Destructive tools belong in a VM; GPU slicing for VMs is harder (passthrough, vendor vGPU or MIG), so keep the GPU on the model side.
Side channels: HAMi cannot intercept them, even MIG leaves timing channels, but vGPUmonitor can give us evidence. It records who shares which GPU (device_uuid on every container series, hami_mig_device_info for MIG slices), per-container memory and SM use (hami_vgpu_memory_used_bytes, hami_container_device_utilization_ratio, hami_container_last_kernel_elapsed_seconds) and device-wide signals that contention shows up in (hami_host_gpu_utilization_ratio, hami_host_gpu_memory_controller_utilization_ratio, power, temperature). That allows co-tenancy audit and anomaly hints, for example memory-controller pressure that does not match any tenant's own SM use, or a tenant that runs kernels while its requests are idle. Limits: scrape-interval sampling is far too coarse to see a covert channel itself; it is detection and forensics, not prevention.
-->

## Least Privilege for the GPU

@subtitle One greedy agent must not starve its neighbors

::: grid {cols=3}
::: card {tag=red}
### {icon:triangle-alert cls=accent-secondary} Without HAMi

Agents share a device with no borders. One greedy agent eats all memory and kills the neighbors. On an 8 GB Jetson, that is the whole device.
:::
::: card {tag=green}
### {icon:shield-check cls=accent-primary} With HAMi

Each agent sees only its slice. Every allocation is checked against it.
:::
::: card {tag=cyan}
### {icon:gauge cls=accent-contrast} Per-agent limits

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
    nvidia.com/gpumem: 3000
```
:::
:::

@tiny Footnote: destructive tools are safer in a VM, since escaping a container is easier. GPUs in VMs are possible but costly; agent sandboxes do not need them.

---

<!--
- HAMi slicing is enforced in user space and the GPU is time-shared: it protects availability between cooperating workloads, not confidentiality, and one GPU fault hits every tenant
- MIG partitions compute, cache and memory in hardware, but shared PCIe, power and thermal still leave timing channels; data-center cards only
- Side channels need attacker code on the GPU, so the first rule is that agent code never gets a GPU
- Prompts reach model servers as text through the gateway, not as CUDA code; the residual risk is a compromised model server, hence the gateway and same-classification co-location
- HAMi is where this policy is enforced: placement (UUID, type, spread), MIG profiles, quotas; vGPUmonitor shows who shared which GPU, but cannot stop a channel
- Worth a look, not something we have run or evaluated: gpucellpool composes KubeSwift and HAMi: one whole GPU passed into a VM with VFIO, HAMi slices it inside. "A HAMi fraction is never handed to VFIO: the two layers nest, they do not translate." Its own wording: layered isolation between groups that trust the same operators, not tenant isolation. Alpha, one GPU per cell, about 5 minutes to boot a cell
-->

## Share a GPU Only Within One Trust Domain

@subtitle Slicing protects availability, not secrets

| Workload | GPU | With HAMi |
|---|---|---|
| Agent sandboxes | None | No device at all |
| Your model servers, same data class | Shared slices | `gpumem`, `gpucores`, binpack |
| Different tenants or data classes | MIG or a whole GPU | `vgpu-mode: mig`, `use-gpuuuid`, spread |
| Strictest | Separate nodes | Separate node pools |

@tiny Even MIG leaves side channels. vGPUmonitor shows who shared which GPU, as evidence, not prevention.

---

# Part 4: Local and Offline

@subtitle Run it on hardware you own

---

<!--
The path is short. Pick a device: Jetson-class for CUDA compatibility (the HAMi slicing path exists for CUDA). Slice it: memory in MiB, compute in percent, hard limits per agent. Schedule agents: binpack to pack them tight, spread for SLOs. Everything runs on k3s or k0s. Olares is the turnkey path: an open-source (AGPL-3.0) personal cloud OS on K3s that ships its own HAMi fork for GPU time-slicing and memory-slicing; MCP comes per app from its market.
-->

## Keep Sensitive Context Local

@subtitle Three steps to a multi-agent edge device

::: grid {cols=3}
::: card {tag=green}
### {icon:cpu cls=accent-primary} 1. Pick a device

Jetson-class GPU: CUDA compatible, so HAMi can slice it.
:::
::: card {tag=cyan}
### {icon:gauge cls=accent-primary} 2. Slice it

Memory and compute per agent, with hard limits.
:::
::: card {tag=yellow}
### {icon:git-branch cls=accent-contrast} 3. Schedule agents

Binpack many agents onto one device; spread when latency matters.
:::
:::

- Prompts, documents and mail never leave the device.
- **Olares** ([github.com/beclab/olares](https://github.com/beclab/olares)): open-source personal cloud OS on K3s, ships a HAMi fork for GPU slicing.
- Or run on k3s or k0s directly: Kubernetes APIs without an ops team.

---

<!--
- The boundary is enforced by the tool, the config and the scheduler, not just by the agent's good behavior
-->

## Takeaways

- Assume every tool is hostile; layer limits in the agent, the tool and around both.
- Let responsibility decide each boundary: not everything needs a VM.
- Separate reasoning from action: the model proposes, the tool server decides.
- Grant nothing by default; keep the grant out of the agent's reach.
- Keep inference and tools on separate nodes; the sandbox reaches only the model gateway.
- Give each agent its own compute slice, on hardware you own.

---

@layout ecosystem
## Community & Adopters

@subtitle Devices, integrations, and who uses HAMi

<!--
5.2k stars, 325k pulls, 500+ contributors, 27 countries. 11 device types, 20+ adopters.
-->

#### Open Source, CNCF Backed, Production Ready
::: grid {cols=5}
::: card {metric}
5.2k
Github Stars
:::
::: card {metric}
325k
Docker Pulls
:::
::: card {metric}
500+
Contributors
:::
::: card {metric}
27
Contributor Countries
:::
::: card

![Kubernetes](assets/ecosystem/integrations/kubernetes.png) ![Volcano](assets/ecosystem/integrations/volcano.png) ![Kueue](assets/ecosystem/integrations/kueue.png) ![Koordinator](assets/ecosystem/integrations/koordinator.png) ![KAI Scheduler](assets/ecosystem/integrations/kai-scheduler.png) ![cozystack](assets/ecosystem/integrations/cozystack.svg)
:::
:::

#### Ecosystem & Device Support
::: grid {cols=2}
::: card
![NVIDIA](assets/ecosystem/devices/nvidia.png) ![Ascend](assets/ecosystem/devices/ascend.png) ![Cambricon](assets/ecosystem/devices/cambricon.png) ![Hygon](assets/ecosystem/devices/hygon.png) ![Iluvatar](assets/ecosystem/devices/illuvitar.png)
![Metax](assets/ecosystem/devices/metax.png) ![Moore Threads](assets/ecosystem/devices/moorethreads.png) ![Kunlunxin](assets/ecosystem/devices/kunlunxin.png) ![Enflame](assets/ecosystem/devices/enflame.png)
![AWS](assets/ecosystem/devices/aws.png) ![VastStream](assets/ecosystem/devices/vaststream.png)
:::
:::

#### Adopters
::: grid {cols=2}
::: card
![4Paradigm](assets/ecosystem/adopters/4paradigm.png) ![Baidu](assets/ecosystem/adopters/baiduzhineng.png) ![Baike](assets/ecosystem/adopters/baike.png) ![China Merchants](assets/ecosystem/adopters/chinamerchants.png) ![China Mobile](assets/ecosystem/adopters/chinamobile.png)
![China Unicom](assets/ecosystem/adopters/chinaunicom.png) ![DaoCloud](assets/ecosystem/adopters/daocloud.png) ![Dynamia](assets/ecosystem/adopters/dynamia.png) ![H3C](assets/ecosystem/adopters/h3c.png) ![Huawei](assets/ecosystem/adopters/huawei.png)
![LinkedIn](assets/ecosystem/adopters/linkedin.png) ![MSXF](assets/ecosystem/adopters/msxf.png) ![NIO](assets/ecosystem/adopters/nio.png) ![PPIO](assets/ecosystem/adopters/ppio.png) ![Prep](assets/ecosystem/adopters/prep.png)
![SAP](assets/ecosystem/adopters/sap.png) ![SF Technology](assets/ecosystem/adopters/sftechnology.png) ![Si-Tech](assets/ecosystem/adopters/si-tech.png) ![Snow](assets/ecosystem/adopters/snow.png) ![Viettel](assets/ecosystem/adopters/viettel.png)
:::
:::

---

@kicker Thank You
@side-image assets/qr-notmutt.png
# Questions?

@subtitle github.com/Project-HAMi/HAMi - github.com/fishman/notmutt

@speaker name="Reza Jelveh" role="Solution Architect, Dynamia AI - Makers of HAMi" github=github.com/fishman linkedin=linkedin.com/in/rezajelveh
