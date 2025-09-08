"""
FIXED DOCUMENTATION MANAGER - COMPLETE VERSION
===============================================
Complete documentation_manager.py with all missing methods and proper error handling
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DocumentationManager:
    """COMPLETE Documentation Manager with all methods implemented"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.docs_path = self.project_path / "docs"
        
        # Create directories with proper error handling
        try:
            self.docs_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create docs directory: {e}")
            # Fallback to temp directory
            import tempfile
            self.docs_path = Path(tempfile.mkdtemp()) / "docs"
            self.docs_path.mkdir(parents=True, exist_ok=True)
        
        # Documentation templates
        self.templates = {
            "architecture_patterns": {
                "react_node": "React frontend with Node.js backend, following clean architecture",
                "angular_dotnet": "Angular frontend with .NET Core backend, following domain-driven design",
                "vue_python": "Vue.js frontend with Python Django backend, following MVC pattern"
            },
            "quality_standards": {
                "syntax": "100% - Code must compile and run without errors",
                "security": "90% - No critical vulnerabilities, comprehensive input validation", 
                "architecture": "85% - Follows established patterns, proper separation of concerns",
                "performance": "80% - Efficient queries, proper error handling, caching strategies",
                "maintainability": "85% - Clean code, consistent naming, inline documentation"
            }
        }
    
    def generate_initial_readme(self, tech_stack: Dict[str, Any], 
                              features: List[str], context: Dict[str, Any]) -> str:
        """Generate comprehensive initial architecture documentation"""
        
        try:
            tech_recommendations = tech_stack.get("technology_recommendations", {})
            frontend_tech = tech_recommendations.get("frontend", {}).get("framework", "Unknown")
            backend_tech = tech_recommendations.get("backend", {}).get("framework", "Unknown")
            database_tech = tech_recommendations.get("database", {}).get("primary", "Unknown")
            
            # Determine architecture pattern
            architecture_key = f"{frontend_tech.lower()}_{backend_tech.lower().replace('.', '').replace(' ', '')}"
            architecture_pattern = self.templates["architecture_patterns"].get(
                architecture_key, 
                f"{frontend_tech} frontend with {backend_tech} backend, following enterprise patterns"
            )
            
            # Format features with priority classification
            features_formatted = self._format_features_with_priorities(features)
            
            # Build comprehensive README
            readme_content = f"""# {context.get('project_name', 'Generated Enterprise Application')}

## 🎯 System Overview
**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Quality Target**: 80-90% production-ready code  
**Architecture Pattern**: {architecture_pattern}  
**Total Features**: {len(features)} enterprise-grade features  

## 🏗️ Technology Stack

### Frontend: {frontend_tech}
**Libraries & Tools:**
{self._format_tech_list(tech_recommendations.get("frontend", {}).get("libraries", []))}

### Backend: {backend_tech}
**Language**: {tech_recommendations.get("backend", {}).get("language", "Not specified")}  
**Libraries & Tools:**
{self._format_tech_list(tech_recommendations.get("backend", {}).get("libraries", []))}

### Database: {database_tech}
**Secondary Storage:**
{self._format_tech_list(tech_recommendations.get("database", {}).get("secondary", []))}

## 🎯 Design Principles & Quality Standards

### 1. Security First
- **Authentication**: JWT with refresh token rotation (15min access, 7-day refresh)
- **Authorization**: Role-based access control (RBAC) with permission granularity
- **Input Validation**: Comprehensive validation and sanitization on all inputs
- **Data Protection**: Encryption at rest and in transit, GDPR compliance ready
- **Security Headers**: Helmet.js, CORS, CSP, rate limiting (100 req/min per user)

### 2. Performance Excellence
- **API Response Time**: Sub-200ms for 95% of requests
- **Database Queries**: Optimized with proper indexing, connection pooling
- **Frontend Rendering**: Virtual scrolling, lazy loading, code splitting
- **Caching Strategy**: Multi-layer caching (Redis, CDN, browser cache)
- **Resource Optimization**: Minification, compression, image optimization

### 3. Maintainability & Scalability
- **Code Structure**: Clean architecture with clear separation of concerns
- **Error Handling**: Comprehensive error boundaries and graceful degradation
- **Logging**: Structured logging with correlation IDs and distributed tracing
- **Testing**: Unit, integration, and E2E test-ready architecture
- **Documentation**: Inline comments, API docs, architecture decision records

## 📋 Features Implementation Plan

{features_formatted}

## 🔧 Quality Assurance Gates

{self._format_quality_standards()}

## 🔌 API Design Standards

### RESTful Conventions
- **Resource Naming**: Plural nouns, lowercase with hyphens
- **HTTP Methods**: GET (retrieve), POST (create), PUT (update), DELETE (remove)
- **Status Codes**: Proper HTTP status codes with meaningful error messages
- **Versioning**: URL versioning (/api/v1/) with backward compatibility

### Request/Response Format
```json
// Standard Success Response
{{
  "success": true,
  "data": {{}},
  "metadata": {{
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0",
    "correlation_id": "uuid"
  }}
}}

// Standard Error Response
{{
  "success": false,
  "error": {{
    "code": "VALIDATION_ERROR",
    "message": "User-friendly error message",
    "details": ["Specific validation failures"]
  }},
  "metadata": {{
    "timestamp": "2024-01-15T10:30:00Z",
    "correlation_id": "uuid"
  }}
}}
```

## 🗄️ Database Design Principles

### Schema Design
- **Normalization**: Third normal form with strategic denormalization for performance
- **Constraints**: Foreign key relationships with proper CASCADE/RESTRICT policies
- **Indexing**: Composite indexes on frequently queried column combinations
- **Data Types**: Appropriate data types with proper constraints and defaults

## 🚀 Getting Started

### Prerequisites
```bash
# Node.js & npm (Backend)
node --version  # v18+ required
npm --version   # v9+ required

# Database
{self._get_database_setup_commands(database_tech)}
```

### Development Setup
```bash
# 1. Clone and setup backend
cd backend
npm install
npm run migrate
npm run seed
npm run dev  # Starts on port 3000

# 2. Setup frontend  
cd ../frontend
npm install
npm start    # Starts on port 3001

# 3. Setup database
{self._get_database_setup_commands(database_tech)}
```

## 🔄 Integration Contracts
*[This section will be populated as handlers generate code and establish contracts]*

---

**Generated by Ultra-Premium Code Generation Pipeline**  
**Quality Standard**: Enterprise-grade (8.0+/10)  
**Last Updated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
            
            return readme_content
            
        except Exception as e:
            logger.error(f"Error generating initial README: {e}")
            return self._generate_fallback_readme(context.get('project_name', 'Generated Project'))
    
    def update_readme_after_handler_completion(self, existing_readme: str, 
                                             handler_type: str, 
                                             handler_result: Any) -> str:
        """Update README after a handler completes generation"""
        
        try:
            # Create handler-specific section
            handler_section = self._build_handler_completion_section(handler_type, handler_result)
            
            # Find insertion point for contracts section
            contracts_marker = "## 🔄 Integration Contracts"
            if contracts_marker in existing_readme:
                parts = existing_readme.split(contracts_marker)
                updated_readme = parts[0] + contracts_marker + "\n" + handler_section + "\n" + parts[1]
            else:
                updated_readme = existing_readme + "\n" + handler_section
            
            return updated_readme
            
        except Exception as e:
            logger.error(f"Error updating README after handler completion: {e}")
            return existing_readme  # Return original if update fails
    
    def update_readme_with_completion(self, handler_results: Dict[str, Any], 
                                    quality_report: Any, 
                                    written_files: List[str]) -> str:
        """Update README with final completion details"""
        
        try:
            completion_section = f"""
## ✅ Implementation Completed
**Completion Timestamp**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Final Quality Score**: {getattr(quality_report, 'overall_score', 0)}/10  
**Refinement Cycles**: {getattr(quality_report, 'refinement_cycles', 0)}  
**Files Generated**: {len(written_files)}  
**Handlers Completed**: {len(handler_results)}  

### 🎯 Quality Achievements
{self._format_quality_achievements(quality_report)}

### 📁 Generated Project Structure
```
{self._build_file_tree(written_files)}
```

### 🔌 API Endpoints Summary
{self._build_api_summary(handler_results)}

### 🗄️ Database Schema Summary  
{self._build_database_summary(handler_results)}

## 🚀 Next Steps
1. **Review Generated Code**: Examine all generated files for business logic accuracy
2. **Run Quality Checks**: Execute linting, testing, and security scans
3. **Environment Setup**: Configure development, staging, and production environments
4. **Deploy**: Follow deployment guide for your target environment
5. **Monitor**: Set up monitoring and alerting for production deployment

---
*Generated with Ultra-Premium Code Generation Pipeline*
"""
            
            return completion_section
            
        except Exception as e:
            logger.error(f"Error updating README with completion: {e}")
            return "## ✅ Implementation Completed\n*Documentation update failed*"
    
    def update_readme_after_failure(self, existing_readme: str, 
                                   failure_info: Dict[str, Any]) -> str:
        """Update README with failure details and recovery instructions"""
        
        try:
            failure_section = f"""
## ⚠️ Generation Status: Partial Completion
**Failure Timestamp**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Failed Component**: {failure_info.get('handler_type', 'Unknown')}  
**Error Type**: {failure_info.get('error_type', 'Unknown')}  

### What Was Successfully Generated
{self._format_completed_components(failure_info.get('completed_handlers', []))}

### What Requires Manual Completion
{self._format_failed_components(failure_info.get('failed_handlers', []))}

### Recovery Instructions
{self._build_recovery_instructions(failure_info)}

---
"""
            
            # Insert failure section before contracts
            contracts_marker = "## 🔄 Integration Contracts"
            if contracts_marker in existing_readme:
                parts = existing_readme.split(contracts_marker)
                updated_readme = parts[0] + failure_section + contracts_marker + parts[1]
            else:
                updated_readme = existing_readme + failure_section
            
            return updated_readme
            
        except Exception as e:
            logger.error(f"Error updating README after failure: {e}")
            return existing_readme
    
    def save_stage_documentation(self, stage: str, content: str, metadata: Dict[str, Any]):
        """Save documentation for a specific generation stage"""
        
        try:
            # Save current README
            readme_path = self.project_path / "README.md"
            readme_path.write_text(content, encoding='utf-8')
            
            # Save stage-specific backup
            timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
            stage_backup = self.docs_path / f"README-{stage}-{timestamp}.md"
            stage_backup.write_text(content, encoding='utf-8')
            
            # Save metadata
            metadata_path = self.docs_path / f"generation-metadata-{stage}.json"
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
            
            logger.info(f"📚 Documentation saved for stage: {stage}")
            
        except Exception as e:
            logger.error(f"Error saving stage documentation: {e}")
    
    # ALL HELPER METHODS PROPERLY IMPLEMENTED
    
    def _format_features_with_priorities(self, features: List[str]) -> str:
        """Format features with priority classification"""
        try:
            # Classify features by priority
            core_features = [f for f in features if f in ['authentication', 'user_management', 'dashboard']]
            business_features = [f for f in features if f not in core_features and f not in ['analytics', 'reporting']]
            advanced_features = [f for f in features if f in ['analytics', 'reporting', 'ai_integration']]
            
            formatted = ""
            
            if core_features:
                formatted += "\n### 🔐 Core Features (High Priority)\n"
                for feature in core_features:
                    formatted += f"- **{feature.replace('_', ' ').title()}**: Essential system functionality\n"
            
            if business_features:
                formatted += "\n### 💼 Business Features (Medium Priority)\n"
                for feature in business_features:
                    formatted += f"- **{feature.replace('_', ' ').title()}**: Core business logic implementation\n"
            
            if advanced_features:
                formatted += "\n### 🚀 Advanced Features (Low Priority)\n"
                for feature in advanced_features:
                    formatted += f"- **{feature.replace('_', ' ').title()}**: Enhanced functionality and analytics\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting features: {e}")
            return "\n### Features\n" + "\n".join([f"- {f.replace('_', ' ').title()}" for f in features])
    
    def _format_tech_list(self, tech_list: List[str]) -> str:
        """Format technology list with bullet points"""
        try:
            if not tech_list:
                return "- *Standard libraries and tools*"
            return "\n".join([f"- {tech}" for tech in tech_list])
        except Exception as e:
            logger.error(f"Error formatting tech list: {e}")
            return "- *Technology list unavailable*"
    
    def _format_quality_standards(self) -> str:
        """Format quality standards section"""
        try:
            formatted = ""
            for standard, description in self.templates["quality_standards"].items():
                formatted += f"- **{standard.title()}**: {description}\n"
            return formatted
        except Exception as e:
            logger.error(f"Error formatting quality standards: {e}")
            return "- Quality standards unavailable"
    
    def _get_database_setup_commands(self, database_tech: str) -> str:
        """Get database-specific setup commands"""
        try:
            commands = {
                "postgresql": "# PostgreSQL\npsql -U postgres -c 'CREATE DATABASE myapp_dev;'",
                "mysql": "# MySQL\nmysql -u root -e 'CREATE DATABASE myapp_dev;'",
                "mongodb": "# MongoDB\nmongod --dbpath ./data/db",
                "sqlite": "# SQLite (no setup required)"
            }
            
            return commands.get(database_tech.lower(), f"# {database_tech} setup commands")
        except Exception as e:
            logger.error(f"Error getting database commands: {e}")
            return "# Database setup commands"
    
    def _build_handler_completion_section(self, handler_type: str, handler_result: Any) -> str:
        """Build documentation section for completed handler"""
        try:
            section = f"""
### {handler_type.replace('_', ' ').title()} Implementation ✅
**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Quality Score**: {getattr(handler_result, 'quality_score', 0)}/10  
**Files Generated**: {len(getattr(handler_result, 'code_files', {}))}  

**Key Components:**
"""
            
            # Add handler-specific details
            if hasattr(handler_result, 'contracts'):
                contracts = handler_result.contracts
                
                if 'api_endpoints' in contracts:
                    section += f"- **API Endpoints**: {len(contracts['api_endpoints'])} RESTful endpoints\n"
                
                if 'components_created' in contracts:
                    section += f"- **Components**: {len(contracts['components_created'])} UI components\n"
                
                if 'models_created' in contracts:
                    section += f"- **Data Models**: {len(contracts['models_created'])} database models\n"
            
            return section
            
        except Exception as e:
            logger.error(f"Error building handler completion section: {e}")
            return f"### {handler_type} Implementation\n*Documentation generation failed*"
    
    def _format_quality_achievements(self, quality_report: Any) -> str:
        """Format quality achievements section"""
        try:
            if not quality_report:
                return "- Quality assessment not available"
            
            achievements = []
            
            overall_score = getattr(quality_report, 'overall_score', 0)
            if overall_score >= 9.0:
                achievements.append("🏆 **Exceptional Quality**: 9.0+/10 - Production-ready excellence")
            elif overall_score >= 8.0:
                achievements.append("✅ **High Quality**: 8.0+/10 - Enterprise-grade standards met")
            elif overall_score >= 7.0:
                achievements.append("⚠️ **Good Quality**: 7.0+/10 - Minor improvements recommended")
            else:
                achievements.append("❌ **Quality Issues**: <7.0/10 - Significant improvements needed")
            
            critical_issues = len(getattr(quality_report, 'critical_issues', []))
            if critical_issues == 0:
                achievements.append("🔒 **Security**: No critical security issues identified")
            else:
                achievements.append(f"⚠️ **Security**: {critical_issues} critical issues require attention")
            
            refinement_cycles = getattr(quality_report, 'refinement_cycles', 0)
            if refinement_cycles > 0:
                achievements.append(f"🔄 **Refinement**: {refinement_cycles} improvement cycles applied")
            
            return "\n".join([f"- {achievement}" for achievement in achievements])
            
        except Exception as e:
            logger.error(f"Error formatting quality achievements: {e}")
            return "- Quality achievements unavailable"
    
    def _build_file_tree(self, written_files: List[str]) -> str:
        """Build file tree representation"""
        try:
            if not written_files:
                return "No files generated"
            
            # Simple file tree
            tree_lines = []
            for file_path in sorted(written_files)[:20]:  # Limit to 20 files
                # Extract relative path
                if '/' in file_path:
                    relative_path = '/'.join(file_path.split('/')[-3:])  # Last 3 parts
                    tree_lines.append('├── ' + relative_path)
                else:
                    tree_lines.append('├── ' + file_path)
            
            if len(written_files) > 20:
                tree_lines.append(f'└── ... and {len(written_files) - 20} more files')
            
            return '\n'.join(tree_lines)
            
        except Exception as e:
            logger.error(f"Error building file tree: {e}")
            return f"Files generated: {len(written_files)}"
    
    def _build_api_summary(self, handler_results: Dict[str, Any]) -> str:
        """Build API endpoints summary"""
        try:
            all_endpoints = []
            
            for handler_name, result in handler_results.items():
                if hasattr(result, 'contracts') and 'api_endpoints' in result.contracts:
                    all_endpoints.extend(result.contracts['api_endpoints'])
            
            if not all_endpoints:
                return "No API endpoints generated"
            
            summary = []
            for endpoint in all_endpoints[:10]:  # Limit to first 10
                method = endpoint.get('method', 'GET')
                path = endpoint.get('path', '/unknown')
                summary.append(f"- **{method}** `{path}`")
            
            if len(all_endpoints) > 10:
                summary.append(f"- ... and {len(all_endpoints) - 10} more endpoints")
            
            return '\n'.join(summary)
            
        except Exception as e:
            logger.error(f"Error building API summary: {e}")
            return "API summary unavailable"
    
    def _build_database_summary(self, handler_results: Dict[str, Any]) -> str:
        """Build database schema summary"""
        try:
            all_models = []
            
            for handler_name, result in handler_results.items():
                if hasattr(result, 'contracts'):
                    contracts = result.contracts
                    if 'models_created' in contracts:
                        all_models.extend(contracts['models_created'])
                    elif 'tables_created' in contracts:
                        all_models.extend(contracts['tables_created'])
            
            if not all_models:
                return "No database models generated"
            
            summary = []
            for model in all_models[:5]:  # Limit to first 5
                name = model.get('name', 'Unknown')
                summary.append(f"- **{name}**: Database model with relationships")
            
            if len(all_models) > 5:
                summary.append(f"- ... and {len(all_models) - 5} more models")
            
            return '\n'.join(summary)
            
        except Exception as e:
            logger.error(f"Error building database summary: {e}")
            return "Database summary unavailable"
    
    def _format_completed_components(self, completed_handlers: List[str]) -> str:
        """Format completed components section"""
        try:
            if not completed_handlers:
                return "- No components completed successfully"
            
            return '\n'.join([f"- ✅ **{handler.replace('_', ' ').title()}**: Successfully generated" 
                             for handler in completed_handlers])
        except Exception as e:
            logger.error(f"Error formatting completed components: {e}")
            return "- Completed components list unavailable"
    
    def _format_failed_components(self, failed_handlers: List[str]) -> str:
        """Format failed components section"""
        try:
            if not failed_handlers:
                return "- All components completed successfully"
            
            return '\n'.join([f"- ❌ **{handler.replace('_', ' ').title()}**: Requires manual implementation" 
                             for handler in failed_handlers])
        except Exception as e:
            logger.error(f"Error formatting failed components: {e}")
            return "- Failed components list unavailable"
    
    def _build_recovery_instructions(self, failure_info: Dict[str, Any]) -> str:
        """Build recovery instructions for failed generation"""
        try:
            failed_handler = failure_info.get('handler_type', 'unknown')
            error_message = failure_info.get('error_message', 'Unknown error')
            
            instructions = f"""
1. **Review Error Details**: {error_message[:100]}...
2. **Check Generated Code**: Review partial code in the output directory
3. **Use Established Contracts**: Follow the API contracts that were successfully created
4. **Manual Implementation**: Complete the {failed_handler} component manually
5. **Quality Validation**: Run quality checks after manual completion
6. **Integration Testing**: Test integration between completed and manual components
"""
            
            return instructions
            
        except Exception as e:
            logger.error(f"Error building recovery instructions: {e}")
            return "Recovery instructions unavailable"
    
    def _generate_fallback_readme(self, project_name: str) -> str:
        """Generate minimal fallback README if main generation fails"""
        return f"""# {project_name}

## Generated Application
This application was generated using the Ultra-Premium Code Generation Pipeline.

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Getting Started
1. Review the generated code files
2. Install dependencies
3. Configure environment variables
4. Run the application

*Detailed documentation generation encountered an error. Please check logs for details.*
"""