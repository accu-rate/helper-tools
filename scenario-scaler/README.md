# crowd:it Scenario Scaler

Scales the geometry of a crowd:it scenario (`.crowdit` + `_res/`) by a given percentage.
Available as a **GUI** (`scale_scenario_gui.py`) and as a **CLI** (`scale_scenario.py`).

## Requirements

- **Python 3.10 or newer**
- **tkinter** — usually included with Python on Windows and macOS; on Linux install separately:
  ```bash
  sudo apt install python3-tk   # Debian/Ubuntu
  ```
- **tkinterdnd2** *(optional)* — enables drag & drop in the GUI:
  ```bash
  pip install tkinterdnd2
  ```
  Without it the GUI still works, but only via the click-to-browse button.

Both scripts are self-contained — no other third-party packages are required.

## GUI (`scale_scenario_gui.py`)

```bash
python scale_scenario_gui.py
```

1. Drag a `.crowdit` file onto the drop zone — or click to open a file browser.
2. Set the scale factor with the slider or by typing a value (10 % – 200 %).
3. Choose whether to create a new file or overwrite the original.
4. Click **Skalieren**.

The `.crowdit` file must have a matching `<name>_res/` directory next to it.

## CLI (`scale_scenario.py`)

```bash
python scale_scenario.py <crowdit_file> <scale_percent> [options]
```

### Arguments

| Argument | Description |
|---|---|
| `crowdit_file` | Path to the `.crowdit` file |
| `scale_percent` | Scale percentage, e.g. `70` for 70 % (factor 0.7) |

### Options

| Option | Description |
|---|---|
| *(none)* | Creates `<name>_<pct>pct.crowdit` + `<name>_<pct>pct_res/` next to the original |
| `--inplace` | Modifies the original files directly |
| `--output <dir>` | Writes the scaled scenario into the given directory |

### Examples

```bash
# New file: my-scenario_70pct.crowdit + my-scenario_70pct_res/
python scale_scenario.py my-scenario.crowdit 70

# Overwrite the original
python scale_scenario.py my-scenario.crowdit 70 --inplace

# Write to a specific directory
python scale_scenario.py my-scenario.crowdit 70 --output ./scaled/
```

## What gets scaled

- All `<point x="..." y="..."/>` coordinates in floor geometry files (`_res/geometry/*.floor`)
- All `<point x="..." y="..."/>` coordinates in the `.crowdit` file (measurement rectangles etc.)

## What is NOT scaled

| Property | Reason |
|---|---|
| Pedestrian velocity, torso size, perception radius | Agent physics — independent of geometry size |
| Time values (intervals, premovement distributions) | Timing is not geometry-dependent |
| Pedestrian counts | Population size is independent of scale |
| Floor height / elevation | Vertical axis is not scaled |
| `cellDist` in `<floorProp>` | Grid cell resolution |
| `distBetweenTwoPts` in `<settings>` | Agent locomotion step size |
| `_res/out/` folder | Simulation results — not part of the input |
