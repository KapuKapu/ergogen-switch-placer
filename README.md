# Ergogen Swtich Placer

Places a KiCad footprint at every key position defined in an [Ergogen](https://docs.ergogen.xyz/) points JSON file, producing a `.kicad_pcb` board.

## Prerequisites

- [KiCad](https://www.kicad.org/) (provides the `pcbnew` Python module)
- [mise](https://mise.jdx.dev/) (task runner)

## Usage

```
mise place <points.json> <footprint.kicad_mod> [output.kicad_pcb]
```

| Argument | Description |
|---|---|
| `points_path` | Ergogen points JSON file (required) |
| `footprint_path` | KiCad footprint `.kicad_mod` file (required) |
| `output_path` | Output `.kicad_pcb` path (default: `placed.kicad_pcb`) |

### Example

```
mise place points.json Kailh_socket_PG1350.kicad_mod keyboard.kicad_pcb
```

### Output

```
Placed 36 footprints -> keyboard.kicad_pcb
```

Each key gets a reference (`K1`, `K2`, …) and its Ergogen key name as the value. Coordinates are translated from Ergogen's coordinate system (Y-up) to KiCad's (Y-down).

## Testing

```
mise run test
```
