# Image2Net Setup Guide

This repository contains the CI2N/Image2Net code, dataset files, and the reference paper for converting analog circuit diagram images into netlists.

Repository layout:

```text
image2net/
  ci2n/            # CI2N inference code
  ci2n_datasets/   # Dataset repository contents
  paper.pdf        # Reference research paper
  README.md        # This setup guide
```

The runnable code is inside `ci2n/`. Run CI2N commands from that folder unless stated otherwise.

## 1. Go To The Repository

```bash
git clone <repo-url>
cd image2net
```

## 2. Install Git LFS And Pull Model Weights

CI2N uses large model-weight files:

```text
ci2n/models/yolo_model.pt
ci2n/models/item_classifier.h5
ci2n/models/junction_classifier.pt
```

These are handled through Git LFS. Install Git LFS:

```bash
sudo apt install git-lfs
git lfs install
```

Pull the actual model binaries:

```bash
git lfs pull
```

Verify that the weights are real binaries and not tiny LFS pointer files:

```bash
file ci2n/models/yolo_model.pt ci2n/models/item_classifier.h5 ci2n/models/junction_classifier.pt
du -h ci2n/models/yolo_model.pt ci2n/models/item_classifier.h5 ci2n/models/junction_classifier.pt
```

Expected approximate sizes:

```text
ci2n/models/yolo_model.pt: about 273 MB
ci2n/models/item_classifier.h5: about 228 MB
ci2n/models/junction_classifier.pt: about 45 MB
```

## 3. Create The Conda Environment

The CI2N repo declares Python `^3.9`, so we used Python 3.9.

```bash
conda create -y -n image2net-ci2n python=3.9 pip
conda activate image2net-ci2n
```

## 4. Install Runtime Dependencies

Install the dependency stack directly into the conda environment using that environment's Python:

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

Note: the upstream `ci2n` README mentions Poetry. This repository was set up with the conda environment above and direct `pip` installs inside that environment.

## 5. Verify The Environment

Check dependency consistency:

```bash
python -m pip check
```

Expected result:

```text
No broken requirements found.
```

Verify core imports and versions:

```bash
python -c "import sys, cv2, skimage, tensorflow, keras, torch, torchvision, ultralytics, urllib3; print('imports ok'); print('python', sys.version.split()[0]); print('cv2', cv2.__version__); print('skimage', skimage.__version__); print('tensorflow', tensorflow.__version__); print('keras', keras.__version__); print('torch', torch.__version__); print('torchvision', torchvision.__version__); print('ultralytics', ultralytics.__version__); print('urllib3', urllib3.__version__)"
```

Verified versions:

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

## 6. Optional Config Directories

If Matplotlib or Ultralytics cannot write to their default config directories, set writable temporary directories:

```bash
export MPLCONFIGDIR=/tmp/matplotlib
export YOLO_CONFIG_DIR=/tmp/ultralytics
```

## 7. Prepare Input And Output Folders

Run from the CI2N code folder:

```bash
cd ci2n
mkdir -p inputs outputs
```

Place input circuit images inside `inputs/`.

Example:

```text
inputs/006.png
```

Generated netlists can be written to `outputs/`.

Example:

```text
outputs/006.json
```

## 8. Run CI2N

Run from the `ci2n` folder so the relative model paths resolve correctly:

```bash
cd ci2n
conda activate image2net-ci2n
```

Run inference:

```bash
python run.py --path inputs/006.png --output outputs/006.json
```

Run inference with verbose intermediate outputs:

```bash
python run.py --path inputs/006.png --output outputs/006.json --verbose=True
```

The main netlist output is saved to the path passed through `--output`.

Verbose artifacts are saved under:

```text
ci2n/verbose/<timestamp>/
```

## 9. CPU-Only Weight Loading Note

If the machine does not have CUDA available, PyTorch may fail when loading a model saved on CUDA unless the model is mapped to CPU.

The junction classifier should be loaded with `map_location`:

```python
junction_classifier_model = torch.load(
    settings.junction_classifier_model_path,
    map_location=torch_device,
).to(torch_device)
```

This avoids:

```text
RuntimeError: Attempting to deserialize object on a CUDA device but torch.cuda.is_available() is False
```

## 10. Common Startup Messages

TensorFlow may print messages like:

```text
oneDNN custom operations are on
Unable to register cuFFT factory
Unable to register cuDNN factory
Unable to register cuBLAS factory
TF-TRT Warning: Could not find TensorRT
```

These are usually environment/startup warnings. They do not necessarily mean CI2N failed. If the program fails, look for the later Python traceback.
