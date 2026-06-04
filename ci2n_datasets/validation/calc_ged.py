import fire
from pathlib import Path
import shutil
from functools import partial
from utils_ged import ged, HeteroGraph
import json

def process_one_task(task_id, input_dir: Path, golden_dir: Path, output_dir: Path, timeout=10):
    task_id = Path(task_id)
    
    input_path = input_dir / task_id
    golden_path = golden_dir / task_id
    output_dir = output_dir / task_id.stem
    
    input_json = input_path.read_text()
    golden_json = golden_path.read_text()
    
    ground_truth = HeteroGraph()
    
    _, input_graph, _= ground_truth.generate_all_from_json(json.loads(input_json))
    _, true_graph, _= ground_truth.generate_all_from_json(json.loads(golden_json)) 
    
    ged_value = ged(input_graph, true_graph, task_name=task_id.stem, timeout=timeout)
    
    return (task_id.stem, ged_value)

def main(input_dir: str = "./input", golden_dir: str = "./golden", output_dir: str = "./output", timeout: int = 60):
    input_dir = Path(input_dir)
    golden_dir = Path(golden_dir)
    output_dir = Path(output_dir)
    
    assert input_dir.is_dir(), f"input_dir <{input_dir}> must be a existing directory"
    assert golden_dir.is_dir(), f"golden_dir <{golden_dir}> must be a directory"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks = [task.name for task in golden_dir.glob("*.json")]
    print(f"Found {len(tasks)} tasks")
    
    process = partial(process_one_task, input_dir=input_dir, golden_dir=golden_dir, output_dir=output_dir, timeout=timeout)
    
    scores = []
    for index, task in enumerate(tasks, start=1):
        print(f"Processing {index}/{len(tasks)}: {task}", flush=True)
        scores.append(process(task))
        
    result = {
        id: score
        for id, score in scores
    }
    # sort by key
    result = dict(sorted(result.items()))
    
    (output_dir / "result.json").write_text(json.dumps(result, indent=4))
    
    

if __name__ == '__main__':
    fire.Fire(main)
