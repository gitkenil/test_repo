"""
BASE HANDLER: Technology Handler Interface
==========================================
Base class for all technology-specific handlers with context preservation
"""

import asyncio
import json
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class HandlerResult:
    """Result from handler code generation"""
    success: bool
    handler_type: str
    features_implemented: List[str]
    code_files: Dict[str, str]  # file_path -> content
    contracts: Dict[str, Any]   # contracts created
    quality_score: float
    tokens_used: int = 0
    generation_time: float = 0.0
    error_message: str = None
    refinement_cycles: int = 0

@dataclass
class ContextChunk:
    """Context chunk for Claude token management"""
    chunk_id: str
    chunk_type: str  # "architecture", "contracts", "previous_code", "feature_spec"
    content: str
    priority: int    # 1=critical, 2=important, 3=nice-to-have
    tokens_estimate: int
    created_at: str

class TechnologyHandler(ABC):
    """Base class for all technology handlers"""
    
    def __init__(self, contract_registry, event_bus, claude_client=None):
        self.contracts = contract_registry
        self.events = event_bus
        self.claude_client = claude_client
        
        # Handler configuration
        self.handler_type = "base"
        self.quality_threshold = 8.0
        self.max_refinement_cycles = 5
        self.max_tokens_per_request = 150000  # Conservative limit
        
        # Context management for Claude
        self.context_chunks: List[ContextChunk] = []
        self.generation_history: List[Dict[str, Any]] = []
        
        # Subscribe to relevant events
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions for this handler"""
        self.events.subscribe("generation_started", self._on_generation_started, self.handler_type)
        self.events.subscribe("contracts_established", self._on_contracts_established, self.handler_type)
        self.events.subscribe("quality_validation_required", self._on_quality_validation, self.handler_type)
    
    async def generate_code(self, features: List[str], context: Dict[str, Any], 
                          quality_target: float = 8.0) -> HandlerResult:
        """Main code generation method with context preservation"""
        
        start_time = datetime.utcnow()
        correlation_id = self.events.create_correlation_id()
        
        try:
            logger.info(f"🚀 {self.handler_type} handler starting generation for: {features}")
            
            # Step 1: Prepare context chunks for Claude
            context_chunks = await self._prepare_context_chunks(features, context)
            
            # Step 2: Generate code with chunked context
            initial_result = await self._generate_with_chunked_context(
                features, context_chunks, correlation_id
            )
            
            # Step 3: Validate and refine quality
            if initial_result.quality_score < quality_target:
                refined_result = await self._refine_until_quality_met(
                    initial_result, quality_target, correlation_id
                )
            else:
                refined_result = initial_result
            
            # Step 4: Register contracts and publish events
            await self._finalize_generation(refined_result, correlation_id)
            
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            refined_result.generation_time = generation_time
            
            logger.info(f"✅ {self.handler_type} generation completed: {refined_result.quality_score}/10 quality")
            return refined_result
            
        except Exception as e:
            logger.error(f"❌ {self.handler_type} generation failed: {e}")
            
            # Publish failure event
            await self.events.publish("handler_generation_failed", {
                "handler": self.handler_type,
                "features": features,
                "error": str(e)
            }, self.handler_type, correlation_id)
            
            return HandlerResult(
                success=False,
                handler_type=self.handler_type,
                features_implemented=[],
                code_files={},
                contracts={},
                quality_score=0.0,
                error_message=str(e)
            )
    
    async def _prepare_context_chunks(self, features: List[str], 
                                    context: Dict[str, Any]) -> List[ContextChunk]:
        """Prepare context chunks for Claude with token management"""
        
        chunks = []
        
        # Chunk 1: Critical architecture decisions (Priority 1)
        architecture_context = self._build_architecture_context(context)
        chunks.append(ContextChunk(
            chunk_id="architecture",
            chunk_type="architecture",
            content=architecture_context,
            priority=1,
            tokens_estimate=len(architecture_context) // 4,  # Rough estimate
            created_at=datetime.utcnow().isoformat()
        ))
        
        # Chunk 2: Existing contracts (Priority 1)
        contracts_context = self._build_contracts_context(features)
        chunks.append(ContextChunk(
            chunk_id="contracts",
            chunk_type="contracts", 
            content=contracts_context,
            priority=1,
            tokens_estimate=len(contracts_context) // 4,
            created_at=datetime.utcnow().isoformat()
        ))
        
        # Chunk 3: Previous generation history (Priority 2)
        if self.generation_history:
            history_context = self._build_history_context()
            chunks.append(ContextChunk(
                chunk_id="history",
                chunk_type="previous_code",
                content=history_context,
                priority=2,
                tokens_estimate=len(history_context) // 4,
                created_at=datetime.utcnow().isoformat()
            ))
        
        # Chunk 4: Feature specifications (Priority 1)
        feature_context = self._build_feature_context(features, context)
        chunks.append(ContextChunk(
            chunk_id="features",
            chunk_type="feature_spec",
            content=feature_context,
            priority=1,
            tokens_estimate=len(feature_context) // 4,
            created_at=datetime.utcnow().isoformat()
        ))
        
        return self._optimize_chunks_for_tokens(chunks)
    
    def _optimize_chunks_for_tokens(self, chunks: List[ContextChunk]) -> List[ContextChunk]:
        """Optimize chunks to fit within token limits"""
        
        # Sort by priority (1 = highest priority)
        chunks.sort(key=lambda x: x.priority)
        
        total_tokens = sum(chunk.tokens_estimate for chunk in chunks)
        
        if total_tokens <= self.max_tokens_per_request:
            return chunks
        
        # Remove lowest priority chunks until we fit
        optimized_chunks = []
        current_tokens = 0
        
        for chunk in chunks:
            if current_tokens + chunk.tokens_estimate <= self.max_tokens_per_request:
                optimized_chunks.append(chunk)
                current_tokens += chunk.tokens_estimate
            elif chunk.priority == 1:  # Always include critical chunks, truncate if needed
                truncated_content = chunk.content[:int((self.max_tokens_per_request - current_tokens) * 4)]
                chunk.content = truncated_content + "\n... [TRUNCATED FOR TOKEN LIMIT]"
                chunk.tokens_estimate = len(chunk.content) // 4
                optimized_chunks.append(chunk)
                break
        
        logger.info(f"🔧 Optimized context: {len(optimized_chunks)} chunks, ~{current_tokens} tokens")
        return optimized_chunks
    
    @abstractmethod
    async def _generate_with_chunked_context(self, features: List[str], 
                                           context_chunks: List[ContextChunk],
                                           correlation_id: str) -> HandlerResult:
        """Generate code using chunked context - implemented by subclasses"""
        pass
    
    @abstractmethod
    def _build_expert_prompt(self, features: List[str], context_chunks: List[ContextChunk]) -> str:
        """Build technology-specific expert prompt - implemented by subclasses"""
        pass
    
    @abstractmethod
    async def _validate_code_quality(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        """Validate generated code quality - implemented by subclasses"""
        pass
    
    def _build_architecture_context(self, context: Dict[str, Any]) -> str:
        """Build architecture context string"""
        return f"""
=== ARCHITECTURE CONTEXT ===
Project: {context.get('project_name', 'Unknown')}
Tech Stack: {json.dumps(context.get('technology_stack', {}), indent=2)}
Design Patterns: {context.get('established_patterns', [])}
Security Standards: {context.get('security_standards', [])}
Naming Conventions: {json.dumps(context.get('naming_conventions', {}), indent=2)}
=== END ARCHITECTURE ===
"""
    
    def _build_contracts_context(self, features: List[str]) -> str:
        """Build contracts context string"""
        context_parts = ["=== EXISTING CONTRACTS ==="]
        
        for feature in features:
            contract = self.contracts.get_feature_contract(feature)
            if contract:
                context_parts.append(f"\nFeature: {feature}")
                context_parts.append(f"Endpoints: {len(contract.endpoints)}")
                for ep in contract.endpoints:
                    context_parts.append(f"  {ep.method} {ep.path}")
                context_parts.append(f"Models: {[m.name for m in contract.models]}")
        
        context_parts.append("=== END CONTRACTS ===")
        return "\n".join(context_parts)
    
    def _build_history_context(self) -> str:
        """Build generation history context"""
        if not self.generation_history:
            return "=== NO PREVIOUS GENERATION HISTORY ==="
        
        context_parts = ["=== GENERATION HISTORY ==="]
        
        # Include last 3 generations to avoid token overflow
        recent_history = self.generation_history[-3:]
        
        for i, gen in enumerate(recent_history):
            context_parts.append(f"\nGeneration {i+1}:")
            context_parts.append(f"Features: {gen.get('features', [])}")
            context_parts.append(f"Quality: {gen.get('quality_score', 0)}/10")
            context_parts.append(f"Patterns Used: {gen.get('patterns_used', [])}")
        
        context_parts.append("=== END HISTORY ===")
        return "\n".join(context_parts)
    
    def _build_feature_context(self, features: List[str], context: Dict[str, Any]) -> str:
        """Build feature-specific context"""
        return f"""
=== FEATURES TO IMPLEMENT ===
Features: {features}
Requirements: {context.get('requirements', {})}
Dependencies: {context.get('feature_dependencies', {})}
=== END FEATURES ===
"""
    
    async def _refine_until_quality_met(self, initial_result: HandlerResult, 
                                      quality_target: float, 
                                      correlation_id: str) -> HandlerResult:
        """Iteratively refine code until quality target is met"""
        
        current_result = initial_result
        cycle = 0
        
        while (current_result.quality_score < quality_target and 
               cycle < self.max_refinement_cycles):
            
            cycle += 1
            logger.info(f"🔄 {self.handler_type} refinement cycle {cycle}: {current_result.quality_score}/10")
            
            # Generate improvement prompt
            improvement_prompt = await self._build_improvement_prompt(current_result, quality_target)
            
            # Apply improvements
            improved_result = await self._apply_improvements(current_result, improvement_prompt)
            
            # Update result
            current_result = improved_result
            current_result.refinement_cycles = cycle
            
            # Publish refinement event
            await self.events.publish("refinement_cycle_completed", {
                "handler": self.handler_type,
                "cycle": cycle,
                "quality_score": current_result.quality_score,
                "target": quality_target
            }, self.handler_type, correlation_id)
        
        if current_result.quality_score < quality_target:
            logger.warning(f"⚠️ {self.handler_type} quality target not met after {cycle} cycles")
        
        return current_result
    
    async def _finalize_generation(self, result: HandlerResult, correlation_id: str):
        """Finalize generation with contract registration and events"""
        
        # Store generation in history for future context
        self.generation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "features": result.features_implemented,
            "quality_score": result.quality_score,
            "patterns_used": self._extract_patterns_used(result),
            "contracts": result.contracts
        })
        
        # Publish completion event
        await self.events.publish(f"{self.handler_type}_generation_completed", {
            "handler": self.handler_type,
            "features": result.features_implemented,
            "quality_score": result.quality_score,
            "contracts": result.contracts,
            "files_generated": len(result.code_files)
        }, self.handler_type, correlation_id)
    
    def _extract_patterns_used(self, result: HandlerResult) -> List[str]:
        """Extract architectural patterns used in generation"""
        # To be implemented by subclasses based on code analysis
        return []
    
    # Event handlers
    async def _on_generation_started(self, event):
        """Handle generation started event"""
        logger.info(f"📡 {self.handler_type} received generation_started event")
    
    async def _on_contracts_established(self, event):
        """Handle contracts established event"""
        logger.info(f"📡 {self.handler_type} received contracts_established event")
    
    async def _on_quality_validation(self, event):
        """Handle quality validation request"""
        logger.info(f"📡 {self.handler_type} received quality_validation_required event")
    
    @abstractmethod
    async def _build_improvement_prompt(self, current_result: HandlerResult, 
                                      quality_target: float) -> str:
        """Build improvement prompt for refinement"""
        pass
    
    @abstractmethod
    async def _apply_improvements(self, current_result: HandlerResult, 
                                improvement_prompt: str) -> HandlerResult:
        """Apply improvements to code"""
        pass