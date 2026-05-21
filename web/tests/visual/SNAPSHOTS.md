# Visual Regression Snapshot Manifest

28 baseline PNG fixtures committed for CI visual regression (`maxDiffPixelRatio: 0.02`).

## Galaxy view (9)

| File | Viewport | State |
|------|----------|-------|
| `snapshots/galaxy.spec.ts/galaxy-1024x768-empty.png` | 1024×768 | empty |
| `snapshots/galaxy.spec.ts/galaxy-1024x768-activating.png` | 1024×768 | activating |
| `snapshots/galaxy.spec.ts/galaxy-1024x768-activated.png` | 1024×768 | activated |
| `snapshots/galaxy.spec.ts/galaxy-1440x900-empty.png` | 1440×900 | empty |
| `snapshots/galaxy.spec.ts/galaxy-1440x900-activating.png` | 1440×900 | activating |
| `snapshots/galaxy.spec.ts/galaxy-1440x900-activated.png` | 1440×900 | activated |
| `snapshots/galaxy.spec.ts/galaxy-2560x1440-empty.png` | 2560×1440 | empty |
| `snapshots/galaxy.spec.ts/galaxy-2560x1440-activating.png` | 2560×1440 | activating |
| `snapshots/galaxy.spec.ts/galaxy-2560x1440-activated.png` | 2560×1440 | activated |

## Topology view (9)

| File | Viewport | State |
|------|----------|-------|
| `snapshots/topology.spec.ts/topology-1024x768-empty.png` | 1024×768 | empty |
| `snapshots/topology.spec.ts/topology-1024x768-activating.png` | 1024×768 | activating |
| `snapshots/topology.spec.ts/topology-1024x768-activated.png` | 1024×768 | activated |
| `snapshots/topology.spec.ts/topology-1440x900-empty.png` | 1440×900 | empty |
| `snapshots/topology.spec.ts/topology-1440x900-activating.png` | 1440×900 | activating |
| `snapshots/topology.spec.ts/topology-1440x900-activated.png` | 1440×900 | activated |
| `snapshots/topology.spec.ts/topology-2560x1440-empty.png` | 2560×1440 | empty |
| `snapshots/topology.spec.ts/topology-2560x1440-activating.png` | 2560×1440 | activating |
| `snapshots/topology.spec.ts/topology-2560x1440-activated.png` | 2560×1440 | activated |

## Decision Graph view (10)

| File | Viewport | State |
|------|----------|-------|
| `snapshots/decisions.spec.ts/decisions-empty-1024x768.png` | 1024×768 | empty |
| `snapshots/decisions.spec.ts/decisions-empty-1440x900.png` | 1440×900 | empty |
| `snapshots/decisions.spec.ts/decisions-empty-2560x1440.png` | 2560×1440 | empty |
| `snapshots/decisions.spec.ts/decisions-activating-1024x768.png` | 1024×768 | activating |
| `snapshots/decisions.spec.ts/decisions-activating-1440x900.png` | 1440×900 | activating |
| `snapshots/decisions.spec.ts/decisions-activating-2560x1440.png` | 2560×1440 | activating |
| `snapshots/decisions.spec.ts/decisions-activated-1024x768.png` | 1024×768 | activated |
| `snapshots/decisions.spec.ts/decisions-activated-1440x900.png` | 1440×900 | activated |
| `snapshots/decisions.spec.ts/decisions-activated-2560x1440.png` | 2560×1440 | activated |
| `snapshots/decisions.spec.ts/decisions-edge-types.png` | 1440×900 | activated (all 3 edge types) |

## Dev tooling notes

- All tests use `?mock=<state>` (galaxy/topology) or `?devState=<state>` (decisions) URL params — no backend seed required
- `?devEdgeDemo=true` activates in-memory edge-type demo data for the `decisions-edge-types` fixture
- Galaxy tests use `waitUntil: 'domcontentloaded'` to avoid ForceAtlas2 Web Worker keeping network active
- Topology `activating`/`activated` states render immediately without waiting for the data API
- Re-generate with: `npx playwright test tests/visual/ --update-snapshots`
