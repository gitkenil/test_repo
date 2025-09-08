"""
REACT FRONTEND HANDLER - FIXED JSON VERSION
=====================
Expert-level React code generation with context preservation
"""

import json
import re
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.handlers.base_handler import TechnologyHandler, HandlerResult, ContextChunk
import logging

logger = logging.getLogger(__name__)

class ReactHandler(TechnologyHandler):
    """Expert React frontend code generator"""
    
    def __init__(self, contract_registry, event_bus, claude_client=None):
        super().__init__(contract_registry, event_bus, claude_client)
        self.handler_type = "react_frontend"
        
        # React-specific configuration
        self.react_patterns = {
            "authentication": {
                "components": ["LoginForm", "AuthProvider", "ProtectedRoute"],
                "hooks": ["useAuth", "useAuthContext"],
                "services": ["authService", "tokenManager"]
            },
            "user_management": {
                "components": ["UserList", "UserForm", "UserProfile"],
                "hooks": ["useUsers", "useUserForm"],
                "services": ["userService"]
            },
            "real_time_chat": {
                "components": ["ChatRoom", "MessageList", "MessageInput"],
                "hooks": ["useSocket", "useMessages"],
                "services": ["socketService", "messageService"]
            }
        }
        
        # Quality validation patterns
        self.quality_patterns = {
            "error_handling": r"try\s*{|catch\s*\(|\.catch\(|error\s*&&",
            "loading_states": r"loading|isLoading|pending",
            "typescript_types": r"interface\s+\w+|type\s+\w+\s*=",
            "proper_hooks": r"useEffect|useState|useCallback|useMemo",
            "accessibility": r"aria-|role=|alt=",
            "security": r"sanitize|escape|validate"
        }
    
    async def _generate_with_chunked_context(self, features: List[str], 
                                           context_chunks: List[ContextChunk],
                                           correlation_id: str) -> HandlerResult:
        """Generate React code using chunked context"""
        
        if not self.claude_client:
            raise Exception("Claude client not initialized")
        
        # Build expert React prompt
        prompt = self._build_expert_prompt(features, context_chunks)
        
        try:
            # Make Claude API call with retry logic
            response = await self._claude_request_with_retry(prompt, max_tokens=8000)
            response_text = response.content[0].text
            
            # Parse response into structured code
            parsed_code = self._parse_react_response(response_text)
            
            # Validate code quality
            quality_report = await self._validate_code_quality(parsed_code)
            
            # Extract contracts from generated code
            contracts = self._extract_react_contracts(parsed_code, features)
            
            return HandlerResult(
                success=True,
                handler_type=self.handler_type,
                features_implemented=features,
                code_files=parsed_code,
                contracts=contracts,
                quality_score=quality_report["overall_score"],
                tokens_used=response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0
            )
            
        except Exception as e:
            logger.error(f"❌ React generation failed: {e}")
            raise e
    
    def _build_expert_prompt(self, features: List[str], context_chunks: List[ContextChunk]) -> str:
        """Build expert-level React prompt with context"""
        
        # Combine context chunks
        context_content = "\n\n".join([
            f"=== {chunk.chunk_type.upper()} ===\n{chunk.content}"
            for chunk in context_chunks
        ])
        
        # Get existing contracts
        existing_contracts = ""
        for feature in features:
            contract = self.contracts.get_feature_contract(feature)
            if contract:
                endpoints = "\n".join([f"  {ep.method} {ep.path}" for ep in contract.endpoints])
                existing_contracts += f"\n{feature} API:\n{endpoints}\n"
        
        features_text = "\n".join([f"- {feature.replace('_', ' ').title()}" for feature in features])
        
        prompt = f"""You are an EXPERT React developer with 10+ years of enterprise experience. Generate PRODUCTION-READY React components with PERFECT code quality.

{context_content}

EXISTING API CONTRACTS TO INTEGRATE:
{existing_contracts}

FEATURES TO IMPLEMENT:
{features_text}

REACT REQUIREMENTS:
1. **TypeScript**: Use proper interfaces and types
2. **Modern Hooks**: useState, useEffect, useCallback, useMemo appropriately
3. **Error Handling**: Try/catch blocks, error boundaries, loading states
4. **Accessibility**: ARIA labels, semantic HTML, keyboard navigation
5. **Performance**: React.memo, useMemo for expensive calculations
6. **Security**: Input validation, XSS prevention, sanitization
7. **State Management**: Redux Toolkit with RTK Query for API calls
8. **Styling**: Styled-components or CSS modules
9. **Testing**: Component structure ready for Jest/RTL

ARCHITECTURE PATTERNS:
- Feature-based folder structure
- Custom hooks for business logic
- Service layer for API calls
- Context providers for global state
- Higher-order components for reusability

CRITICAL JSON RESPONSE REQUIREMENTS:
- Your response MUST be ONLY valid JSON. No explanations, no markdown, no code blocks.
- Start with {{ and end with }}. Nothing else.
- Do NOT use ```json or ``` anywhere in your response.
- Each file path maps to complete working code as a string.
- Use \\n for line breaks in code strings.

RESPONSE FORMAT - ONLY THIS JSON STRUCTURE:
{{"src/components/LoginForm.tsx": "import React, {{ useState }} from 'react';\\n\\nconst LoginForm = () => {{\\n  const [email, setEmail] = useState('');\\n  const [password, setPassword] = useState('');\\n  // COMPLETE WORKING CODE HERE\\n}};\\n\\nexport default LoginForm;", "src/components/SignupForm.tsx": "import React, {{ useState }} from 'react';\\n\\nconst SignupForm = () => {{\\n  const [formData, setFormData] = useState({{}});\\n  // COMPLETE WORKING CODE HERE\\n}};\\n\\nexport default SignupForm;"}}

EXAMPLE CORRECT RESPONSE:
{{"file1.tsx": "const code = 'here';", "file2.ts": "export const api = 'code';"}}

EXAMPLE WRONG RESPONSE (DO NOT DO THIS):
```json
{{"file": "code"}}
```

CRITICAL REQUIREMENTS:
- COMPLETE, WORKING components (no placeholders)
- Proper TypeScript interfaces
- Comprehensive error handling
- Loading and error states
- Responsive design patterns
- Accessibility compliance
- Security best practices
- Integration with existing API contracts

Generate ONLY the JSON object. No other text. Implement ALL features with complete functionality."""

        return prompt
    
    def _parse_react_response(self, response: str) -> Dict[str, str]:
        """Parse Claude's React response into structured code files"""
        
        try:
            # Try direct JSON parsing first
            response_clean = response.strip()
            
            # Find JSON boundaries
            start_idx = response_clean.find('{')
            end_idx = response_clean.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_content = response_clean[start_idx:end_idx]
                parsed = json.loads(json_content)
                
                # Validate structure
                if isinstance(parsed, dict) and all(
                    isinstance(k, str) and isinstance(v, str) 
                    for k, v in parsed.items()
                ):
                    return parsed
            
            # Fallback: Extract code blocks
            return self._extract_code_blocks_fallback(response)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}, using fallback extraction")
            return self._extract_code_blocks_fallback(response)
    
    def _extract_code_blocks_fallback(self, response: str) -> Dict[str, str]:
        """Fallback method to extract React code blocks"""
        
        code_files = {}
        
        # Pattern to match file paths and code blocks
        file_pattern = r'(?:```(?:typescript|tsx|ts|javascript|jsx)?\s*)?(?://\s*)?([^\n]*\.(?:tsx?|jsx?|ts))\s*\n(.*?)(?=\n\s*(?://|```|\w+/)|$)'
        
        matches = re.findall(file_pattern, response, re.DOTALL)
        
        for file_path, code_content in matches:
            file_path = file_path.strip().strip('"\'')
            code_content = code_content.strip()
            
            # Clean up code content
            if code_content.startswith('```'):
                code_content = '\n'.join(code_content.split('\n')[1:])
            if code_content.endswith('```'):
                code_content = '\n'.join(code_content.split('\n')[:-1])
            
            if file_path and code_content and len(code_content) > 50:
                code_files[file_path] = code_content
        
        # If still no files found, create basic structure
        if not code_files:
            logger.warning("No code files extracted, creating basic structure")
            code_files = {
                "src/components/App.tsx": self._generate_basic_app_component(),
                "src/index.tsx": self._generate_basic_index_file()
            }
        
        return code_files
    
    async def _validate_code_quality(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        """Validate React code quality with detailed scoring"""
        
        total_score = 0
        file_scores = {}
        issues = []
        
        for file_path, content in code_files.items():
            file_score = self._validate_single_file_quality(file_path, content)
            file_scores[file_path] = file_score
            total_score += file_score["score"]
            issues.extend(file_score["issues"])
        
        overall_score = total_score / len(code_files) if code_files else 0
        
        return {
            "overall_score": overall_score,
            "file_scores": file_scores,
            "issues": issues,
            "metrics": {
                "total_files": len(code_files),
                "average_score": overall_score,
                "files_above_8": sum(1 for score in file_scores.values() if score["score"] >= 8.0),
                "critical_issues": len([i for i in issues if i.startswith("CRITICAL")])
            }
        }
    
    def _validate_single_file_quality(self, file_path: str, content: str) -> Dict[str, Any]:
        """Validate quality of a single React file"""
        
        score = 10.0
        issues = []
        
        # Check for TypeScript usage
        if file_path.endswith('.tsx') or file_path.endswith('.ts'):
            if not re.search(self.quality_patterns["typescript_types"], content):
                score -= 1.0
                issues.append(f"Missing TypeScript types in {file_path}")
        
        # Check for proper hooks usage
        if 'component' in file_path.lower() or 'hook' in file_path.lower():
            if not re.search(self.quality_patterns["proper_hooks"], content):
                score -= 1.0
                issues.append(f"Missing proper hooks usage in {file_path}")
        
        # Check for error handling
        if not re.search(self.quality_patterns["error_handling"], content):
            score -= 1.5
            issues.append(f"CRITICAL: No error handling in {file_path}")
        
        # Check for loading states
        if 'component' in file_path.lower():
            if not re.search(self.quality_patterns["loading_states"], content):
                score -= 1.0
                issues.append(f"Missing loading states in {file_path}")
        
        # Check for accessibility
        if 'component' in file_path.lower():
            if not re.search(self.quality_patterns["accessibility"], content):
                score -= 0.5
                issues.append(f"Missing accessibility features in {file_path}")
        
        # Check for security patterns
        if 'form' in file_path.lower() or 'input' in file_path.lower():
            if not re.search(self.quality_patterns["security"], content):
                score -= 1.0
                issues.append(f"Missing security validation in {file_path}")
        
        # Check for basic structure
        if len(content.strip()) < 100:
            score -= 3.0
            issues.append(f"CRITICAL: File too short/incomplete {file_path}")
        
        # Check for syntax issues (basic)
        if content.count('{') != content.count('}'):
            score -= 2.0
            issues.append(f"CRITICAL: Bracket mismatch in {file_path}")
        
        return {
            "score": max(0, score),
            "issues": issues,
            "file_path": file_path
        }
    
    def _extract_react_contracts(self, code_files: Dict[str, str], features: List[str]) -> Dict[str, Any]:
        """Extract API contracts from React code"""
        
        contracts = {
            "api_calls": [],
            "components_created": [],
            "hooks_created": [],
            "services_created": []
        }
        
        for file_path, content in code_files.items():
            # Extract API calls
            api_pattern = r'(?:fetch|axios|api)\s*\.\s*(?:get|post|put|delete)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
            api_matches = re.findall(api_pattern, content, re.IGNORECASE)
            
            for endpoint in api_matches:
                contracts["api_calls"].append({
                    "endpoint": endpoint,
                    "file": file_path,
                    "method": "unknown"  # Could be enhanced to detect method
                })
            
            # Extract component exports
            if file_path.endswith('.tsx'):
                component_pattern = r'export\s+(?:default\s+)?(?:const|function)\s+(\w+)'
                component_matches = re.findall(component_pattern, content)
                
                for component in component_matches:
                    contracts["components_created"].append({
                        "name": component,
                        "file": file_path,
                        "features": features
                    })
            
            # Extract custom hooks
            if 'hook' in file_path.lower() or re.search(r'export\s+(?:const|function)\s+use\w+', content):
                hook_pattern = r'export\s+(?:const|function)\s+(use\w+)'
                hook_matches = re.findall(hook_pattern, content)
                
                for hook in hook_matches:
                    contracts["hooks_created"].append({
                        "name": hook,
                        "file": file_path,
                        "features": features
                    })
        
        return contracts
    
    async def _build_improvement_prompt(self, current_result: HandlerResult, 
                                      quality_target: float) -> str:
        """Build improvement prompt for React code refinement"""
        
        issues_text = "\n".join([
            f"- {issue}" for issue in current_result.contracts.get("quality_issues", [])
        ])
        
        return f"""IMPROVE this React code to achieve {quality_target}/10 quality.

CURRENT QUALITY: {current_result.quality_score}/10
TARGET QUALITY: {quality_target}/10

IDENTIFIED ISSUES:
{issues_text}

CURRENT CODE FILES:
{json.dumps(current_result.code_files, indent=2)}

IMPROVEMENT REQUIREMENTS:
1. Fix all critical issues (error handling, security, accessibility)
2. Enhance TypeScript types and interfaces
3. Improve component structure and reusability
4. Add comprehensive error boundaries
5. Implement proper loading states
6. Ensure accessibility compliance
7. Add input validation and sanitization
8. Optimize performance with React.memo, useMemo
9. Follow React best practices and patterns
10. Ensure all components are production-ready

CRITICAL: Return ONLY valid JSON. No explanations, no markdown, no code blocks.

Return ONLY the improved code in this JSON format:
{{
  "file_path": "improved_complete_code"
}}

Make every improvement necessary to reach the quality target."""
    
    async def _apply_improvements(self, current_result: HandlerResult, 
                                improvement_prompt: str) -> HandlerResult:
        """Apply improvements to React code"""
        
        try:
            response = await self._claude_request_with_retry(improvement_prompt, max_tokens=8000)
            response_text = response.content[0].text
            
            # Parse improved code
            improved_code = self._parse_react_response(response_text)
            
            # Merge with existing code (keep files that weren't improved)
            final_code = current_result.code_files.copy()
            final_code.update(improved_code)
            
            # Re-validate quality
            quality_report = await self._validate_code_quality(final_code)
            
            # Update result
            improved_result = HandlerResult(
                success=True,
                handler_type=self.handler_type,
                features_implemented=current_result.features_implemented,
                code_files=final_code,
                contracts=self._extract_react_contracts(final_code, current_result.features_implemented),
                quality_score=quality_report["overall_score"],
                tokens_used=current_result.tokens_used + (
                    response.usage.input_tokens + response.usage.output_tokens 
                    if hasattr(response, 'usage') else 0
                ),
                refinement_cycles=current_result.refinement_cycles
            )
            
            return improved_result
            
        except Exception as e:
            logger.error(f"❌ React improvement failed: {e}")
            return current_result  # Return original if improvement fails
    
    async def _claude_request_with_retry(self, prompt: str, max_tokens: int = 4000, max_retries: int = 3):
        """Make Claude API request with retry logic"""
        
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(2 * attempt)  # Progressive delay
                
                message = self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                return message
                
            except Exception as e:
                if "overloaded" in str(e) or "rate_limit" in str(e):
                    wait_time = 5 * (2 ** attempt)
                    logger.warning(f"⚠️ API overloaded, waiting {wait_time}s (attempt {attempt+1})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ Claude API error: {e}")
                    if attempt == max_retries - 1:
                        raise e
        
        raise Exception("Max retries exceeded for Claude API")
    
    def _generate_basic_app_component(self) -> str:
        """Generate basic App component as fallback"""
        return '''import React from 'react';
import './App.css';

const App: React.FC = () => {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Generated React Application</h1>
        <p>Your application components will be implemented here.</p>
      </header>
    </div>
  );
};

export default App;'''
    
    def _generate_basic_index_file(self) -> str:
        """Generate basic index file as fallback"""
        return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);'''