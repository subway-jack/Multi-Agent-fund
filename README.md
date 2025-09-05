# Agentic World Model

The Agentic World Model (AWM) library provides an end‑to‑end pipeline for generating, executing, and evaluating code‑world models (CWMs) that serve as interactive environments for both the CWMB and ByteSized32 benchmarks. It is designed to test large‑language‑model planning agents on in‑context code generation tasks in a reproducible, gym‑style fashion.

## Directory Overview

**🛠️ code-world-models/**  
├─ **📄 data/prompts/**      – Predefined prompts for 18 Gymnasium environments  
└─ **⚙️ src/experiments/**  – Driver scripts for AWM and Baseline-MCTS pipelines  

**📝 ByteSized32/**  
├─ **📊 data/**             – CSV experiment definitions and benchmark specs  
└─ **🔧 scripts/**          – Helper scripts for code generation, reflection, and evaluation  

**🤖 src/**  
├─ **🔬 deep_research_agent/**   – “Deep Research” agent implementation  
└─ **🌐 agentic_world_model/**   – Core Agentic World Model logic  

**📈 results/**  
– Auto-generated CWMs, episode logs, and analysis artifacts  

# Quick‑Start

## Installation

```bash
conda create -n agenticworldmodel python=3.10
conda activate agenticworldmodel
pip install -r requirements.txt 
(cd ByteSized32 && pip install -e .)
(cd code-world-models/RTFM && pip install -e .)
```

## Generate a CWMB Environment

### Agentic World Model (AWM)

```bash
# Generate CWMs for env indices 0,1,2
python3 code-world-models/src/experiments/run_agentic_world_model_cwm.py \
--idx 0,1,2\
--model "deep research" \
--save_dir "results/cwm/agentic_world_model"
```

*Omit `--idx` and `--env` to process all 18 default tasks.*

### Baseline-MCTS

```bash
# Generate CWMs for env indices 0,1
python3 code-world-models/src/experiments/run_mcts_cwm.py \
--idx 0,1 \
--model gpt-4.1 \
--save_dir "results/cwm/mcts"
```

## Evaluate Planning Performance

After CWMs are generated, evaluate how well each planner solves the tasks.

### Agentic World Model (AWM)

```bash
python code-world-models/src/experiments/eval_planning.py \
--save_dir results/awm \
--experiment_name "agentic_world_model" \
--n_episodes 10
```

- `--save_dir` Point to the directory where the CWM JSONs were saved.
- `--experiment_name` Name of the method or model that generated the code environments to be evaluated.
- `--n_episodes` controls how many episodes to run per environment (default here: 10).

### Baseline-MCTS

```bash
python code-world-models/src/experiments/eval_planning.py \
--save_dir results/mcts \
--experiment_name "mcts" \
--n_episodes 10
```

## Analyze Results

To get a detailed analysis of the evaluation results, including success rates and average scores, run the analysis script:

```bash
python3 code-world-models/analyze_results.py \
code-world-models/results/cwm/results.json
```

## Experiments with bytesized32

### Code Generation

With the generated CSV files, run the following to generate code for each experiment:

#### Agentic World Model (AWM)

```bash
python ByteSized32/scripts/run_code_generate_agentic_world_model.py ByteSized32/data/experiment_action.csv \
  --output-folder results/bytes32/agentic_world_model \
  --model gpt-4.1

python ByteSized32/scripts/run_code_generate_agentic_world_model.py ByteSized32/data/experiment_distractor.csv \
  --output-folder results/bytes32/agentic_world_model \
  --model gpt-4.1

python ByteSized32/scripts/run_code_generate_agentic_world_model.py ByteSized32/data/experiment_object.csv \
  --output-folder results/bytes32/agentic_world_model \
  --model gpt-4.1
```

#### Baseline-code

```bash
python ByteSized32/scripts/run_code_generation.py ByteSized32/data/experiment_action.csv \
  --output-folder results/bytes32/code \
  --model gpt-4.1

python ByteSized32/scripts/run_code_generation.py ByteSized32/data/experiment_distractor.csv \
  --output-folder results/bytes32/code \
  --model gpt-4.1

python ByteSized32/scripts/run_code_generation.py ByteSized32/data/experiment_object.csv \
  --output-folder results/bytes32/code \
  --model gpt-4.1
```

### Code Reflection

Some generated games may not be valid Python code. Use the following script to perform self-reflection and improve code validity:

```bash
python scripts/run_code_reflection.py --game-folder results/run/generated_games/ \
  --revision-folder results/run/revised_games/
```

### Automatic Evaluation

The codebase supports automatic evaluation of the generated games based on the following metrics:

- Technical Validity: Whether the game is valid Python code with the expected classes and methods.
- Specification Compliance: Whether the required actions, objects, and distractors are present as specified in the experiment file.
- Physical Reality Alignment: Whether the game correctly models constraints of the physical world.
- Game Winnability: Whether a winning sequence of actions exists.

#### Agentic World Model (AWM)

```bash
python ByteSized32/scripts/run_code_evaluation.py \
--game-folder results/bytes32/agentic_world_model \
--results-file "results/bytes32/eval_agentic_results.json"
```

#### Baseline-code

```bash
python ByteSized32/scripts/run_code_evaluation.py \
  --game-folder results/bytes32/code \
  --results-file "results/bytes32/eval_code_results.json"
```

### Visualize Results

```bash
python scripts/make_table2.py --results results/bytes32/eval_agentic_results.json
python scripts/make_table3.py --results results/bytes32/eval_agentic_results.json
python scripts/make_figure4.py --results results/bytes32/eval_agentic_results.json
```
# Test change
