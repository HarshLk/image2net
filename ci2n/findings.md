# Image2Net / ci2n Repository Findings

Date reviewed: 2026-06-02

This repository contains a Python implementation of Image2Net, a hybrid framework for converting analog circuit diagram images into JSON netlists. I reviewed the repository files, the provided `paper.pdf`, the dependency metadata, and the model-file state. I did not run the repository's conversion program or perform inference.

## Repository Contents

Tracked files:

- `README.md`: Minimal setup instructions. It says to install Poetry, install Git LFS, run `poetry update`, and run `poetry run python run.py --path img.jpg --output output.json`.
- `pyproject.toml`: Poetry package metadata and top-level dependencies.
- `poetry.lock`: Resolved Poetry dependency lockfile.
- `run.py`: Thin Fire CLI wrapper around `ci2n.app.main`.
- `ci2n/app.py`: Main end-to-end conversion pipeline.
- `ci2n/line_algo.py`: Classical computer vision, graph, port, junction, wire, and JSON output helpers.
- `ci2n/items.py`: Pydantic data models and enum definitions for devices, ports, circuits, and junctions.
- `models/yolo_model.pt`: Git LFS pointer for the YOLO model, not the actual binary weight file.
- `models/junction_classifier.pt`: Git LFS pointer for the PyTorch junction classifier, not the actual binary weight file.
- `models/item_classifier.h5`: Git LFS pointer for the Keras/TensorFlow orientation classifier, not the actual binary weight file.
- `.gitattributes`: Marks `*.pt` and `*.h5` as Git LFS-managed files.
- `.gitignore`: Standard Python ignore file.
- `LICENSE`: GNU Affero General Public License v3.0.

Untracked file:

- `paper.pdf`: Provided research paper, 11 pages. Git currently reports it as untracked.

Additional directories:

- `.git`: Git metadata.
- `.codex`, `.agents`: Present but contain no files at max depth 2.

## Setup Performed

Created a separate conda environment:

```bash
conda create -y -n image2net-ci2n python=3.9 pip
```

Installed the repository's runtime dependency stack into that environment using the environment's `pip`, because Poetry was not installed on the machine:

```bash
python -m pip install \
  opencv-python==4.10.0.84 \
  scikit-image==0.24.0 \
  loguru==0.7.2 \
  pydantic==2.9.1 \
  tensorflow==2.17.0 \
  keras==3.5.0 \
  igraph==0.11.6 \
  ultralytics==8.2.92 \
  fire==0.6.0 \
  urllib3==1.22 \
  torch==2.4.1 \
  torchvision==0.19.1
```

Verification performed:

```bash
python -m pip check
```

Result:

```text
No broken requirements found.
```

Core imports also succeeded:

```text
imports ok
python 3.9.25
cv2 4.10.0
skimage 0.24.0
tensorflow 2.17.0
keras 3.5.0
torch 2.4.1+cu121
torchvision 0.19.1+cu121
ultralytics 8.2.92
urllib3 1.22
```

Import-time warnings observed:

- TensorFlow emitted CUDA factory registration / TensorRT warnings. These are common runtime-environment warnings and did not prevent import.
- Matplotlib could not write to the user's default Matplotlib config directory and used a temporary cache under `/tmp`.
- Ultralytics could not write to the user's default Ultralytics config directory and defaulted to `/tmp` or CWD.

If needed, set writable config directories before running:

```bash
export MPLCONFIGDIR=/tmp/matplotlib
export YOLO_CONFIG_DIR=/tmp/ultralytics
```

## Poetry vs Conda Setup

The repository recommends Poetry. The environment above is still valid for the practical goal of making the runtime libraries available in a separate conda env.

The clean Poetry + conda method would be:

```bash
conda create -n image2net-ci2n-poetry python=3.9
conda activate image2net-ci2n-poetry
pip install poetry
poetry config virtualenvs.create false
poetry install --no-root
```

Important: `poetry config virtualenvs.create false` prevents Poetry from creating a nested Poetry virtualenv and makes it install into the active conda env.

I did not run this Poetry path because Poetry was not installed initially, and installing Poetry into the same project env can conflict with the repository's strict `urllib3==1.22` pin. A cleaner Poetry path would use Poetry as an external tool or a fresh conda env.

## Git LFS / Model File Blocker

The model files are currently Git LFS pointer text files, not real model binaries:

```text
models/yolo_model.pt: expected LFS size 273253617 bytes
models/item_classifier.h5: expected LFS size 228476192 bytes
models/junction_classifier.pt: expected LFS size 44777446 bytes
```

`git lfs` is not installed:

```text
git: 'lfs' is not a git command.
```

Because of this, inference would fail at model loading:

- `YOLO('./models/yolo_model.pt')`
- `tf.keras.models.load_model('./models/item_classifier.h5')`
- `torch.load('./models/junction_classifier.pt')`

Required next setup step before running the system:

```bash
git lfs install
git lfs pull
```

or manually place the actual model binaries at the same paths.

## What the System Does

Image2Net converts a circuit diagram image into a netlist-like JSON representation. The input is an image containing an analog circuit schematic. The output is a JSON list of detected components, where each component has:

- `component_type`: the predicted device/component type.
- `port_connection`: a mapping from that component's port names to generated net names.

Example output shape:

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

The generated net names are artificial names such as `a`, `b`, `c`, ..., `z`, `A`, `B`, etc. They identify electrical connectivity groups, not original labels from the image.

## Paper Summary

The paper is titled "Image2Net: Datasets, Benchmark and Hybrid Framework to Convert Analog Circuit Diagrams into Netlists."

The paper's motivation is that analog IC knowledge is often trapped in image-based circuit diagrams, while LLMs and many EDA workflows need textual representations such as netlists. Existing diagram-to-netlist systems are described as limited by simplified drawing styles, limited device coverage, and weak handling of wire crossings.

The paper contributes:

- A dataset of 2914 circuit diagrams with 84195 total annotations.
- Device identification annotations for 48930 devices.
- Crossing identification annotations for 28195 crossings across 1983 images.
- Device orientation data for MOS, BJT, diode, amplifier, and voltage-line style components.
- A 104-case netlist evaluation set.
- A metric called Netlist Edit Distance (NED), based on graph edit distance over a heterogeneous graph representation of devices, nets, ports, and port-edge types.
- The Image2Net hybrid framework, combining object detection, classification, image processing, wire skeletonization, graph construction, and post-processing.

The paper reports:

- Device detection mAP@50: 98.38%.
- Device detection mAP@50-95: 74.31%.
- Crossing detection mAP@inside: 97.30%.
- Final successful rate: 80.77%.
- Average NED: reported as 0.116 in the abstract/table, while one extracted sentence says 0.657/0.659. This appears internally inconsistent in the paper text.

## Framework Architecture

The implementation is a hybrid learned-model + classical computer vision pipeline.

Learned models:

- YOLOv8 via Ultralytics detects component bounding boxes and classes.
- TensorFlow/Keras model classifies item orientation for supported components.
- PyTorch model classifies junction/crossing type.

Classical algorithms:

- OpenCV grayscale conversion and Otsu thresholding.
- Scikit-image skeletonization.
- Connected-component filtering.
- Junction point detection by local skeleton-neighborhood degree.
- Wire tracing by flood-fill / stack search over skeleton pixels.
- Geometric overlap / nearest-port matching.
- igraph connected-component grouping for final net extraction.

## Main Runtime Entry Point

Command described by the README:

```bash
poetry run python run.py --path img.jpg --output output.json
```

Equivalent with the created conda env:

```bash
conda activate image2net-ci2n
python run.py --path img.jpg --output output.json
```

I did not run this command.

`run.py` exposes a Fire CLI:

- Accepts `path`, `output`, and optional `verbose`.
- Imports `ci2n.app.main`.
- Calls `main(path, output, verbose)`.

`ci2n.app.main` hardcodes model paths:

- `./models/yolo_model.pt`
- `./models/item_classifier.h5`
- `./models/junction_classifier.pt`

It also hardcodes the verbose artifact directory:

- `verbose/`

## End-to-End Pipeline

The main function `circuit_image_to_netlist` performs these steps:

1. Select Torch device:
   - Uses `cuda:0` if available, otherwise CPU.

2. Configure logging:
   - If `verbose=False`, uses `FakeLogger`.
   - If `verbose=True`, uses Loguru and writes debug artifacts under `verbose/<timestamp>/`.

3. Load models:
   - YOLO model for device detection.
   - Keras model for orientation classification.
   - PyTorch model for junction classification.

4. Run YOLO on the input image:
   - Each detected box is converted into a `Device`.
   - Device names are generated as `<device_type>:<index>`, for example `nmos:0`.

5. Infer device direction and ports:
   - `get_device_direction_and_ports` classifies supported device orientation.
   - `get_device_ports` assigns named ports based on the device type and direction.

6. Build skeleton image:
   - Convert image to grayscale.
   - Apply Otsu thresholding with inverted binary output.
   - Skeletonize the binary image so wires become one-pixel-wide lines.

7. Replace detected devices with rectangles in the skeleton image:
   - Device interiors are removed.
   - Bounding boxes are drawn to preserve connection structure.

8. Remove small connected components:
   - Uses OpenCV connected-component statistics.
   - Filters components smaller than `largest_component_area // 20`.
   - The paper describes this as removing text/noise/interference.

9. Remove detected devices from skeleton:
   - Produces a wire/junction-focused skeleton.

10. Detect junction locations:
    - A skeleton pixel is a junction candidate if its 3x3 neighborhood contains more than three white pixels.
    - Connected junction candidate pixels are merged by centroid.

11. Classify junctions:
    - Crop 48x48-ish local junction images.
    - Draw red square context.
    - Normalize with hardcoded mean/std.
    - Run PyTorch classifier.
    - Junction classes are `circle`, `flat`, `bridge`, or `others`.

12. Infer image crossing style:
    - If any `bridge` is present, bridges are treated as non-connected jumpers.
    - Else if both `circle` and `flat` are present, flats are treated as non-connected jumpers.
    - Otherwise no junction type is preserved as a jumper.

13. Convert selected junctions to virtual bridge devices:
    - Each retained jumper gets virtual ports based on out-degree around its local square.
    - These are added as `bridge:<index>` devices.

14. Remove devices and virtual junctions from the skeleton:
    - Produces a skeleton where remaining connected domains are wires.

15. Find wires:
    - Searches around each device bounding box with a margin.
    - Uses stack-based flood fill across 8-neighbor skeleton pixels.

16. Convert wires to graph connections:
    - For each wire, find device ports near wire pixels.
    - Build pairwise graph edges between ports touched by the same wire.
    - Use igraph connected components to turn those graph edges into connection sets.

17. Apply jumper logic:
    - For each virtual bridge, ports are sorted clockwise and paired with opposite ports.
    - The nets connected to opposite virtual bridge ports are merged.
    - Bridge devices are removed from the final circuit.

18. Convert circuit to JSON:
    - For each remaining device, emit `component_type` and `port_connection`.
    - Connections are named using generated letters.

## Inputs

Runtime input:

- An image path passed through `--path`, e.g. `img.jpg`.
- The image is read by OpenCV using `cv2.imread`.
- The implementation expects a normal image array in OpenCV BGR format.

Model inputs:

- YOLO receives the full image.
- The Keras orientation model receives cropped component images resized to 150x150.
- The PyTorch junction classifier receives cropped junction feature images resized to 48x48 and normalized.

Static inputs:

- Pretrained model weights in `models/`.
- Hardcoded normalization constants for the junction classifier.
- Device-class mapping in `ci2n/items.py`.

## Outputs

Primary output:

- The file path passed by `--output`.
- Contents are JSON produced by `circuit_to_json`.

Verbose outputs when `verbose=True`:

- Directory: `verbose/<YYYY-MM-DD_HH-MM-SS>/`
- Intermediate artifacts include:
  - YOLO result image.
  - Skeleton image.
  - Skeleton with item rectangles.
  - Skeleton after small component removal.
  - Skeleton without items.
  - Junction visualization.
  - Junction feature crops.
  - Junction out-degree feature crops.
  - All devices/junctions/ports visualization.
  - Skeleton without items and junctions.
  - Detected line visualization.
  - Connection visualization.
  - Connection visualization after junction logic.
  - Final output JSON copy.

## Data Model

`Port`:

- `top_left`: coordinate tuple.
- `bottom_right`: coordinate tuple.

`Device`:

- `device_type`: enum.
- `ports`: map of port name to `Port`.
- `top_left`, `bottom_right`: detected bounding box.
- `direction`: one of `u`, `d`, `l`, `r`.
- `mirror`: integer, currently stored but not meaningfully used in the code path reviewed.

`Connection`:

- `ports`: frozen set of `(device_name, port_name)` tuples.
- Hash/equality defined by the port frozenset.

`Circuit`:

- `devices`: map of generated device names to devices.
- `connections`: set of `Connection`.

`Junction`:

- `location`: image coordinate.
- `junction_type`: `circle`, `flat`, `bridge`, or `others`.
- `feature_img`: cropped image around junction.
- `ports`: list of virtual ports.

## Device Coverage in Code

`DeviceType` defines many component types, including MOS, BJT, passives, sources, amplifiers, switches, antenna, and bridge-like virtual devices.

However, the current port assignment implementation only properly handles:

- MOS-like types in `MosTypes`.
- `gnd`.
- `port`.

For other detected device types, `get_device_direction_and_ports` and/or `get_device_ports` raises `ValueError`, which is caught in `app.py` with a warning. The device remains in the circuit but may have no usable ports, which means it may not participate correctly in final connectivity.

This is an important implementation limitation compared with the broader device coverage described in the paper.

## Notable Implementation Details and Risks

- The README says `poetry update`, but for reproducibility `poetry install` is usually safer because it follows `poetry.lock`; `poetry update` may resolve newer dependencies.
- The hardcoded model paths assume the command is run from repository root.
- Actual model binaries are missing because Git LFS content has not been fetched.
- `paper.pdf` is untracked.
- `models/*.pt` and `models/*.h5` are LFS pointer files in the working tree.
- `git-lfs` is required but not installed.
- `add_connection` in `line_algo.py` prints Chinese debug text, but it appears unused in the main connection path.
- Some counters in `get_connections` (`count`, `count2`, `count3`, `count4`) are incremented but not used.
- `remove_small_connected_components` can fail if no connected components exist after thresholding because it calls `.max()` on `stats[:, 4][1:]`.
- `get_connections` builds `ig.Graph.TupleList(connections_graph, directed=False)`. If no connections are found, behavior should be checked before relying on it.
- `Connection.ports` is typed as `FrozenSet`, but `junction_logic` mutates `NET1.ports` and `NET2.ports` with `-=`, which relies on Pydantic/model mutability behavior and should be tested carefully.
- Net names are generated from set iteration order, so output net labels may not be stable across runs even if topology is identical.
- The generated JSON omits device instance names and bounding boxes; it returns a list of component objects only.

## Practical Run Preconditions

Before running conversion:

1. Install/fetch Git LFS model binaries.
2. Confirm real model files are present, not pointer files.
3. Activate the environment:

```bash
conda activate image2net-ci2n
```

4. Optionally set writable config dirs:

```bash
export MPLCONFIGDIR=/tmp/matplotlib
export YOLO_CONFIG_DIR=/tmp/ultralytics
```

5. Run from repository root because model paths are relative:

```bash
python run.py --path img.jpg --output output.json
```

Again, this command was not run during setup/review.

---

## Follow-up Questions and Answers

These answers address the specific doubts raised after the initial repository review.

### 1. Does it run complete training again, or does it import weights and run inference?

It does not run training. The local `ci2n` repository is an inference pipeline.

Evidence from the code:

- `ci2n/app.py` loads three pretrained model files:
  - `YOLO(str(settings.yolo_model_path))`
  - `tf.keras.models.load_model(str(settings.item_classifier_model_path))`
  - `torch.load(settings.junction_classifier_model_path)`
- The code then immediately runs those models on the input image or image crops.
- There are no local training scripts, no optimizer setup, no dataset loader for training, and no training loop in this repository.

So the runtime flow is:

1. Load pretrained weights from `models/`.
2. Run model inference for device detection, device orientation, and junction classification.
3. Use classical CV and graph logic to produce the final netlist JSON.

The datasets mentioned in the paper are for training/evaluation of the published framework, but this local repository only contains the inference code and LFS pointers to trained weights.

### 2. How do I verify whether the generated netlist is correct?

There are three levels of verification.

First, visual/manual verification:

- Run with `verbose=True`.
- Inspect the debug images under `verbose/<timestamp>/`.
- Check whether detected devices, ports, wires, junctions, and final colored connections match the source schematic.
- Compare the generated output JSON against the circuit topology manually.

Second, compare against a ground-truth netlist:

- If you have the correct/reference netlist for the same image, compare each component type and each port's net assignment.
- Device names and net names do not need to be identical, but topology must be equivalent. For example, generated net `a` may correspond to reference net `net3`; the actual question is whether the same ports are grouped together.

Third, use the paper's benchmark method:

- The paper uses Netlist Edit Distance (NED), derived from Graph Edit Distance (GED).
- The netlists are converted into heterogeneous graphs containing devices, nets, ports, and typed port-to-net edges.
- A perfect result has `NED = 0`.
- Nonzero NED means some edit operations are needed to transform the generated graph into the ground-truth graph.

The separate public dataset repository `https://github.com/LAD021/ci2n_datasets` currently includes a `validation/` dataset area with:

- `golden/`: ground-truth circuit JSON files.
- `images/`: corresponding circuit images.
- `calc_ged.py`, `utils_ged.py`, `my_networkx.py`: GED/NED-style validation utilities.

That validation repository is the most direct way to reproduce paper-style correctness checks, but it is separate from this local `ci2n` inference repository.

### 3. How do I import the weights and make it ready to run?

There is no special Python import step. The code already knows where to load weights from. You only need the real model binary files at these exact paths:

```text
models/yolo_model.pt
models/item_classifier.h5
models/junction_classifier.pt
```

Currently, those three files are Git LFS pointer files, not real model binaries. The expected real sizes are:

```text
models/yolo_model.pt: 273253617 bytes
models/item_classifier.h5: 228476192 bytes
models/junction_classifier.pt: 44777446 bytes
```

To make the repository ready:

1. Install Git LFS.

On Ubuntu/Debian-style systems:

```bash
sudo apt install git-lfs
```

Alternative with conda-forge:

```bash
conda install -c conda-forge git-lfs
```

2. Initialize Git LFS and fetch the binary model files:

```bash
git lfs install
git lfs pull
```

3. Verify the files are no longer tiny text pointers:

```bash
file models/yolo_model.pt models/item_classifier.h5 models/junction_classifier.pt
du -h models/yolo_model.pt models/item_classifier.h5 models/junction_classifier.pt
```

4. Run from the repository root so the hardcoded relative paths resolve:

```bash
conda activate image2net-ci2n
python run.py --path img.jpg --output output.json
```

I have not run this command yet, per the original instruction not to run repository programs.

### 4. The paper says 2914 images. Where are those images from, and are they available?

They are not present in this local `ci2n` repository. This repository contains code and model pointers only.

The paper says the 2914 complete circuit images were collected from:

- textbooks/books,
- academic papers,
- the internet/web sources,
- and related manually prepared sources.

The paper also says the dataset is open-sourced. The corresponding public dataset repository is:

```text
https://github.com/LAD021/ci2n_datasets
```

The currently visible dataset repository is organized into:

```text
device_identification/
device_orientation/
jumper_identification/
validation/
```

The dataset repository README currently describes:

- `device_identification`: component detection/classification data.
- `device_orientation`: orientation classification crops organized by class folders.
- `jumper_identification`: train/validation images and labels for jumper/crossing-related detection.
- `validation`: images, golden netlist JSON files, and GED calculation scripts.

Important discrepancy:

- The paper reports 2914 complete circuit images and 84195 annotations.
- The currently visible GitHub dataset README says `device_identification` has 900 PNG circuit diagrams, `jumper_identification` has 500+ images, and `validation` has 127 images / 65 golden JSON files.

So the public dataset repository appears available, but the README counts visible today do not exactly match the paper's 2914-image claim. Possible explanations are that the public repository is a subset, the README is stale, files are stored in Git LFS, or the paper and repo versions are not synchronized.

To access the dataset:

```bash
git clone https://github.com/LAD021/ci2n_datasets.git
cd ci2n_datasets
```

If large files are LFS-managed there too:

```bash
git lfs install
git lfs pull
```

### 5. Can we give our own image apart from those dataset images?

Yes. The CLI accepts any image path:

```bash
python run.py --path your_image.jpg --output output.json
```

The input is read with `cv2.imread`, so common OpenCV-readable formats such as JPG and PNG should work.

Practical constraints:

- The image should look like the circuit diagram styles the models were trained on.
- The code assumes the model can detect known component classes.
- Very different drawing styles, low-resolution screenshots, handwritten diagrams, text-heavy figures, nonstandard symbols, rotated pages, or components unsupported by the current port logic may reduce accuracy.
- The implementation currently assigns ports robustly only for MOS-like devices, `gnd`, and `port`; broader component coverage is defined in enums but not fully implemented in the local port-assignment logic.

### 6. The paper claims a final successful rate of 80.77%. What does that mean?

The paper defines successful rate as:

```text
Successful Rate = Nsuccess / Ntotal
```

In this context, a "success" means the generated netlist matches the manually labeled ground-truth netlist for a test case. The paper also explains that if the result is completely correct, `NED = 0`.

So an 80.77% successful rate means:

- On their benchmark/evaluation set, about 80.77% of tested circuit images were converted into fully correct netlists under their graph/netlist equivalence check.
- The remaining cases had some topology, device, port, or net-connection error.
- This is not a per-component accuracy. It is stricter: one significant topology error can make an entire circuit case unsuccessful.

The paper reports the evaluation set has 104 manually verified image/netlist pairs. If 80.77% is computed over 104 cases, that corresponds to about 84 successful cases out of 104.

The paper also reports average NED to quantify how wrong the failed or imperfect cases are. Lower NED means the generated netlists are closer to ground truth.

### 7. How does the netlist/graph equivalence check and GED/NED validation work?

The core idea is that two netlists can be electrically/topologically equivalent even if they use different instance names or net names. For example, one output may call a wire `a` while the ground truth calls the same wire `net7`. A direct string comparison would incorrectly mark that as different. The paper avoids this by converting both netlists into graphs and comparing graph structure.

The validation process works like this:

1. Parse the generated netlist and the ground-truth netlist.

   The generated output from this repo is a JSON list of components:

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

2. Normalize names that should not matter.

   Device instance names and net names are not treated as the main source of truth. What matters is:

   - what type each component is,
   - what ports it has,
   - which ports are connected to the same net,
   - and what port role each connection represents.

   This is why arbitrary generated net names like `a`, `b`, `c` can still be correct.

3. Normalize equivalent ports.

   Some physical ports are interchangeable. The paper explicitly handles this so the evaluator does not punish harmless naming swaps. Examples from the paper:

   - MOS drain/source are treated as interchangeable and renamed to a shared role like `D_S`.
   - Passive component positive/negative ports are treated as interchangeable.
   - Some source ports are similarly normalized, except for cases such as `voltage_lines`.

   This matters because many schematic symbols do not make source/drain or passive polarity uniquely meaningful.

4. Convert each netlist into a heterogeneous graph.

   The graph contains multiple kinds of nodes:

   - component nodes, such as `NMOS`, `PMOS`, `resistor`, `capacitor`, etc.
   - net nodes, representing electrical networks/wires.

   The graph contains typed edges:

   - an edge connects a component node to a net node,
   - the edge type stores the port role, such as `NMOS_Gate`, `NMOS_D_S`, `PMOS_Gate`, `resistor_Port`, etc.

   So a transistor gate connected to net `a` becomes an edge from the NMOS node to the net node with edge type `NMOS_Gate`.

5. Compare the generated graph with the golden graph.

   Two graphs are considered exactly equivalent if there is an isomorphism between them after considering:

   - node types,
   - edge/port types,
   - and topology.

   This allows node names to differ while still requiring the same circuit structure.

6. Compute Graph Edit Distance (GED).

   GED is the minimum number of edit operations needed to transform the generated graph into the golden/reference graph.

   Edit operations include:

   - inserting a missing node,
   - deleting an extra node,
   - substituting an incorrect node type,
   - inserting a missing edge,
   - deleting an extra edge,
   - substituting an incorrect edge/port type.

   In the paper, each operation has cost `1`.

   Examples:

   - If an NMOS is incorrectly recognized as a PMOS, that can cause a node substitution and several edge substitutions.
   - If a drain is connected to the wrong net, that can cause an edge deletion plus an edge insertion.
   - If a component is missed entirely, that causes node and edge deletions relative to the golden graph.

7. Compute Netlist Edit Distance (NED).

   NED normalizes GED by circuit size:

   ```text
   NED = GED / (Ndevice + Nnet + Nport)
   ```

   where:

   - `Ndevice` is the number of devices in the golden netlist,
   - `Nnet` is the number of nets in the golden netlist,
   - `Nport` is the number of ports in the golden netlist.

   This normalization matters because a GED of `3` is severe for a tiny circuit but relatively smaller for a large circuit.

8. Decide whether the whole case is successful.

   A case is successful when the generated graph is exactly equivalent to the golden graph. Practically, that means:

   ```text
   GED = 0
   NED = 0
   ```

   Any nonzero GED/NED means the generated netlist has at least one structural or typing error.

The public dataset repository's validation area (`ci2n_datasets/validation/`) contains scripts named:

- `calc_ged.py`
- `utils_ged.py`
- `my_networkx.py`

Based on the paper and filenames, these tools implement the graph conversion and GED/NED calculation workflow for generated-vs-golden netlist comparison. `my_networkx.py` likely exists because the paper says they invoked NetworkX's GED algorithm and made optimizations for speed. GED is computationally expensive, and the paper notes that graph edit distance is NP-hard, so benchmark runs may need timeouts or long per-case budgets.

In simple terms:

- String comparison asks: "Are these JSON files textually identical?"
- Netlist/graph equivalence asks: "Do these two JSON netlists describe the same circuit topology?"
- GED asks: "How many graph edits are needed to fix the generated circuit?"
- NED asks: "How large is that error after accounting for circuit size?"

### 8. Does NED require ground-truth netlists, and are the dataset JSON files ground truth or generated inference outputs?

Yes. GED/NED validation requires a reference/ground-truth netlist for each evaluated image.

Without ground truth, the tool can still generate a netlist, but it cannot know whether the result is correct. GED/NED are comparative metrics:

```text
generated netlist + golden netlist -> graph comparison -> GED/NED
```

I inspected the cloned dataset repository at:

```text
../ci2n_datasets
```

The dataset repository has these top-level folders:

```text
device_identification/
device_orientation/
jumper_identification/
validation/
```

The ground-truth netlists are in:

```text
validation/golden/
```

The corresponding validation images are in:

```text
validation/images/
```

In the local clone, I counted:

```text
validation/images/*.png: 122
validation/golden/*.json: 122
```

Every validation image has a matching golden JSON filename, and every golden JSON has a matching image filename.

Example ground-truth validation netlist format:

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

These `validation/golden/*.json` files are the golden/reference netlists used by the validation scripts. They are not generated by running the local `ci2n` inference code. The dataset README calls them "Ground truth circuit representations", and `validation/README.md` calls the directory "golden netlists". The paper says the evaluation set contains manually verified image/netlist pairs. So the most defensible interpretation is:

- these are human-authored or human-verified ground-truth netlists,
- they are meant to evaluate model/system outputs,
- they are not inference outputs from the system being evaluated.

The exact authoring workflow is not fully documented in the README. It does not say whether the authors manually wrote the JSON directly, converted from manually written SPICE/Spectre, or corrected an automatic draft. But they are clearly intended as golden labels.

The JSON files in:

```text
device_identification/
```

are different. In the local clone, I counted:

```text
device_identification/*.png: 2269
device_identification/*.json: 2269
```

Those JSON files are not netlists. They are LabelMe-style object-detection annotations for component bounding boxes.

Example `device_identification/0.json` structure:

```json
{
  "version": "5.1.1",
  "flags": {},
  "shapes": [
    {
      "label": "port",
      "points": [[437.0, 19.0], [456.0, 38.0]],
      "shape_type": "rectangle"
    },
    {
      "label": "resistor",
      "points": [[597.0, 298.0], [668.0, 339.0]],
      "shape_type": "rectangle"
    }
  ],
  "imageHeight": 400,
  "imageWidth": 800
}
```

I checked the repository contents:

```text
device_identification JSON files containing "ckt_netlist": 0
device_identification JSON files containing "shapes": 2269
validation/golden JSON files containing "ckt_netlist": 122
```

So:

- `device_identification/*.json` = ground-truth bounding-box annotations for training/evaluating component detection.
- `validation/golden/*.json` = ground-truth netlists for GED/NED validation.

The validation tool in `validation/calc_ged.py` expects a directory of generated output JSON files and compares them against `validation/golden` by filename:

```bash
uv run python calc_ged.py \
  --input_dir <input_dir> \
  --golden_dir golden \
  --output_dir <output_dir> \
  --timeout <timeout>
```

For example, if `validation/golden/001.json` exists, then your generated result should be placed as:

```text
<input_dir>/001.json
```

The script then:

1. Reads `<input_dir>/<case>.json`.
2. Reads `golden/<case>.json`.
3. Converts both JSON netlists into heterogeneous graphs with `HeteroGraph.generate_all_from_json`.
4. Checks graph isomorphism first.
5. If not isomorphic, runs the modified NetworkX GED algorithm.
6. Writes per-case GED values to `<output_dir>/result.json`.

One important compatibility issue: the current local `ci2n` inference repo outputs a bare JSON list:

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

The dataset validation tool expects wrapped validation JSON:

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
    "ckt_type": "..."
}
```

Therefore, the raw output of this local `ci2n` repo may not be directly accepted by the validation tool without an adapter. At minimum, an adapter would need to:

- wrap the output list under `ckt_netlist`,
- add a `ckt_type` field,
- map component names from local enum names such as `nmos` to validation names such as `NMOS`,
- map local port names such as `g`, `ds1`, `ds2` to validation names such as `Gate`, `Drain`, `Source`,
- and possibly handle source/drain ambiguity consistently with the validation graph logic.

Also, the validation script currently reports GED values. I did not find direct NED calculation in `validation/calc_ged.py`; NED is the paper-level normalization:

```text
NED = GED / (Ndevice + Nnet + Nport)
```

So to reproduce NED exactly, one would compute GED with the provided script and then normalize by the ground-truth circuit size.

### 9. Example: run inference on `inputs/006.png` and save output under `outputs/`

Assume the local `ci2n` repository contains:

```text
inputs/006.png
models/yolo_model.pt
models/item_classifier.h5
models/junction_classifier.pt
```

and the model files are real Git LFS-fetched binaries, not pointer text files.

From the `ci2n` repository root:

```bash
cd ci2n
conda activate image2net-ci2n
mkdir -p outputs
python run.py --path inputs/006.png --output outputs/006.json
```

To run with verbose/debug artifacts enabled:

```bash
python run.py --path inputs/006.png --output outputs/006.json --verbose=True
```

To suppress most logging and intermediate image saves:

```bash
python run.py --path inputs/006.png --output outputs/006.json --verbose=False
```

Expected primary output:

```text
outputs/006.json
```

If `verbose=True`, the program also writes intermediate debug artifacts under:

```text
verbose/<timestamp>/
```

Run from repository root because `ci2n/app.py` hardcodes relative model paths:

```text
./models/yolo_model.pt
./models/item_classifier.h5
./models/junction_classifier.pt
```

If you run from another directory, those model paths may not resolve unless you adjust the code or launch command accordingly.
