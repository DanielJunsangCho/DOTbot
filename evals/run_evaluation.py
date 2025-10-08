"""Entry point for running evaluations."""

import argparse
import logging
from langsmith import Client

from .config import EvalConfig
from .dataset_creation import create_sample_dataset
from .evaluator import run_evaluation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for running evaluations."""
    parser = argparse.ArgumentParser(description="Run DOTbot evaluations")
    parser.add_argument(
        "--dataset",
        type=str,
        default="Sample dataset",
        help="Name of the dataset to evaluate on"
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="Create sample dataset before running evaluation"
    )
    parser.add_argument(
        "--experiment-prefix",
        type=str,
        default=None,
        help="Prefix for experiment name"
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=None,
        help="Maximum number of concurrent evaluations"
    )
    
    args = parser.parse_args()
    
    try:
        client = Client()
        
        # Create sample dataset if requested
        if args.create_sample:
            logger.info("Creating sample dataset...")
            dataset_id = create_sample_dataset(client)
            logger.info(f"Sample dataset created with ID: {dataset_id}")
        
        # Run evaluation
        logger.info(f"Starting evaluation on dataset: {args.dataset}")
        results = run_evaluation(
            dataset_name=args.dataset,
            experiment_prefix=args.experiment_prefix,
            max_concurrency=args.max_concurrency,
            client=client
        )
        
        logger.info("Evaluation completed successfully!")
        logger.info(f"Results: {results}")
        
    except Exception as e:
        logger.error(f"Error running evaluation: {e}")
        raise


if __name__ == "__main__":
    main()

