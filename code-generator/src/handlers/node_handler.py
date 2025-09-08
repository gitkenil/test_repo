"""
NODE.JS BACKEND HANDLER - DYNAMIC SQL/ENV GENERATION
==================================================
Expert-level Node.js backend code generation with intelligent file generation
"""

import json
import re
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.handlers.base_handler import TechnologyHandler, HandlerResult, ContextChunk
from src.core.contract_registry import APIEndpoint, DataModel, FeatureContract
import logging

logger = logging.getLogger(__name__)

class NodeHandler(TechnologyHandler):
    """Expert Node.js backend code generator"""
    
    def __init__(self, contract_registry, event_bus, claude_client=None):
        super().__init__(contract_registry, event_bus, claude_client)
        self.handler_type = "node_backend"
        
        # Node.js-specific patterns
        self.node_patterns = {
            "authentication": {
                "routes": ["POST /api/auth/login", "POST /api/auth/register", "POST /api/auth/refresh"],
                "middleware": ["authMiddleware", "validateToken", "rateLimiter"],
                "services": ["AuthService", "TokenService", "PasswordService"]
            },
            "user_management": {
                "routes": ["GET /api/users", "POST /api/users", "PUT /api/users/:id", "DELETE /api/users/:id"],
                "middleware": ["validateUser", "checkPermissions"],
                "services": ["UserService", "ValidationService"]
            },
            "real_time_chat": {
                "routes": ["GET /api/chat/rooms", "POST /api/chat/rooms", "GET /api/chat/messages"],
                "middleware": ["socketAuth", "roomValidator"],
                "services": ["ChatService", "SocketService", "MessageService"]
            }
        }
        
        # Quality validation patterns
        self.quality_patterns = {
            "error_handling": r"try\s*{|catch\s*\(|\.catch\(|next\(|throw\s+new",
            "validation": r"joi\.|validator\.|validate\(|schema\.",
            "security": r"helmet|cors|sanitize|escape|bcrypt|jwt",
            "logging": r"logger\.|console\.|winston|log\(",
            "async_await": r"async\s+function|await\s+",
            "middleware": r"\.use\(|middleware|next\(\)",
            "database": r"\.findOne|\.create|\.update|\.delete|\.save|query\(",
            "status_codes": r"\.status\(|res\.json|res\.send"
        }
    
    async def _generate_with_chunked_context(self, features: List[str], 
                                           context_chunks: List[ContextChunk],
                                           correlation_id: str) -> HandlerResult:
        """Generate Node.js code using chunked context"""
        
        if not self.claude_client:
            raise Exception("Claude client not initialized")
        
        # Build expert Node.js prompt
        prompt = self._build_expert_prompt(features, context_chunks)
        
        try:
            # Make Claude API call
            response = await self._claude_request_with_retry(prompt, max_tokens=8000)
            response_text = response.content[0].text
            
            # Parse response into structured code
            parsed_code = self._parse_node_response(response_text)
            
            # Validate code quality
            quality_report = await self._validate_code_quality(parsed_code)
            
            # Extract and register contracts
            contracts = self._extract_node_contracts(parsed_code, features)
            
            # Register API endpoints in contract registry
            await self._register_api_contracts(features, contracts)
            
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
            logger.error(f"❌ Node.js generation failed: {e}")
            raise e
    
    def _build_expert_prompt(self, features: List[str], context_chunks: List[ContextChunk]) -> str:
        """Build expert-level Node.js prompt with context"""
        
        # Combine context chunks
        context_content = "\n\n".join([
            f"=== {chunk.chunk_type.upper()} ===\n{chunk.content}"
            for chunk in context_chunks
        ])
        
        features_text = "\n".join([f"- {feature.replace('_', ' ').title()}" for feature in features])
        
        # Get expected API patterns for features
        expected_apis = []
        for feature in features:
            if feature in self.node_patterns:
                expected_apis.extend(self.node_patterns[feature]["routes"])
        
        expected_apis_text = "\n".join([f"- {api}" for api in expected_apis])
        
        prompt = f"""You are an EXPERT Node.js backend developer with 10+ years of enterprise experience. Generate PRODUCTION-READY backend code with PERFECT architecture and 9/10 quality.

{context_content}

FEATURES TO IMPLEMENT:
{features_text}

EXPECTED API ENDPOINTS:
{expected_apis_text}

NODE.JS REQUIREMENTS:
1. **Express.js Framework**: Latest version with proper structure
2. **Authentication**: JWT tokens with refresh, bcrypt passwords
3. **Validation**: Joi schemas for all inputs
4. **Security**: Helmet, CORS, rate limiting, input sanitization
5. **Error Handling**: Global error middleware, try/catch blocks
6. **Logging**: Winston logger with correlation IDs
7. **Database**: Sequelize ORM with proper models
8. **Middleware**: Authentication, validation, error handling
9. **Testing**: Jest-ready structure with proper mocking
10. **Documentation**: JSDoc comments, API documentation

ARCHITECTURE PATTERNS:
- Controller → Service → Repository pattern
- Dependency injection
- Middleware chain for cross-cutting concerns
- Centralized error handling
- Configuration management
- Health checks and monitoring

INTELLIGENT FILE GENERATION REQUIREMENTS:
🔥 CRITICAL: You must analyze the code you generate and automatically create ALL supporting files:

1. **Database Files**: For every Sequelize model you create, automatically generate the corresponding SQL migration file
   - If you create User model → automatically create database/migrations/001_create_users.sql
   - If you create Chat model → automatically create database/migrations/002_create_chats.sql
   - Include proper table structure, indexes, constraints, and relationships

2. **Package Dependencies**: Analyze every require() statement in your code and include ALL packages in package.json
   - If your code uses bcrypt → add "bcryptjs" to dependencies
   - If your code uses jwt → add "jsonwebtoken" to dependencies
   - If your code uses sequelize → add "sequelize" and "pg" to dependencies

3. **Environment Variables**: For every process.env variable in your code, add it to .env.example
   - If your code uses process.env.JWT_SECRET → add JWT_SECRET to .env.example
   - If your code uses process.env.DB_HOST → add DB_HOST to .env.example
   - Include proper default values and comments

4. **Configuration Files**: Generate any additional files your code references
   - Database configuration files
   - Logger configuration
   - Any other config files your code imports

CRITICAL JSON RESPONSE REQUIREMENTS:
- Your response MUST be ONLY valid JSON. No explanations, no markdown, no code blocks.
- Start with {{ and end with }}. Nothing else.
- Do NOT use ```json or ``` anywhere in your response.
- Each file path maps to complete working code as a string.
- Use \\n for line breaks in code strings.
- AUTOMATICALLY generate ALL files needed for a complete working application

RESPONSE FORMAT - ONLY THIS JSON STRUCTURE:
{{"src/controllers/authController.js": "complete_working_controller_code", "src/models/User.js": "complete_sequelize_model", "database/migrations/001_create_users.sql": "CREATE_TABLE_statement_matching_your_User_model", "package.json": "complete_package_json_with_ALL_dependencies_your_code_uses", ".env.example": "ALL_environment_variables_your_code_references", "src/config/database.js": "database_config_if_your_code_needs_it"}}

EXAMPLE CORRECT RESPONSE:
{{"file1.js": "const bcrypt = require('bcryptjs'); module.exports = {{ hash: bcrypt.hash }};", "package.json": "{{ \\"dependencies\\": {{ \\"bcryptjs\\": \\"^2.4.3\\" }} }}", ".env.example": "# Bcrypt configuration\\nBCRYPT_ROUNDS=12"}}

EXAMPLE WRONG RESPONSE (DO NOT DO THIS):
```json
{{"file": "code"}}
```

CRITICAL REQUIREMENTS:
- COMPLETE, WORKING code (no placeholders or TODOs)
- Automatically generate SQL migrations for EVERY model you create
- Automatically generate package.json with EVERY dependency you use in your code
- Automatically generate .env.example with EVERY environment variable you reference
- Comprehensive error handling with proper HTTP status codes
- Security best practices (OWASP compliance)
- Input validation for all endpoints
- Proper async/await usage
- Database transactions where needed
- Rate limiting and authentication
- Comprehensive logging
- RESTful API design
- Performance optimizations

Generate ONLY the JSON object. No other text. Implement ALL features with complete functionality and ALL supporting files based on what you actually create."""

        return prompt
    
    def _parse_node_response(self, response: str) -> Dict[str, str]:
        """Parse Claude's Node.js response into structured code files"""
        
        try:
            # Try direct JSON parsing
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
        """Fallback method to extract Node.js code blocks"""
        
        code_files = {}
        
        # Pattern to match file paths and code blocks
        file_pattern = r'(?:```(?:javascript|js|json|sql)?\s*)?(?://\s*)?([^\n]*\.(?:js|json|ts|sql))\s*\n(.*?)(?=\n\s*(?://|```|\w+/)|$)'
        
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
        
        # If no files found, create basic structure
        if not code_files:
            logger.warning("No code files extracted, creating basic structure")
            code_files = {
                "src/app.js": self._generate_basic_app_file(),
                "src/server.js": self._generate_basic_server_file(),
                "package.json": self._generate_basic_package_json()
            }
        
        return code_files
    
    async def _validate_code_quality(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        """Validate Node.js code quality with detailed scoring"""
        
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
        """Validate quality of a single Node.js file"""
        
        score = 10.0
        issues = []
        
        # Skip validation for SQL and config files
        if file_path.endswith('.sql') or file_path.endswith('.env.example'):
            return {"score": 10.0, "issues": [], "file_path": file_path}
        
        # Check for error handling
        if not re.search(self.quality_patterns["error_handling"], content):
            score -= 2.0
            issues.append(f"CRITICAL: No error handling in {file_path}")
        
        # Check for validation (controllers/routes)
        if 'controller' in file_path.lower() or 'route' in file_path.lower():
            if not re.search(self.quality_patterns["validation"], content):
                score -= 1.5
                issues.append(f"CRITICAL: No input validation in {file_path}")
        
        # Check for security patterns
        if 'auth' in file_path.lower() or 'security' in file_path.lower():
            if not re.search(self.quality_patterns["security"], content):
                score -= 1.5
                issues.append(f"CRITICAL: Missing security patterns in {file_path}")
        
        # Check for proper async/await
        if not re.search(self.quality_patterns["async_await"], content) and 'config' not in file_path.lower():
            score -= 1.0
            issues.append(f"Missing async/await patterns in {file_path}")
        
        # Check for logging
        if not re.search(self.quality_patterns["logging"], content):
            score -= 0.5
            issues.append(f"Missing logging in {file_path}")
        
        # Check for proper HTTP status codes
        if 'controller' in file_path.lower():
            if not re.search(self.quality_patterns["status_codes"], content):
                score -= 1.0
                issues.append(f"Missing proper HTTP responses in {file_path}")
        
        # Check for middleware usage
        if 'app.js' in file_path or 'server.js' in file_path:
            if not re.search(self.quality_patterns["middleware"], content):
                score -= 1.0
                issues.append(f"Missing middleware setup in {file_path}")
        
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
    
    def _extract_node_contracts(self, code_files: Dict[str, str], features: List[str]) -> Dict[str, Any]:
        """Extract API contracts from Node.js code"""
        
        contracts = {
            "api_endpoints": [],
            "models_created": [],
            "services_created": [],
            "middleware_created": []
        }
        
        for file_path, content in code_files.items():
            # Extract API endpoints from routes/controllers
            if 'route' in file_path.lower() or 'controller' in file_path.lower():
                # Pattern for Express routes
                route_pattern = r'(?:router|app)\s*\.\s*(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
                route_matches = re.findall(route_pattern, content, re.IGNORECASE)
                
                for method, path in route_matches:
                    contracts["api_endpoints"].append({
                        "method": method.upper(),
                        "path": path,
                        "file": file_path,
                        "features": features,
                        "authentication_required": "auth" in content.lower(),
                        "validation": "validate" in content.lower() or "joi" in content.lower()
                    })
            
            # Extract models
            if 'model' in file_path.lower():
                # Pattern for Sequelize models
                model_pattern = r'(?:sequelize\.define|DataTypes)\s*\(\s*[\'"`](\w+)[\'"`]'
                model_matches = re.findall(model_pattern, content, re.IGNORECASE)
                
                for model_name in model_matches:
                    contracts["models_created"].append({
                        "name": model_name,
                        "file": file_path,
                        "features": features
                    })
            
            # Extract services
            if 'service' in file_path.lower():
                service_pattern = r'class\s+(\w+Service)|(?:const|let|var)\s+(\w+Service)'
                service_matches = re.findall(service_pattern, content)
                
                for class_name, const_name in service_matches:
                    service_name = class_name or const_name
                    if service_name:
                        contracts["services_created"].append({
                            "name": service_name,
                            "file": file_path,
                            "features": features
                        })
        
        return contracts
    
    async def _register_api_contracts(self, features: List[str], contracts: Dict[str, Any]):
        """Register API contracts in the contract registry"""
        
        for feature in features:
            # Filter endpoints for this feature
            feature_endpoints = [
                APIEndpoint(
                    method=ep["method"],
                    path=ep["path"],
                    input_schema={},  # To be enhanced
                    output_schema={}, # To be enhanced
                    authentication_required=ep.get("authentication_required", True),
                    description=f"{feature} endpoint"
                )
                for ep in contracts["api_endpoints"]
                if feature in ep.get("features", [])
            ]
            
            # Create data models
            feature_models = [
                DataModel(
                    name=model["name"],
                    schema={},  # To be enhanced with actual schema
                    table_name=model["name"].lower() + "s"
                )
                for model in contracts["models_created"]
                if feature in model.get("features", [])
            ]
            
            # Create feature contract
            if feature_endpoints or feature_models:
                feature_contract = FeatureContract(
                    feature_name=feature,
                    endpoints=feature_endpoints,
                    models=feature_models,
                    created_by=self.handler_type
                )
                
                self.contracts.register_feature_contract(feature_contract)
                logger.info(f"✅ Registered contracts for {feature}: {len(feature_endpoints)} endpoints, {len(feature_models)} models")
    
    async def _build_improvement_prompt(self, current_result: HandlerResult, 
                                      quality_target: float) -> str:
        """Build improvement prompt for Node.js code refinement"""
        
        issues_text = "\n".join([
            f"- {issue}" for issue in current_result.contracts.get("quality_issues", [])
        ])
        
        return f"""IMPROVE this Node.js backend code to achieve {quality_target}/10 quality.

CURRENT QUALITY: {current_result.quality_score}/10
TARGET QUALITY: {quality_target}/10

IDENTIFIED ISSUES:
{issues_text}

CURRENT CODE FILES:
{json.dumps(current_result.code_files, indent=2)}

IMPROVEMENT REQUIREMENTS:
1. Add comprehensive error handling with try/catch blocks
2. Implement input validation with Joi schemas
3. Add security middleware (helmet, cors, rate limiting)
4. Improve async/await usage and error handling
5. Add comprehensive logging with Winston
6. Implement proper HTTP status codes
7. Add authentication and authorization middleware
8. Optimize database queries and add transactions
9. Add API documentation and comments
10. Follow Node.js best practices and patterns

INTELLIGENT FILE GENERATION FOR IMPROVEMENTS:
- If you improve models, update corresponding SQL migration files
- If you add new dependencies, update package.json
- If you add new environment variables, update .env.example

CRITICAL: Return ONLY valid JSON. No explanations, no markdown, no code blocks.

Return ONLY the improved code in this JSON format including ALL supporting files:
{{
  "file_path": "improved_complete_code",
  "database/migrations/updated_migration.sql": "updated_sql_if_models_changed",
  "package.json": "updated_package_json_if_dependencies_added"
}}

Make every improvement necessary to reach enterprise-grade quality."""
    
    async def _apply_improvements(self, current_result: HandlerResult, 
                                improvement_prompt: str) -> HandlerResult:
        """Apply improvements to Node.js code"""
        
        try:
            response = await self._claude_request_with_retry(improvement_prompt, max_tokens=8000)
            response_text = response.content[0].text
            
            # Parse improved code
            improved_code = self._parse_node_response(response_text)
            
            # Merge with existing code
            final_code = current_result.code_files.copy()
            final_code.update(improved_code)
            
            # Re-validate quality
            quality_report = await self._validate_code_quality(final_code)
            
            # Update contracts
            contracts = self._extract_node_contracts(final_code, current_result.features_implemented)
            
            # Update result
            improved_result = HandlerResult(
                success=True,
                handler_type=self.handler_type,
                features_implemented=current_result.features_implemented,
                code_files=final_code,
                contracts=contracts,
                quality_score=quality_report["overall_score"],
                tokens_used=current_result.tokens_used + (
                    response.usage.input_tokens + response.usage.output_tokens 
                    if hasattr(response, 'usage') else 0
                ),
                refinement_cycles=current_result.refinement_cycles
            )
            
            return improved_result
            
        except Exception as e:
            logger.error(f"❌ Node.js improvement failed: {e}")
            return current_result
    
    async def _claude_request_with_retry(self, prompt: str, max_tokens: int = 4000, max_retries: int = 3):
        """Make Claude API request with retry logic"""
        
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(2 * attempt)
                
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
    
    def _generate_basic_app_file(self) -> str:
        """Generate basic Express app as fallback"""
        return '''const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

const app = express();

// Security middleware
app.use(helmet());
app.use(cors());

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

module.exports = app;'''
    
    def _generate_basic_server_file(self) -> str:
        """Generate basic server file as fallback"""
        return '''const app = require('./app');
const PORT = process.env.PORT || 3000;

const server = app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
  });
});'''
    
    def _generate_basic_package_json(self) -> str:
        """Generate basic package.json as fallback"""
        return '''{
  "name": "generated-backend",
  "version": "1.0.0",
  "description": "Generated Node.js backend application",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "nodemon src/server.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "joi": "^17.9.2",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "winston": "^3.10.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2"
  }
}'''