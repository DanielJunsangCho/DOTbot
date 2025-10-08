# DOTbot Evaluations

This directory contains the evaluation framework for the DOTbot web scraping agent using LangSmith.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in your `.env` file:
```bash
LANGSMITH_API_KEY=your_api_key_here
LANGSMITH_PROJECT=dotbot-evals
OPENAI_API_KEY=your_openai_key_here
```

## Usage

### Creating a Dataset

```python
from evals.dataset_creation import create_dataset

examples = [
    {
        "inputs": {"question": "What is the capital of France?"},
        "outputs": {"answer": "Paris"},
    },
]

dataset_id = create_dataset("My Dataset", examples)
```

Or create a sample dataset:

```bash
python -m evals.dataset_creation
```

### Running Evaluations

Using the command-line interface:

```bash
# Run evaluation with sample dataset
python -m evals.run_evaluation --dataset "Sample dataset"

# Create sample dataset and run evaluation
python -m evals.run_evaluation --create-sample --dataset "Sample dataset"

# Custom experiment settings
python -m evals.run_evaluation \
    --dataset "My Dataset" \
    --experiment-prefix "my-experiment" \
    --max-concurrency 4
```

Using Python:

```python
from evals.evaluator import run_evaluation

results = run_evaluation(
    dataset_name="Sample dataset",
    experiment_prefix="my-eval"
)
```

## Configuration

Edit `config.py` to customize:
- Model settings
- Evaluation parameters
- Dataset defaults

## Structure

```
evals/
├── __init__.py           # Package initialization
├── README.md             # This file
├── config.py             # Configuration settings
├── dataset_creation.py   # Dataset creation utilities
├── evaluator.py          # Evaluation runner
├── run_evaluation.py     # CLI entry point
└── utils/                # Utility functions
    └── __init__.py
```

## Adding Custom Evaluators

Create a new evaluator function:

```python
def my_custom_evaluator(inputs, outputs, reference_outputs):
    # Your evaluation logic here
    return {"score": 1.0, "reasoning": "Evaluation passed"}

# Use it in evaluation
run_evaluation(
    dataset_name="My Dataset",
    evaluators=[my_custom_evaluator]
)
```

