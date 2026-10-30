# talks-slide-decks

Talk slide decks built with [decktile](https://github.com/decktile/decktile).

## Setup

```bash
git clone --recurse-submodules <this-repo>
# or if already cloned:
git submodule update --init
pdm install
```

`pdm install` installs decktile from the `decktile/` submodule so `pdm run decktile`
works from the project root. Diagrams are ` ```pdg ` blocks
([predictygraph](https://github.com/predictygraph/predictygraph)); no graphviz needed.

## Build

```bash
make                    # build all decks
make watch-<deck>       # watch and rebuild
```

## Decks

- `snow_corp_cncf.md` - Shared GPU Scheduling (KubeCon Japan 2026)
- `hami_intro.md` - HAMi Introduction and Features - Shared GPU Scheduling & Proactive Autoscaling (KubeCon Japan 2026)

## Assets

Images per deck live in `assets/<deck>/`. Symlinked into `dist/` on build.
