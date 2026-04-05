# Ergogen Switch Placer

KiCad IPC API plugin that places a footprint at every key position defined in an [Ergogen](https://ergogen.cache.works/) `points.json` file.

## How it works

The plugin connects to a running KiCad instance via the IPC API (using [kipy](https://github.com/KiCad/kicad-python)), finds a template footprint already on the board, and clones it to every key position from the Ergogen points file — setting the correct X/Y coordinates and rotation for each.

### Template footprint workaround

The KiCad IPC API does not yet support creating footprints from a library directly. As a workaround, **you must manually place one instance** of the desired footprint on the board first (Place → Add Footprint). The plugin uses that instance as a clone template and removes the need to place every remaining switch by hand.

## Installation

Copy the `plugins/` directory into your KiCad plugins path, or symlink it:

```sh
ln -s "$(pwd)/plugins" ~/.local/share/kicad/9.0/scripting/plugins/ergogen-switch-placer
```

Install the plugin's Python dependencies into KiCad's scripting environment, or into the plugin directory:

```sh
pip install -r plugins/requirements.txt
```

## Standalone CLI usage

The plugin can also be run outside KiCad as a CLI tool (KiCad must still be running for the IPC connection):

```sh
uv run --extra plugin python plugins/action.py points.json "Library:Footprint"
```

Arguments:

- `points.json` — path to the Ergogen points JSON file
- `Library:Footprint` — footprint to place, in `LibraryName:FootprintName` format

## Development

Requires [mise](https://mise.jdx.dev/) and [uv](https://docs.astral.sh/uv/).

```sh
mise run test     # run tests
mise run lint     # lint with ruff
mise run format   # format with ruff
```
