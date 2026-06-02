# Image2Net

This repository contains the Image2Net/CI2N code, dataset repository contents, and the reference research paper for converting analog circuit diagram images into circuit netlists.

It includes a complete setup guide for installing the conda environment, downloading Git LFS model weights, preparing inputs/outputs, and running CI2N inference.

The complete `image2net` folder contains:

```text
image2net/
  ci2n/
  ci2n_datasets/
  paper.pdf
  README.md
```

The executable CI2N code is inside `ci2n/`. The dataset material is inside `ci2n_datasets/`.

## 1. Important Git LFS Note For Model Weights

The CI2N model weights are large files:

```text
ci2n/models/yolo_model.pt
ci2n/models/item_classifier.h5
ci2n/models/junction_classifier.pt
```

These files must be handled with Git LFS when uploading this parent `image2net` repo to GitHub.

Normal GitHub has a hard file-size limit of 100 MB. Two of the model files are larger than that, so a normal `git add . && git push` will fail unless the weights are tracked through Git LFS.

## 2. Preparing This Parent Repo For GitHub

Run these commands from the parent `image2net` folder:

```bash
cd /home/harsh/Desktop/Project_Competitions/Silicon_Talks/image2net
```

Check whether there are nested Git repositories:

```bash
find . -name .git -type d
```

For one combined GitHub repo, only the parent `image2net/.git` should exist. If `ci2n/.git` or `ci2n_datasets/.git` exist, remove only those inner Git metadata folders before committing the parent repo:

```bash
rm -rf ci2n/.git
rm -rf ci2n_datasets/.git
```

Install and initialize Git LFS:

```bash
git lfs install
```

Track the model-weight file types:

```bash
git lfs track "*.pt"
git lfs track "*.h5"
```

This creates or updates `.gitattributes`. Make sure `.gitattributes` is committed.

Check the LFS rules:

```bash
cat .gitattributes
```

Expected rules should include:

```text
*.pt filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
```

Now initialize Git if the parent folder is not already a valid repo:

```bash
git init
git branch -M main
```

If `git status` says this is not a Git repository even though an `image2net/.git` directory exists, inspect it:

```bash
ls -la .git
```

If it is empty and you do not need any existing parent-repo history, remove that empty `.git` directory and initialize again:

```bash
rm -rf .git
git init
git branch -M main
```

Add files:

```bash
git add .gitattributes
git add .
git status
```

Before committing, confirm the model files are staged as LFS objects:

```bash
git lfs ls-files
```

You should see entries for:

```text
ci2n/models/yolo_model.pt
ci2n/models/item_classifier.h5
ci2n/models/junction_classifier.pt
```

Commit:

```bash
git commit -m "Initial Image2Net repository"
```

Create an empty GitHub repository, then connect and push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/image2net.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

If the weight files were already committed once without LFS, do not simply add LFS afterward. You must rewrite that Git history with:

```bash
git lfs migrate import --include="*.pt,*.h5"
```

Then force-push only if you understand the impact:

```bash
git push --force-with-lease
```

## 3. Cloning The Complete Repo Later

On a new machine, install Git LFS first:

```bash
sudo apt install git-lfs
git lfs install
```

Clone the parent repo:

```bash
git clone https://github.com/YOUR_USERNAME/image2net.git
cd image2net
```

Pull the real model binaries:

```bash
git lfs pull
```

Verify that the model files are real binaries, not small LFS pointer text files:

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

## 4. Create The Conda Environment

The CI2N repo declares Python `^3.9`, so we used Python 3.9.

```bash
conda create -y -n image2net-ci2n python=3.9 pip
conda activate image2net-ci2n
```

## 5. Install Runtime Dependencies

We installed the dependency stack directly into the conda environment using that environment's Python:

```bash
/home/harsh/miniconda3/envs/image2net-ci2n/bin/python -m pip install \
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

Note: the upstream `ci2n` README recommends Poetry, but this is the conda setup used for this local `image2net` workspace. Poetry is not required after these packages are installed in the conda environment.

## 6. Verify Dependency Installation

Run:

```bash
/home/harsh/miniconda3/envs/image2net-ci2n/bin/python -m pip check
```

Expected result:

```text
No broken requirements found.
```

Verify the core imports:

```bash
/home/harsh/miniconda3/envs/image2net-ci2n/bin/python -c "import sys, cv2, skimage, tensorflow, keras, torch, torchvision, ultralytics, urllib3; print('imports ok'); print('python', sys.version.split()[0]); print('cv2', cv2.__version__); print('skimage', skimage.__version__); print('tensorflow', tensorflow.__version__); print('keras', keras.__version__); print('torch', torch.__version__); print('torchvision', torchvision.__version__); print('ultralytics', ultralytics.__version__); print('urllib3', urllib3.__version__)"
```

The verified versions were:

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

## 7. Optional Config Directories

During import or runtime, Matplotlib and Ultralytics may warn if they cannot write to their default config folders. If needed, use writable temporary folders:

```bash
export MPLCONFIGDIR=/tmp/matplotlib
export YOLO_CONFIG_DIR=/tmp/ultralytics
```

## 8. Prepare Input And Output Folders

Run from the CI2N code folder:

```bash
cd /home/harsh/Desktop/Project_Competitions/Silicon_Talks/image2net/ci2n
mkdir -p inputs outputs
```

Example input path:

```text
ci2n/inputs/006.png
```

Example output path:

```text
ci2n/outputs/006.json
```

## 9. Run The CI2N Program

Run from the `ci2n` folder so the relative model paths resolve correctly:

```bash
cd /home/harsh/Desktop/Project_Competitions/Silicon_Talks/image2net/ci2n
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

Example:

```text
ci2n/verbose/2026-06-03_01-59-26/
```

## 10. CPU-Only Weight Loading Note

If the machine does not have CUDA available, PyTorch may fail when loading a model saved on CUDA unless the model is mapped to CPU.

The junction classifier load should use:

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

## 11. Common Startup Messages

TensorFlow may print messages like:

```text
oneDNN custom operations are on
Unable to register cuFFT factory
Unable to register cuDNN factory
Unable to register cuBLAS factory
TF-TRT Warning: Could not find TensorRT
```

These are usually environment/startup warnings. They do not necessarily mean CI2N failed. If the program fails, look for the later Python traceback.

## 12. Useful Checks

Check local changes:

```bash
git status --short
```

Check LFS files:

```bash
git lfs ls-files
```

Check installed packages:

```bash
/home/harsh/miniconda3/envs/image2net-ci2n/bin/python -m pip freeze
```
