"""
Base LangGraph node definition following CLAUDE.md standards.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from app.schemas import UnifiedState

logger = logging.getLogger(__name__)


class BaseLangGraphNode(ABC):
    """
    Abstract base class for LangGraph nodes following CLAUDE.md standards.
    
    Each node must explicitly define inputs, outputs, and completion criteria
    per CLAUDE.md requirements for explicit contracts.
    """
    
    # Explicit input/output contracts as required by CLAUDE.md
    inputs: Dict[str, type] = {}
    outputs: Dict[str, type] = {}
    
    def __init__(self, name: str):
        """
        Initialize base node with explicit naming.
        
        Args:
            name: Node identifier for traceability
        """
        self.name = name
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Validate contract definition
        if not self.inputs or not self.outputs:
            raise ValueError(f"Node {name} must define explicit input/output contracts")
        
        self.logger.info(f"Initialized {self.__class__.__name__} node: {name}")
    
    @abstractmethod
    async def process(self, state: UnifiedState) -> Dict[str, Any]:
        """
        Core processing logic for the node.
        
        Args:
            state: Current workflow state
            
        Returns:
            State updates to apply
            
        Raises:
            NotImplementedError: Must be implemented by concrete nodes
        """
        raise NotImplementedError("Subclasses must implement process method")
    
    async def __call__(self, state: UnifiedState) -> Dict[str, Any]:
        """
        Node execution wrapper with validation and error handling.
        
        Args:
            state: Current workflow state
            
        Returns:
            Validated state updates
            
        Raises:
            ValueError: On input validation failures
            RuntimeError: On processing failures
        """
        
        self.logger.info(f"Executing node {self.name}")
        
        try:
            # Validate inputs
            self._validate_inputs(state)
            
            # Execute core processing
            updates = await self.process(state)
            
            # Validate outputs
            self._validate_outputs(updates)
            
            # Add execution metadata
            updates.setdefault("step_history", state.step_history.copy()).append(self.name)
            updates["current_step"] = self.name
            
            self.logger.info(f"Node {self.name} completed successfully")
            return updates
            
        except Exception as e:
            self.logger.error(f"Node {self.name} failed: {e}")
            
            return {
                "success": False,
                "error": f"Node {self.name} failed: {str(e)}",
                "current_step": f"{self.name}_error",
                "step_history": state.step_history + [f"{self.name}_error"]
            }
    
    def _validate_inputs(self, state: UnifiedState) -> None:
        """
        Validate required inputs are present in state.
        
        Args:
            state: Current workflow state
            
        Raises:
            ValueError: On missing required inputs
        """
        
        for input_name, input_type in self.inputs.items():
            if not hasattr(state, input_name):
                raise ValueError(f"Missing required input: {input_name}")
            
            value = getattr(state, input_name)
            if value is None and input_type != Optional:
                raise ValueError(f"Required input {input_name} cannot be None")
    
    def _validate_outputs(self, updates: Dict[str, Any]) -> None:
        """
        Validate outputs match expected contract.
        
        Args:
            updates: Proposed state updates
            
        Raises:
            ValueError: On invalid outputs
        """
        
        for output_name, output_type in self.outputs.items():
            if output_name in updates:
                value = updates[output_name]
                
                # Basic type checking (could be enhanced with more sophisticated validation)
                if value is not None and output_type != Any:
                    try:
                        # Handle Optional types
                        if hasattr(output_type, '__origin__') and output_type.__origin__ is type(Optional[int].__origin__):
                            inner_type = output_type.__args__[0]
                            if not isinstance(value, inner_type):
                                raise ValueError(f"Output {output_name} type mismatch")
                        elif not isinstance(value, output_type):
                            raise ValueError(f"Output {output_name} expected {output_type}, got {type(value)}")
                    except (AttributeError, TypeError):
                        # Skip complex type validation for now
                        pass
    
    def get_contract(self) -> Dict[str, Dict[str, type]]:
        """
        Get node contract definition for documentation and validation.
        
        Returns:
            Node input/output contract specification
        """
        
        return {
            "inputs": self.inputs.copy(),
            "outputs": self.outputs.copy(),
            "node_name": self.name,
            "node_class": self.__class__.__name__
        }