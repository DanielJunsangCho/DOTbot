"""Evaluation runner for DOTbot agent using LangSmith."""

from typing import Dict, Any, List, Callable, Optional
from langsmith import Client, wrappers
from langsmith.evaluation import evaluate
from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT
from openai import OpenAI
import logging

from .config import EvalConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_target_function(model: str = "gpt-4o-mini") -> Callable:
    """
    Create a target function that wraps the model for evaluation.
    
    Args:
        model: Model name to use
        
    Returns:
        Target function that takes inputs dict and returns outputs dict
    """
    # Wrap the OpenAI client for LangSmith tracing
    openai_client = wrappers.wrap_openai(OpenAI())
    
    def target(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Target function for evaluation."""
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Answer the following question accurately"},
                {"role": "user", "content": inputs["question"]},
            ],
        )
        return {"answer": response.choices[0].message.content.strip()}
    
    return target


def create_correctness_evaluator(model: str = "gpt-4o-mini") -> Callable:
    """
    Create a correctness evaluator using LLM as a judge.
    
    Args:
        model: Model name to use for evaluation
        
    Returns:
        Evaluator function
    """
    def correctness_evaluator(
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate correctness of outputs against reference."""
        evaluator = create_llm_as_judge(
            prompt=CORRECTNESS_PROMPT,
            model=f"openai:{model}",
            feedback_key="correctness",
        )
        eval_result = evaluator(
            inputs=inputs,
            outputs=outputs,
            reference_outputs=reference_outputs
        )
        return eval_result
    
    return correctness_evaluator


def run_evaluation(
    dataset_name: str,
    target_function: Optional[Callable] = None,
    evaluators: Optional[List[Callable]] = None,
    experiment_prefix: Optional[str] = None,
    max_concurrency: Optional[int] = None,
    client: Optional[Client] = None
) -> Any:
    """
    Run an evaluation experiment on a dataset.
    
    Args:
        dataset_name: Name of the dataset to evaluate on
        target_function: Function to evaluate (creates default if None)
        evaluators: List of evaluator functions (creates default if None)
        experiment_prefix: Prefix for experiment name
        max_concurrency: Max concurrent evaluations
        client: LangSmith client (creates new one if None)
        
    Returns:
        Evaluation results object
    """
    # Validate configuration
    EvalConfig.validate()
    
    if client is None:
        client = Client()
    
    if target_function is None:
        logger.info(f"Creating default target function with model: {EvalConfig.TARGET_MODEL}")
        target_function = create_target_function(EvalConfig.TARGET_MODEL)
    
    if evaluators is None:
        logger.info(f"Creating default correctness evaluator with model: {EvalConfig.EVALUATOR_MODEL}")
        evaluators = [create_correctness_evaluator(EvalConfig.EVALUATOR_MODEL)]
    
    experiment_prefix = experiment_prefix or EvalConfig.EXPERIMENT_PREFIX
    max_concurrency = max_concurrency or EvalConfig.MAX_CONCURRENCY
    
    logger.info(f"Running evaluation on dataset: {dataset_name}")
    logger.info(f"Experiment prefix: {experiment_prefix}")
    logger.info(f"Max concurrency: {max_concurrency}")
    
    try:
        # Run the evaluation
        experiment_results = client.evaluate(
            target_function,
            data=dataset_name,
            evaluators=evaluators,
            experiment_prefix=experiment_prefix,
            max_concurrency=max_concurrency,
        )
        
        logger.info("Evaluation complete!")
        logger.info(f"View results at: {experiment_results}")
        
        return experiment_results
        
    except Exception as e:
        logger.error(f"Error running evaluation: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    results = run_evaluation(
        dataset_name="Sample dataset",
        experiment_prefix="test-eval",
    )
    print(f"Evaluation results: {results}")
