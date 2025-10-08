"""Dataset creation utilities for LangSmith evaluations."""

from typing import List, Dict, Any, Optional
from langsmith import Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_dataset(
    dataset_name: str,
    examples: List[Dict[str, Any]],
    description: Optional[str] = None,
    client: Optional[Client] = None
) -> str:
    """
    Create a dataset in LangSmith with the provided examples.
    
    Args:
        dataset_name: Name of the dataset to create
        examples: List of dicts with 'inputs' and 'outputs' keys
        description: Optional description of the dataset
        client: Optional LangSmith client (creates new one if not provided)
        
    Returns:
        Dataset ID as a string
        
    Example:
        examples = [
            {
                "inputs": {"question": "What is the capital of France?"},
                "outputs": {"answer": "Paris"},
            },
        ]
        dataset_id = create_dataset("My Dataset", examples)
    """
    if client is None:
        client = Client()
    
    try:
        # Check if dataset already exists
        try:
            existing_dataset = client.read_dataset(dataset_name=dataset_name)
            logger.info(f"Dataset '{dataset_name}' already exists with ID: {existing_dataset.id}")
            return str(existing_dataset.id)
        except Exception:
            # Dataset doesn't exist, create it
            pass
        
        # Create the dataset
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=description or f"Dataset: {dataset_name}"
        )
        logger.info(f"Created dataset '{dataset_name}' with ID: {dataset.id}")
        
        # Add examples to the dataset
        client.create_examples(dataset_id=dataset.id, examples=examples)
        logger.info(f"Added {len(examples)} examples to dataset")
        
        return str(dataset.id)
        
    except Exception as e:
        logger.error(f"Error creating dataset: {e}")
        raise


def create_sample_dataset(client: Optional[Client] = None) -> str:
    """
    Create a sample dataset for testing evaluations.
    
    Args:
        client: Optional LangSmith client
        
    Returns:
        Dataset ID as a string
    """
    examples = [
        {
            "inputs": {"question": "Which country is Mount Kilimanjaro located in?"},
            "outputs": {"answer": "Mount Kilimanjaro is located in Tanzania."},
        },
        {
            "inputs": {"question": "What is Earth's lowest point?"},
            "outputs": {"answer": "Earth's lowest point is The Dead Sea."},
        },
    ]
    
    return create_dataset(
        dataset_name="Sample dataset",
        examples=examples,
        description="A sample dataset in LangSmith.",
        client=client
    )


if __name__ == "__main__":
    # Create sample dataset when run directly
    dataset_id = create_sample_dataset()
    print(f"Created dataset with ID: {dataset_id}")
