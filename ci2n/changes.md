# Changes Made to the CI2N Repository

This file records the intentional edits made to the original CI2N repository during the Image2Net analysis and validation work. The changes are listed in the order they were introduced conceptually.

## 1. CPU-safe junction classifier loading

File changed: `ci2n/app.py`

The original code loaded the PyTorch junction classifier with:

```python
junction_classifier_model = torch.load(settings.junction_classifier_model_path).to(torch_device)
```

That failed on a CPU-only machine when the saved model contained CUDA tensor storage metadata. The error was:

```text
RuntimeError: Attempting to deserialize object on a CUDA device but torch.cuda.is_available() is False
```

The model load was changed to:

```python
junction_classifier_model = torch.load(
    settings.junction_classifier_model_path,
    map_location=torch_device,
).to(torch_device)
```

This keeps GPU behavior when CUDA is available and maps the saved tensors to CPU when CUDA is not available. It does not alter model weights or inference logic.

## 2. YOLO class-name normalization

Files changed: `ci2n/app.py`, `ci2n/items.py`

The YOLO model uses several hyphenated class names, such as:

```text
single-end-amp
voltage-lines
pmos-cross
nmos-bulk
capacitor-3
```

The original lookup expected mostly underscore-based names, such as `single_end_amp` and `voltage_lines`. This caused valid detections to be logged as unknown and skipped before any port extraction or netlist generation.

The detection loop now normalizes YOLO class names before lookup:

```python
normalized_class_name = class_name.lower().replace("-", "_")
device_type = class_name_to_device_type.get(normalized_class_name, None)
```

The device label map was also extended with explicit aliases for hyphenated labels and common resistor variants:

```text
voltage-lines
single-end-amp
single-input-single-end-amp
diff-amp
pmos-cross
pmos-bulk
nmos-cross
nmos-bulk
npn-cross
pnp-cross
capacitor-3
inductor-3
switch-3
resistor
resistor-2
resistor1-3
resistor2-3
```

Result: valid YOLO detections are no longer dropped only because the model label spelling differs from the code label spelling.

## 3. Configurable verbose output root

Files changed: `ci2n/app.py`, `run.py`

The original CLI always wrote verbose artifacts under:

```text
verbose/<timestamp>/
```

The `run.py` Fire CLI now accepts:

```text
--verbose_path <path>
```

The default remains `verbose`, but callers can now isolate runs, for example:

```bash
python run.py \
  --path inputs/fix_smoke_v2/006.png \
  --output outputs/fix_smoke_v2/006.json \
  --verbose=True \
  --verbose_path verbose/fix_smoke_v2/006
```

This made it possible to store validation and smoke-run artifacts in separate folders without changing the core inference flow.

## 4. Optional circuit type parameter

Files changed: `ci2n/app.py`, `ci2n/line_algo.py`, `run.py`

The generated validation-style JSON includes a `ckt_type` field because the validation tooling expects that key. However, the inference pipeline generally does not know the true circuit type unless it is supplied externally.

The CLI now accepts:

```text
--ckt_type <label>
```

The default value is now the empty string:

```json
"ckt_type": ""
```

This avoids producing:

```json
"ckt_type": "Unknown"
```

when the circuit type has not actually been inferred. If a caller knows the type, they can pass it explicitly.

## 4a. Selectable output syntax with `--validation`

Files changed: `ci2n/app.py`, `ci2n/line_algo.py`, `run.py`

The CLI now accepts a `--validation` boolean flag that controls only the final JSON syntax. It does not change detection, model loading, port extraction, wire tracing, or junction logic.

Validation mode is the default because it preserves the currently working validation/golden-style output:

```bash
python run.py --path inputs/006.png --output outputs/006.json --verbose=True
```

or explicitly:

```bash
python run.py --path inputs/006.png --output outputs/006.json --verbose=True --validation=True
```

Validation mode emits:

```json
{
  "ckt_netlist": [
    {
      "component_type": "PMOS",
      "port_connection": {
        "Drain": "a",
        "Gate": "b",
        "Source": "c"
      }
    }
  ],
  "ckt_type": ""
}
```

Raw/internal mode can be selected with:

```bash
python run.py --path inputs/006.png --output outputs/006_raw.json --verbose=True --validation=False
```

Raw/internal mode emits the original list-style CI2N component naming:

```json
[
  {
    "component_type": "pmos",
    "port_connection": {
      "ds1": "a",
      "g": "b",
      "ds2": "c"
    }
  }
]
```

The validation mapping is:

```text
pmos / pmos_cross / pmos_bulk -> PMOS
nmos / nmos_cross / nmos_bulk -> NMOS
npn / npn_cross -> NPN
pnp / pnp_cross -> PNP
resistor variants -> Res
capacitor variants -> Cap
inductor variants -> Ind
voltage / voltage_lines -> Voltage
current -> Current
single_end_amp -> Diso_amp
single_input_single_end_amp -> Siso_amp
diff_amp -> Dido_amp
```

## 5. Non-MOS direction classification support

File changed: `ci2n/line_algo.py`

The original `get_device_direction_and_ports` function only supported MOS devices for orientation prediction. Non-MOS components such as resistors, capacitors, BJTs, voltage sources, current sources, diodes, switches, and amplifier blocks were not processed by the direction classifier. Many of them raised:

```text
Device type <...> not supported
```

The code now defines grouped device sets:

```python
TwoTerminalTypes
BjtTypes
AmpTypes
DirectionalTypes
```

`DirectionalTypes` is used for orientation prediction. This allows the existing orientation classifier to run on supported non-MOS devices as well.

Result: non-MOS components now receive a direction value before port boxes are assigned.

## 6. Non-MOS port extraction

File changed: `ci2n/line_algo.py`

The original `get_device_ports` function only implemented meaningful ports for:

```text
PMOS / NMOS
GND
port
```

For other detected devices, ports were empty. That made components such as `resistor2`, `npn`, `capacitor`, `current`, and amplifier blocks appear in raw JSON with `{}` as `port_connection`, which is not useful for GED validation.

The code now assigns approximate geometric port regions for:

```text
Res, Cap, Ind, Switch: Pos, Neg
Voltage / voltage-lines: Positive, Negative
Current: In, Out
Diode: In, Out
NPN / PNP: Collector, Base, Emitter
single-end amplifier: InP, InN, Out
single-input single-end amplifier: In, Out
fully differential amplifier: InP, InN, OutP, OutN
```

The port regions are based on the detected bounding box and the predicted direction. This is a heuristic port extractor; it is not a retrained model.

## 7. BJT port geometry correction

File changed: `ci2n/line_algo.py`

During testing on validation image `006.png`, the detected NPN devices were assigned base regions on the wrong side for the predicted orientation. That caused the wire stage to miss or misassign BJT ports.

The BJT port-region logic was adjusted so that:

```text
direction l: Base on left, Collector/Emitter on right
direction r: Base on right, Collector/Emitter on left
direction u/d: Base and collector/emitter split by vertical orientation
```

This improved preservation of NPN components in the generated netlist for image `006.png`.

## 8. Treat `voltage-lines` as a voltage source

File changed: `ci2n/line_algo.py`

The validation image `002.png` showed that YOLO detects the left-side voltage source symbol as `voltage-lines`. Earlier output formatting treated `voltage_lines` as a hidden terminal/supply marker, which meant it was not emitted as a normal component.

The serialization and port extraction logic now treats `voltage_lines` as:

```text
component_type: Voltage
ports: Positive, Negative
```

The voltage polarity rule was also separated from generic two-terminal components so that for an upward-oriented source, the upper half maps to `Positive` and the lower half maps to `Negative`.

Result for image `002.png`: the generated netlist now includes the voltage source that was missing from the previous formatted output.

## 9. Validation-style JSON output

File changed: `ci2n/line_algo.py`

The original `circuit_to_json` returned a raw list like:

```json
[
  {
    "component_type": "nmos",
    "port_connection": {
      "ds1": "a",
      "g": "b",
      "ds2": "c"
    }
  }
]
```

The validation repository expects a wrapper and golden-style component/port names:

```json
{
  "ckt_netlist": [
    {
      "component_type": "NMOS",
      "port_connection": {
        "Drain": "a",
        "Gate": "b",
        "Source": "c"
      }
    }
  ],
  "ckt_type": ""
}
```

The serializer now maps component names to validation-compatible names:

```text
pmos / pmos_cross / pmos_bulk -> PMOS
nmos / nmos_cross / nmos_bulk -> NMOS
npn / npn_cross -> NPN
pnp / pnp_cross -> PNP
resistor variants -> Res
capacitor variants -> Cap
inductor variants -> Ind
voltage / voltage_lines -> Voltage
current -> Current
single_end_amp -> Diso_amp
single_input_single_end_amp -> Siso_amp
diff_amp -> Dido_amp
```

The serializer also maps MOS ports:

```text
ds1 -> Drain
ds2 -> Source
g -> Gate
```

## 10. Preserve detected components with floating placeholder nets

File changed: `ci2n/line_algo.py`

An earlier formatted-output attempt filtered out components that did not have every expected port connected. That made the formatted output look cleaner, but it also caused a regression: detected components such as NPNs and resistors disappeared from the generated netlist if the wire tracing stage missed one terminal.

The serializer now preserves every detected supported component. If a required port has no inferred net, it is filled with a deterministic placeholder net:

```text
floating_<device_name>_<port_name>
```

Example:

```json
{
  "component_type": "Res",
  "port_connection": {
    "Pos": "d",
    "Neg": "floating_resistor2_5_Neg"
  }
}
```

This makes the output valid for downstream graph construction while still exposing that the connection was not actually recovered by inference. It avoids silently deleting a detected component.

## 11. GND net aliasing

File changed: `ci2n/line_algo.py`

Connections touching detected GND symbols are now named:

```text
GND
```

instead of arbitrary generated net names such as `a`, `b`, or `c`.

This better matches the validation/golden netlist convention and improves readability of generated JSON.

## 12. Validation inference helper script

File added: `scripts/run_validation_inference.py`

A helper script was added to run inference over all validation images in one pass. It:

1. Copies validation images from `../ci2n_datasets/validation/images` into `inputs/validation`.
2. Runs `run.py` on each image.
3. Writes raw output JSON files to `outputs/run1`.
4. Moves verbose artifacts into `verbose/run1/<image_id>`.
5. Captures stdout/stderr for each task in `verbose/run1/<image_id>/run.log`.
6. Writes a summary file at `outputs/run1/_run1_summary.json`.

This script is operational tooling for batch inference. It does not change the CI2N inference algorithm itself.

## 13. Smoke-test artifact folders

Folders added during testing:

```text
inputs/fix_smoke/
outputs/fix_smoke/
verbose/fix_smoke/
inputs/fix_smoke_v2/
outputs/fix_smoke_v2/
verbose/fix_smoke_v2/
```

These folders contain isolated example runs for validation images `002.png` and `006.png`.

The final smoke run after the latest fixes used:

```text
inputs/fix_smoke_v2/
outputs/fix_smoke_v2/
verbose/fix_smoke_v2/
```

Observed component-count comparison:

```text
golden_002: Diso_amp 1, NMOS 2, Voltage 1, Res 1
v2_002:     Diso_amp 1, NMOS 2, Voltage 1

golden_006: Diso_amp 1, PMOS 3, Res 3, NPN 3
v2_006:     Diso_amp 1, PMOS 3, Res 3, NPN 3
```

For `002.png`, the resistor is still missing because the YOLO detector does not produce a resistor bounding box for that image. That is a detector/model limitation, not a serializer or port-formatting issue.

## 14. Remaining limitations

These changes improve label handling, non-MOS ports, and validation-compatible formatting, but they do not make the system equivalent to a retrained or fully paper-level implementation.

Known limitations:

1. Non-MOS port extraction is geometric and heuristic.
2. If YOLO misses a component, serialization cannot recover it.
3. Placeholder `floating_*` nets preserve components but also mark missed wire connections.
4. Device polarity and BJT collector/emitter assignment can still be wrong for some orientations.
5. `ckt_type` is not inferred by the model; it is blank unless supplied with `--ckt_type`.
