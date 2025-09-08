"""
CORE COMPONENT: API Contract Registry
====================================
Central contract management for cross-handler communication
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class APIEndpoint:
    """Structured API endpoint definition"""
    method: str
    path: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    authentication_required: bool = True
    rate_limit: int = 100
    description: str = ""
    handler_type: str = "backend"

@dataclass
class DataModel:
    """Structured data model definition"""
    name: str
    schema: Dict[str, Any]
    relationships: List[str] = None
    table_name: str = None
    indexes: List[str] = None
    constraints: List[str] = None

@dataclass
class FeatureContract:
    """Complete contract for a feature"""
    feature_name: str
    endpoints: List[APIEndpoint]
    models: List[DataModel]
    dependencies: List[str] = None
    security_requirements: List[str] = None
    created_by: str = None
    created_at: str = None

class APIContractRegistry:
    """Central registry for all API contracts"""
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path) if project_path else Path("/tmp")
        self.contracts_path = self.project_path / ".contracts"
        self.contracts_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory registries
        self.feature_contracts: Dict[str, FeatureContract] = {}
        self.endpoint_registry: Dict[str, APIEndpoint] = {}
        self.model_registry: Dict[str, DataModel] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # Context preservation for Claude
        self.generation_context: Dict[str, Any] = {
            "established_patterns": [],
            "architectural_decisions": [],
            "security_standards": [],
            "naming_conventions": {},
            "code_style_preferences": {}
        }
    
    def register_feature_contract(self, contract: FeatureContract):
        """Register complete contract for a feature"""
        contract.created_at = datetime.utcnow().isoformat()
        self.feature_contracts[contract.feature_name] = contract
        
        # Index endpoints
        for endpoint in contract.endpoints:
            key = f"{endpoint.method} {endpoint.path}"
            self.endpoint_registry[key] = endpoint
        
        # Index models
        for model in contract.models:
            self.model_registry[model.name] = model
        
        # Build dependency graph
        if contract.dependencies:
            self.dependency_graph[contract.feature_name] = set(contract.dependencies)
        
        # Persist to disk
        self._save_contract_to_disk(contract)
        
        logger.info(f"✅ Registered contract for feature: {contract.feature_name}")
    
    def get_feature_contract(self, feature_name: str) -> Optional[FeatureContract]:
        """Get contract for specific feature"""
        return self.feature_contracts.get(feature_name)
    
    def get_all_endpoints(self) -> List[APIEndpoint]:
        """Get all registered endpoints"""
        return list(self.endpoint_registry.values())
    
    def get_all_models(self) -> List[DataModel]:
        """Get all registered data models"""
        return list(self.model_registry.values())
    
    def validate_cross_stack_consistency(self) -> Dict[str, List[str]]:
        """Validate consistency across all contracts"""
        issues = {
            "missing_endpoints": [],
            "missing_models": [],
            "dependency_conflicts": [],
            "naming_conflicts": []
        }
        
        # Check for naming conflicts
        endpoint_paths = [ep.path for ep in self.endpoint_registry.values()]
        if len(endpoint_paths) != len(set(endpoint_paths)):
            issues["naming_conflicts"].append("Duplicate endpoint paths detected")
        
        # Check dependency cycles
        for feature, deps in self.dependency_graph.items():
            if self._has_circular_dependency(feature, deps):
                issues["dependency_conflicts"].append(f"Circular dependency in {feature}")
        
        return issues
    
    def get_context_for_handler(self, handler_type: str, feature: str) -> Dict[str, Any]:
        """Get relevant context for specific handler"""
        context = {
            "feature": feature,
            "existing_contracts": self.feature_contracts,
            "established_patterns": self.generation_context["established_patterns"],
            "architectural_decisions": self.generation_context["architectural_decisions"],
            "related_endpoints": [ep for ep in self.endpoint_registry.values() 
                                if ep.handler_type == handler_type],
            "related_models": [model for model in self.model_registry.values()],
            "naming_conventions": self.generation_context["naming_conventions"]
        }
        return context
    
    def update_generation_context(self, updates: Dict[str, Any]):
        """Update context for future generations"""
        for key, value in updates.items():
            if key in self.generation_context:
                if isinstance(self.generation_context[key], list):
                    self.generation_context[key].extend(value)
                else:
                    self.generation_context[key].update(value)
        
        # Persist context
        context_file = self.contracts_path / "generation_context.json"
        context_file.write_text(json.dumps(self.generation_context, indent=2))
    
    def _save_contract_to_disk(self, contract: FeatureContract):
        """Persist contract to disk for recovery"""
        contract_file = self.contracts_path / f"{contract.feature_name}_contract.json"
        contract_data = {
            "feature_name": contract.feature_name,
            "endpoints": [asdict(ep) for ep in contract.endpoints],
            "models": [asdict(model) for model in contract.models],
            "dependencies": contract.dependencies,
            "security_requirements": contract.security_requirements,
            "created_by": contract.created_by,
            "created_at": contract.created_at
        }
        contract_file.write_text(json.dumps(contract_data, indent=2))
    
    def _has_circular_dependency(self, feature: str, dependencies: Set[str], 
                                visited: Set[str] = None) -> bool:
        """Check for circular dependencies"""
        if visited is None:
            visited = set()
        
        if feature in visited:
            return True
        
        visited.add(feature)
        for dep in dependencies:
            if dep in self.dependency_graph:
                if self._has_circular_dependency(dep, self.dependency_graph[dep], visited):
                    return True
        
        visited.remove(feature)
        return False