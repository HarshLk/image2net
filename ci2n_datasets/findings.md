# CI2N Datasets Repository Findings

Date reviewed: 2026-06-02

Repository path reviewed:

```text
ci2n_datasets
```

Remote:

```text
https://github.com/LAD021/ci2n_datasets.git
```

This repository is the dataset companion to the Image2Net / CI2N circuit-image-to-netlist project. It contains training/evaluation datasets for several subproblems:

- component object detection,
- component orientation/mirror classification,
- jumper/crossing detection,
- and graph-based netlist validation.

It is not the same as the inference-code repository. It contains datasets and validation utilities, not the main `run.py` conversion pipeline.

## High-Level Repository Layout

Top-level files:

```text
.gitignore
LICENSE
README.md
README_zh.md
findings.md
```

Top-level data/tool directories:

```text
device_identification/
device_orientation/
jumper_identification/
validation/
```

Actual local file counts:

```text
device_identification: 2269 PNG images, 2269 JSON annotation files
device_orientation: 12047 JPG images, 507 PNG images
jumper_identification: 333 JPG images, 522 PNG images, 855 TXT label files
validation: 122 PNG images, 122 JSON golden netlists, 3 Python files, 2 TOML files, 1 README, 1 uv.lock
```

Important README discrepancy:

- The repository README says `device_identification` has 900 PNG images and fewer JSON files in one section.
- The actual local clone has 2269 paired PNG/JSON files.
- The README says validation has 127 images / 65 JSON in one section.
- The actual local clone has 122 validation images and 122 golden JSON files.

So for practical work, use the actual file counts above rather than the README's stale counts.

## Top-Level Files

### `.gitignore`

Standard Python/packaging ignore file. It ignores:

- Python bytecode and cache files,
- build/distribution artifacts,
- virtual environments,
- test/coverage outputs,
- local IDE/project metadata,
- Python package manager metadata.

It explicitly leaves `uv.lock` and `poetry.lock` uncommented in the template comments, so lockfiles can be tracked.

### `LICENSE`

Apache License 2.0.

This is different from the local `ci2n` inference repository, which has AGPL-3.0. This dataset repository itself is Apache-2.0 licensed.

### `README.md`

English overview of the dataset repository. It describes four datasets:

- `device_identification`: object detection / component bounding boxes.
- `device_orientation`: orientation and mirror classification image folders.
- `jumper_identification`: jumper/crossing detection with YOLO OBB labels.
- `validation`: image/golden-netlist pairs and GED tools.

Some counts in this README are stale relative to the local clone.

### `README_zh.md`

Chinese version of `README.md`. It gives the same dataset categories, examples, and validation-tool notes.

Some counts in this README are also stale relative to the local clone.

### `findings.md`

This file. It documents the analysis of this repository.

## `device_identification/`

Purpose:

- Train or evaluate component object detection.
- Each circuit image has a corresponding JSON file in LabelMe format.

Actual local count:

```text
PNG files: 2269
JSON files: 2269
Filename range: 0.png / 0.json through 2268.png / 2268.json
Missing numeric IDs: none
```

Pairing rule:

```text
device_identification/0.png
device_identification/0.json

device_identification/1234.png
device_identification/1234.json
```

The JSON files in this folder are not netlists. They are object-detection annotations.

### Device Identification JSON Type

Format:

- LabelMe JSON.
- Top-level metadata contains `version`, `flags`, `shapes`, `imagePath`, `imageData`, `imageHeight`, and `imageWidth`.
- The meaningful annotation data is in `shapes`.

Representative structure:

```json
{
  "version": "5.1.1",
  "flags": {},
  "shapes": [
    {
      "label": "port",
      "points": [
        [437.0, 19.0],
        [456.0, 38.0]
      ],
      "group_id": null,
      "shape_type": "rectangle",
      "flags": {}
    },
    {
      "label": "resistor",
      "points": [
        [597.0, 298.0],
        [668.0, 339.0]
      ],
      "group_id": null,
      "shape_type": "rectangle",
      "flags": {}
    }
  ],
  "imageHeight": 400,
  "imageWidth": 800
}
```

How to read it:

- `version`: LabelMe annotation version. All inspected files use `5.1.1`.
- `shapes`: list of labeled objects in the circuit image.
- `shapes[i].label`: component class name, such as `resistor`, `nmos`, `pmos`, `gnd`, etc.
- `shapes[i].points`: two rectangle corner coordinates in pixel space: `[[x1, y1], [x2, y2]]`.
- `shapes[i].shape_type`: all inspected annotations use `rectangle`.
- `imageHeight`, `imageWidth`: dimensions of the corresponding image.

To interpret one object:

```text
"label": "resistor"
"points": [[597.0, 298.0], [668.0, 339.0]]
```

means there is a resistor bounding box with corners:

```text
x1 = 597, y1 = 298
x2 = 668, y2 = 339
```

This is suitable for object detection training. It does not describe electrical connectivity.

### Device Identification Labels

Actual label statistics in the local clone:

```text
Total rectangle annotations: 45257
Unique labels: 31
Shape type: rectangle only
```

Label counts:

```text
port                         8180
resistor                     6891
gnd                          5646
capacitor                    4277
nmos                         3342
pmos                         2564
npn                          2155
vdd                          1633
resistor2                    1558
current                      1148
pnp                          1077
cross-line-curved            1065
switch                        919
voltage                       892
diode                         843
single-end-amp                674
inductor                      618
nmos-bulk                     456
pmos-bulk                     327
pmos-cross                    305
nmos-cross                    200
voltage-lines                 190
single-input-single-end-amp    89
resistor2_3                    59
diff-amp                       45
inductor-3                     31
npn-cross                      27
pnp-cross                      22
switch-3                       12
antenna                         7
capacitor-3                     5
```

Important distinction:

- These labels are detection classes.
- They are not netlist component instances.
- There is no `ckt_netlist` field in any `device_identification/*.json` file.

## `device_orientation/`

Purpose:

- Train or evaluate cropped-component orientation classifiers.
- Labels are encoded by folder names, not JSON files.

Actual local count:

```text
Total images: 12554
JPG images: 12047
PNG images: 507
```

Folder groups:

```text
train_amp_d/
train_amp_m/
train_bjt_d/
train_bjt_m/
train_diode/
train_mos/
train_switch/
train_voltagelines/
```

Naming convention:

- `_d` folders are direction/orientation classification tasks.
- `_m` folders are mirror/non-mirror classification tasks.

Direction class folders:

```text
d = down
l = left
r = right
u = up
```

Mirror class folders:

```text
0 = normal / non-mirrored
1 = mirrored
```

There are no JSON labels here. The label is the subdirectory containing the image.

Example:

```text
device_orientation/train_mos/u/u1.jpg
```

means this is a MOS crop labeled with up orientation.

```text
device_orientation/train_amp_m/1/d20.jpg
```

means this amplifier crop belongs to mirror class `1`.

### Device Orientation Subfolder Counts

```text
train_amp_d/
  d: 347
  l: 347
  r: 347
  u: 347

train_amp_m/
  0: 184
  1: 185

train_bjt_d/
  d: 1310
  l: 1310
  r: 1310
  u: 1310

train_bjt_m/
  0: 655
  1: 655

train_diode/
  d: 319
  l: 305
  r: 305
  u: 319

train_mos/
  d: 331
  l: 460
  r: 418
  u: 352

train_switch/
  d: 117
  l: 117
  r: 117
  u: 117

train_voltagelines/
  d: 229
  l: 229
  r: 229
  u: 283
```

How to use/read this dataset:

- Select the task folder, e.g. `train_mos`.
- Load all images under `d`, `l`, `r`, `u`.
- Use the subfolder name as the class label.
- For mirror tasks, load images under `0` and `1`.

## `jumper_identification/`

Purpose:

- Train or evaluate jumper/crossing detection.
- Uses image files and YOLO OBB label files.

Folder layout:

```text
jumper_identification/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

Actual local counts:

```text
images/train: 683 image files
images/val: 172 image files
labels/train: 683 TXT files
labels/val: 172 TXT files
```

Image suffixes:

```text
.jpg
.png
```

Label suffix:

```text
.txt
```

Pairing:

- Every train image has a matching train label file.
- Every val image has a matching val label file.
- No image/label mismatch was found in the local clone.

Example pair:

```text
jumper_identification/images/train/Snipaste_2024-10-30_17-51-48_train.png
jumper_identification/labels/train/Snipaste_2024-10-30_17-51-48_train.txt
```

### Jumper Label TXT Type

Format:

```text
class_id x1 y1 x2 y2 x3 y3 x4 y4
```

This is YOLO OBB style:

- `class_id`: jumper/crossing class.
- `x1 y1 ... x4 y4`: normalized coordinates of the four oriented-box corner points.
- Coordinates are usually normalized to the image width/height.

Example:

```text
0 0.40473372781065087 0.37669376693766937 0.4804733727810651 0.37669376693766937 0.4804733727810651 0.4254742547425474 0.40473372781065087 0.4254742547425474
1 0.40710059171597635 0.43766937669376693 0.49171597633136094 0.43766937669376693 0.49171597633136094 0.6327913279132791 0.40710059171597635 0.6327913279132791
```

How to read one line:

```text
class_id = 0
corner 1 = (0.4047, 0.3767)
corner 2 = (0.4805, 0.3767)
corner 3 = (0.4805, 0.4255)
corner 4 = (0.4047, 0.4255)
```

To convert normalized coordinates to pixels:

```text
pixel_x = normalized_x * image_width
pixel_y = normalized_y * image_height
```

Class mapping from README:

```text
0 = horizontal jumper
1 = vertical jumper
2 = other direction jumper
```

Actual local label statistics:

```text
Label files: 855
Total jumper annotations: 13829
Class 0: 1329
Class 1: 7510
Class 2: 4990
Malformed label lines: 0
```

This dataset does not contain JSON files.

## `validation/`

Purpose:

- Validate generated circuit netlists against golden/reference netlists.
- Provides image/netlist pairs and GED calculation tools.

Folder/file layout:

```text
validation/
├── .gitignore
├── .python-version
├── README.md
├── calc_ged.py
├── device_def.toml
├── golden/
├── images/
├── my_networkx.py
├── pyproject.toml
├── utils_ged.py
└── uv.lock
```

Actual local counts:

```text
validation/images/*.png: 122
validation/golden/*.json: 122
```

Filename IDs:

```text
001 through 127, with 005, 013, 026, 081, and 098 absent
```

Every validation image has a matching golden JSON file:

```text
validation/images/001.png
validation/golden/001.json
```

These golden JSON files are the ground-truth netlists used for validation.

### `validation/images/`

Contains PNG circuit diagram images for validation. These are the images on which a circuit-to-netlist system should run when producing outputs for GED evaluation.

### `validation/golden/`

Contains the golden/reference netlists.

These JSON files are not object-detection annotations. They are circuit-topology netlists.

### Validation Golden JSON Type

Format:

```json
{
  "ckt_netlist": [
    {
      "component_type": "Res",
      "port_connection": {
        "Neg": "net3",
        "Pos": "VDD"
      }
    },
    {
      "component_type": "NMOS",
      "port_connection": {
        "Drain": "net8",
        "Gate": "net3",
        "Source": "net1"
      }
    }
  ],
  "ckt_type": "DISO-Amplifier"
}
```

How to read it:

- `ckt_netlist`: list of circuit components.
- Each list item is one component instance.
- `component_type`: type of component, such as `NMOS`, `PMOS`, `Res`, `Cap`, etc.
- `port_connection`: mapping from port name to net name.
- `ckt_type`: high-level circuit family/category.

The JSON does not include explicit component instance names. Repeated components are distinguished by list position.

How to interpret nets:

```json
{
  "component_type": "NMOS",
  "port_connection": {
    "Drain": "net8",
    "Gate": "net3",
    "Source": "net1"
  }
}
```

means:

- this NMOS drain is connected to `net8`,
- gate is connected to `net3`,
- source is connected to `net1`.

All ports with the same net string are electrically connected. For example, every port mapped to `net3` belongs to the same network. Special names such as `VDD` and `GND` are also nets.

Actual local golden-netlist statistics:

Circuit type counts:

```text
DISO-Amplifier: 54
Bandgap: 24
DIDO-Amplifier: 21
LDO: 9
Comparator: 7
SISO-Amplifier: 7
```

Component type counts:

```text
PMOS: 582
NMOS: 548
Res: 178
Cap: 99
PNP: 47
NPN: 33
Current: 33
Diso_amp: 28
Voltage: 11
Dido_amp: 7
Diode: 4
Siso_amp: 3
```

Common port names:

```text
PMOS: Drain, Gate, Source, optional Body
NMOS: Drain, Gate, Source, optional Body
Res: Pos, Neg
Cap: Pos, Neg
PNP/NPN: Base, Collector, Emitter
Current: In, Out
Voltage: Positive, Negative
Diso_amp: InN, InP, Out
Dido_amp: InN, InP, OutN, OutP
Diode: In, Out
Siso_amp: In, Out
```

### `validation/README.md`

Brief instructions for the GED validation tool.

It says:

- use `uv` to set up the environment,
- `golden/` contains golden netlists,
- `images/` contains the validation set,
- generated result files should be put into an input directory and named like the files in `golden/`,
- run `calc_ged.py` to compute GED.

Run pattern:

```bash
uv run python calc_ged.py --input_dir <input_dir> --golden_dir golden --output_dir <output_dir> --timeout <timeout>
```

### `validation/.gitignore`

Ignores validation-run artifacts:

```text
.venv
input*
output*
verbose
```

This means expected local validation workflows may create:

- virtual environments,
- generated input directories,
- output reports,
- verbose GED traces.

### `validation/.python-version`

Contains:

```text
3.12
```

This is for pyenv/uv-style Python selection in the validation tool subproject.

### `validation/pyproject.toml`

Defines a small Python project named `netlist` for validation utilities.

Requires:

```text
Python >= 3.12
```

Dependencies listed:

```text
fire>=0.7.0
loguru>=0.7.3
matplotlib>=3.9.3
networkx>=3.4.2
numpy>=2.1.3
pydantic>=2.10.3
scipy>=1.14.1
toml>=0.10.2
torch==2.4
```

Important issue:

- `validation/utils_ged.py` imports `dgl`.
- The README also says DGL is required.
- But `validation/pyproject.toml` does not list `dgl`.

So a fresh `uv sync` may not be sufficient unless DGL is installed separately or the environment already has it.

### `validation/uv.lock`

Lockfile for the validation Python environment managed by `uv`.

It pins resolved package versions and wheel/source hashes for reproducible setup.

### `validation/device_def.toml`

Defines supported device ports and port-merge/equivalence rules.

Important contents:

```toml
[device_ports]
PMOS = ["Drain", "Source", "Gate", "Body"]
NMOS = ["Drain", "Source", "Gate", "Body"]
Voltage = ["Positive", "Negative"]
Current = ["In", "Out"]
NPN = ["Base", "Emitter", "Collector"]
PNP = ["Base", "Emitter", "Collector"]
Diode = ["In", "Out"]
Diso_amp = ["InN", "InP", "Out"]
Siso_amp = ["In", "Out"]
Dido_amp = ["InN", "InP", "OutN", "OutP"]
Cap = ["Pos", "Neg"]
Gnd = ["Port"]
Vdd = ["Port"]
Ind = ["Pos", "Neg"]
Res = ["Pos", "Neg"]

[port_merge]
PMOS = ["DS", "DS", "G", "B"]
NMOS = ["DS", "DS", "G", "B"]
Voltage = ["P", "P"]
Current = ["P", "P"]
Cap = ["P", "P"]
Ind = ["P", "P"]
Res = ["P", "P"]
```

Interpretation:

- `device_ports` lists expected ports for each component type.
- `port_merge` lists equivalence classes used during topology comparison.
- MOS drain/source are merged to `DS`, so drain/source swaps are not penalized.
- Passive positive/negative ports are merged to `P`, so orientation swaps on passive components are not penalized.

Note:

- I did not see `device_def.toml` imported by `calc_ged.py` or `utils_ged.py` in the inspected code path. The same logic appears partly hardcoded in `utils_ged.py`.

### `validation/calc_ged.py`

Entry point for graph-edit-distance validation.

Workflow:

1. Takes `input_dir`, `golden_dir`, `output_dir`, and `timeout`.
2. Collects every `*.json` file from `golden_dir`.
3. For each golden filename, reads:
   - generated result from `input_dir/<same_filename>`,
   - reference result from `golden_dir/<same_filename>`.
4. Converts both JSON files to graphs via `HeteroGraph.generate_all_from_json`.
5. Calls `ged(input_graph, true_graph, task_name=<id>, timeout=<timeout>)`.
6. Runs cases in a multiprocessing pool.
7. Writes a JSON report at:

```text
<output_dir>/result.json
```

Run shape:

```bash
uv run python calc_ged.py \
  --input_dir input \
  --golden_dir golden \
  --output_dir output \
  --timeout 60
```

Input requirement:

If `golden/001.json` exists, your generated netlist must be:

```text
input/001.json
```

### `validation/utils_ged.py`

Main graph-conversion and GED helper file.

Key parts:

- `HeteroGraph`: converts JSON or Spectre-like netlist text into a heterogeneous graph.
- `generate_all_from_json`: reads validation JSON, converts it to a Spectre-like intermediate string, then into a graph.
- `generate_spectre_netlist_from_json`: serializes `ckt_netlist` components into internal lines such as `X0 (...) nmos`.
- `create_pmos`, `create_nmos`, `create_resistor`, etc.: build graph edges for each supported component type.
- `to_MG`: converts a DGL heterograph into a NetworkX multigraph with node/edge type attributes.
- `node_match`: nodes match when their `ntype` attributes match.
- `edge_match`: edges match when their `etype` attributes match.
- `ged`: first checks graph isomorphism; if not isomorphic, calls the custom graph edit distance generator.

Supported component conversions include:

```text
PMOS / pmos / pmos4
NMOS / nmos / nmos4
PNP / pnp
NPN / npn
Res / resistor / res
Cap / capacitor / cap
Ind / inductor
Diode / diode
Switch / switch
Current / isource
Voltage / vsource
Siso_amp / amp
Diso_amp / diffamp / opamp
Dido_amp / dido / fullydiffamp
```

Important implementation detail:

- The comment near the top says this version does not distinguish drain and source.
- For three-terminal PMOS/NMOS, both drain and source are appended to the same edge list (`edge_dp2n` / `edge_dn2n`) in parts of the code.

### `validation/my_networkx.py`

Modified NetworkX graph edit distance implementation.

Purpose:

- Compute graph edit distance between two NetworkX graphs.
- Uses an optimized edit-path search derived from NetworkX's GED algorithm.
- Uses SciPy linear assignment internally.
- Supports timeout.

The README says this modification accelerates GED by about 50%.

## JSON and Label File Types Summary

There are two JSON types and one TXT label type in this repository.

### Type 1: LabelMe Component Detection JSON

Location:

```text
device_identification/*.json
```

Meaning:

- Ground-truth bounding boxes for circuit components.
- Used for object detection training/evaluation.
- Not a circuit netlist.

Key fields:

```text
version
flags
shapes
imageHeight
imageWidth
```

Key per-object fields:

```text
label
points
shape_type
```

How to read:

```text
label = component class
points = two rectangle corners in pixel coordinates
shape_type = rectangle
```

### Type 2: Golden Netlist JSON

Location:

```text
validation/golden/*.json
```

Meaning:

- Ground-truth circuit netlists.
- Used to evaluate generated netlists with GED.
- These are the reference labels for circuit topology.

Key fields:

```text
ckt_netlist
ckt_type
```

Key per-component fields:

```text
component_type
port_connection
```

How to read:

```text
component_type = device type
port_connection = map from port name to net name
same net name = electrically connected
```

### Type 3: YOLO OBB Jumper TXT

Location:

```text
jumper_identification/labels/train/*.txt
jumper_identification/labels/val/*.txt
```

Meaning:

- Oriented bounding boxes for jumper/crossing detection.
- Used for detection model training/evaluation.

Line format:

```text
class_id x1 y1 x2 y2 x3 y3 x4 y4
```

How to read:

```text
class_id = jumper class
(x1, y1) ... (x4, y4) = normalized oriented-box corners
```

Class mapping:

```text
0 = horizontal jumper
1 = vertical jumper
2 = other direction jumper
```

## Ground Truth vs Inference Output

The dataset repository contains ground-truth labels and validation references. It does not contain the generated output of the local `ci2n` inference pipeline as its primary dataset.

Specifically:

- `device_identification/*.json`: ground-truth component bounding boxes.
- `device_orientation/*/<class>/*`: ground-truth class labels encoded by folder.
- `jumper_identification/labels/*.txt`: ground-truth oriented bounding boxes.
- `validation/golden/*.json`: ground-truth netlists.

Generated inference outputs would normally be placed in a separate input/result directory for validation, not committed as the golden dataset.

## How GED Validation Uses This Repository

To evaluate a system:

1. Run the system on each image in `validation/images/`.
2. Write the generated JSON netlist for each image into an input directory.
3. Use the same filename as the golden file:

```text
validation/images/001.png -> input/001.json
validation/golden/001.json -> reference
```

4. Run `validation/calc_ged.py`.
5. Read `<output_dir>/result.json`.

The validation script reports GED values. The paper's NED is a normalization on top of GED:

```text
NED = GED / (Ndevice + Nnet + Nport)
```

I did not find direct NED calculation in `calc_ged.py`; it appears to compute GED only.

## Compatibility Note with Local `ci2n` Inference Repository

The local inference repository output format does not appear directly identical to `validation/golden` format.

Local `ci2n` output shape:

```json
[
  {
    "component_type": "nmos",
    "port_connection": {
      "g": "a",
      "ds1": "b",
      "ds2": "c"
    }
  }
]
```

Validation expected shape:

```json
{
  "ckt_netlist": [
    {
      "component_type": "NMOS",
      "port_connection": {
        "Drain": "net8",
        "Gate": "net3",
        "Source": "net1"
      }
    }
  ],
  "ckt_type": "DISO-Amplifier"
}
```

So an adapter may be needed before scoring local `ci2n` outputs:

- wrap the list under `ckt_netlist`,
- add `ckt_type`,
- map component names to validation component names,
- map local port names to validation port names,
- handle drain/source equivalence carefully.

## Practical Takeaways

- Use `device_identification` JSON files for object detection labels.
- Use `device_orientation` folder names for orientation/mirror labels.
- Use `jumper_identification` TXT files for YOLO OBB jumper labels.
- Use `validation/golden` JSON files for ground-truth netlists.
- Use `validation/calc_ged.py` for GED scoring against generated netlists.
- Do not confuse `device_identification/*.json` with netlists; they are LabelMe bounding-box annotations.
- The README is useful conceptually, but actual file counts in the clone differ from the README.
