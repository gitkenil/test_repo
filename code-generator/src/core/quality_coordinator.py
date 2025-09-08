"""
CORE COMPONENT: Quality Coordinator
==================================
Cross-stack quality validation and coordination between handlers
"""


logger = logging.getLogger(__name__)

@dataclass
class QualityReport:
    """Comprehensive quality assessment report"""
    overall_score: float
    handler_scores: Dict[str, float]
    cross_stack_score: float
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]
    validation_timestamp: str
    refinement_cycles: int = 0

@dataclass
class CrossStackIssue:
    """Cross-stack consistency issue"""
    issue_type: str  # "contract_mismatch", "security_gap", "performance_issue"
    severity: str    # "critical", "warning", "recommendation"
    description: str
    affected_handlers: List[str]
    suggested_fix: str
    
class QualityCoordinator:
    """Coordinates quality validation across all handlers"""
    
    def __init__(self, contract_registry, event_bus):
        self.contracts = contract_registry
        self.events = event_bus
        self.quality_threshold = 8.0
        self.max_refinement_cycles = 5
        
        # Quality validation rules
        self.validation_rules = {
            "contract_consistency": {
                "weight": 0.3,  # 30% of total score
                "validators": [
                    self._validate_api_consistency,
                    self._validate_data_model_consistency,
                    self._validate_authentication_consistency
                ]
            },
            "security_compliance": {
                "weight": 0.25,  # 25% of total score
                "validators": [
                    self._validate_input_sanitization,
                    self._validate_authentication_security,
                    self._validate_authorization_patterns,
                    self._validate_data_encryption
                ]
            },
            "performance_standards": {
                "weight": 0.2,   # 20% of total score
                "validators": [
                    self._validate_database_efficiency,
                    self._validate_api_response_patterns,
                    self._validate_caching_strategies
                ]
            },
            "code_quality": {
                "weight": 0.15,  # 15% of total score
                "validators": [
                    self._validate_error_handling,
                    self._validate_logging_patterns,
                    self._validate_code_structure
                ]
            },
            "maintainability": {
                "weight": 0.1,   # 10% of total score
                "validators": [
                    self._validate_documentation,
                    self._validate_naming_conventions,
                    self._validate_testing_readiness
                ]
            }
        }
    
    async def validate_and_refine(self, handler_results: Dict[str, Any], 
                                target_quality: float = 8.0) -> QualityReport:
        """Main quality validation and refinement orchestrator"""
        
        logger.info(f"🔍 Starting cross-stack quality validation (target: {target_quality}/10)")
        
        # Initial quality assessment
        initial_report = await self._assess_cross_stack_quality(handler_results)
        
        if initial_report.overall_score >= target_quality:
            logger.info(f"✅ Quality target achieved: {initial_report.overall_score}/10")
            return initial_report
        
        # Refinement cycles
        current_results = handler_results.copy()
        current_report = initial_report
        
        for cycle in range(1, self.max_refinement_cycles + 1):
            logger.info(f"🔄 Quality refinement cycle {cycle}: {current_report.overall_score}/10")
            
            # Identify priority issues to fix
            priority_issues = self._prioritize_issues(current_report)
            
            # Apply coordinated improvements
            improved_results = await self._apply_coordinated_improvements(
                current_results, priority_issues, cycle
            )
            
            # Re-assess quality
            current_report = await self._assess_cross_stack_quality(improved_results)
            current_report.refinement_cycles = cycle
            current_results = improved_results
            
            # Publish refinement progress
            await self.events.publish("quality_refinement_cycle", {
                "cycle": cycle,
                "quality_score": current_report.overall_score,
                "target": target_quality,
                "issues_resolved": len(priority_issues),
                "remaining_critical": len(current_report.critical_issues)
            }, "quality_coordinator")
            
            # Check if target achieved
            if current_report.overall_score >= target_quality:
                logger.info(f"✅ Quality target achieved after {cycle} cycles: {current_report.overall_score}/10")
                break
        
        # Final quality report
        if current_report.overall_score < target_quality:
            logger.warning(f"⚠️ Quality target not fully achieved: {current_report.overall_score}/10 (target: {target_quality}/10)")
            current_report.recommendations.append(
                f"Consider human review - automated refinement reached {current_report.overall_score}/10"
            )
        
        return current_report
    
    async def _assess_cross_stack_quality(self, handler_results: Dict[str, Any]) -> QualityReport:
        """Comprehensive cross-stack quality assessment"""
        
        validation_start = datetime.utcnow()
        
        # Initialize report
        report = QualityReport(
            overall_score=0.0,
            handler_scores={},
            cross_stack_score=0.0,
            critical_issues=[],
            warnings=[],
            recommendations=[],
            metrics={},
            validation_timestamp=validation_start.isoformat()
        )
        
        # Collect individual handler scores
        total_handler_score = 0.0
        for handler_name, result in handler_results.items():
            if hasattr(result, 'quality_score'):
                report.handler_scores[handler_name] = result.quality_score
                total_handler_score += result.quality_score
        
        average_handler_score = total_handler_score / len(handler_results) if handler_results else 0
        
        # Run cross-stack validations
        cross_stack_issues = []
        total_cross_stack_score = 0.0
        
        for rule_name, rule_config in self.validation_rules.items():
            rule_score = 0.0
            rule_issues = []
            
            # Run all validators for this rule
            for validator in rule_config["validators"]:
                try:
                    validator_result = await validator(handler_results)
                    rule_score += validator_result["score"]
                    rule_issues.extend(validator_result["issues"])
                except Exception as e:
                    logger.error(f"❌ Validator {validator.__name__} failed: {e}")
                    rule_issues.append(CrossStackIssue(
                        issue_type="validation_error",
                        severity="warning",
                        description=f"Validator {validator.__name__} failed: {str(e)}",
                        affected_handlers=list(handler_results.keys()),
                        suggested_fix="Review validator implementation"
                    ))
            
            # Average score for this rule
            avg_rule_score = rule_score / len(rule_config["validators"])
            weighted_score = avg_rule_score * rule_config["weight"]
            total_cross_stack_score += weighted_score
            
            # Categorize issues by severity
            for issue in rule_issues:
                if issue.severity == "critical":
                    report.critical_issues.append(f"{rule_name}: {issue.description}")
                elif issue.severity == "warning":
                    report.warnings.append(f"{rule_name}: {issue.description}")
                else:
                    report.recommendations.append(f"{rule_name}: {issue.description}")
            
            cross_stack_issues.extend(rule_issues)
        
        # Calculate final scores
        report.cross_stack_score = total_cross_stack_score * 10  # Convert to 0-10 scale
        report.overall_score = (average_handler_score * 0.6 + report.cross_stack_score * 0.4)
        
        # Compile metrics
        report.metrics = {
            "validation_duration": (datetime.utcnow() - validation_start).total_seconds(),
            "handlers_validated": len(handler_results),
            "cross_stack_rules_checked": len(self.validation_rules),
            "total_issues_found": len(cross_stack_issues),
            "critical_issues_count": len(report.critical_issues),
            "warnings_count": len(report.warnings),
            "recommendations_count": len(report.recommendations),
            "handler_average_score": average_handler_score,
            "cross_stack_weighted_score": report.cross_stack_score
        }
        
        logger.info(f"📊 Quality assessment completed: {report.overall_score}/10 ({len(report.critical_issues)} critical issues)")
        
        return report
    
    # Contract Consistency Validators
    async def _validate_api_consistency(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API consistency between frontend and backend"""
        score = 10.0
        issues = []
        
        backend_result = handler_results.get("backend")
        frontend_result = handler_results.get("frontend")
        
        if not backend_result or not frontend_result:
            return {"score": score, "issues": issues}
        
        # Get backend API endpoints
        backend_apis = backend_result.contracts.get("api_endpoints", [])
        frontend_apis = frontend_result.contracts.get("api_calls", [])
        
        # Check if frontend calls match backend endpoints
        backend_endpoints = set(f"{api['method']} {api['path']}" for api in backend_apis)
        frontend_calls = set(api.get("endpoint", "") for api in frontend_apis)
        
        # Find mismatches
        missing_backend = frontend_calls - backend_endpoints
        unused_backend = backend_endpoints - frontend_calls
        
        if missing_backend:
            score -= 3.0
            issues.append(CrossStackIssue(
                issue_type="contract_mismatch",
                severity="critical",
                description=f"Frontend calls missing backend endpoints: {list(missing_backend)}",
                affected_handlers=["frontend", "backend"],
                suggested_fix="Add missing backend endpoints or remove unused frontend calls"
            ))
        
        if unused_backend:
            score -= 1.0
            issues.append(CrossStackIssue(
                issue_type="contract_mismatch",
                severity="warning",
                description=f"Backend endpoints not used by frontend: {list(unused_backend)}",
                affected_handlers=["frontend", "backend"],
                suggested_fix="Remove unused endpoints or add frontend integration"
            ))
        
        return {"score": max(0, score), "issues": issues}
    
    async def _validate_data_model_consistency(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data models consistency between backend and database"""
        score = 10.0
        issues = []
        
        backend_result = handler_results.get("backend")
        database_result = handler_results.get("database")
        
        if not backend_result or not database_result:
            return {"score": score, "issues": issues}
        
        # Get models from both handlers
        backend_models = set(model.get("name", "") for model in backend_result.contracts.get("models_created", []))
        database_models = set(model.get("name", "") for model in database_result.contracts.get("tables_created", []))
        
        # Check consistency
        missing_database = backend_models - database_models
        missing_backend = database_models - backend_models
        
        if missing_database:
            score -= 2.0
            issues.append(CrossStackIssue(
                issue_type="contract_mismatch",
                severity="critical",
                description=f"Backend models missing database tables: {list(missing_database)}",
                affected_handlers=["backend", "database"],
                suggested_fix="Create missing database tables or remove unused backend models"
            ))
        
        if missing_backend:
            score -= 1.0
            issues.append(CrossStackIssue(
                issue_type="contract_mismatch",
                severity="warning",
                description=f"Database tables not used by backend: {list(missing_backend)}",
                affected_handlers=["backend", "database"],
                suggested_fix="Add backend models or remove unused database tables"
            ))
        
        return {"score": max(0, score), "issues": issues}
    
    async def _validate_authentication_consistency(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate authentication patterns across all handlers"""
        score = 10.0
        issues = []
        
        # Check if all handlers implement consistent authentication
        auth_patterns = {}
        
        for handler_name, result in handler_results.items():
            if hasattr(result, 'code_files'):
                auth_found = False
                jwt_found = False
                
                for file_path, content in result.code_files.items():
                    if any(auth_term in content.lower() for auth_term in ['jwt', 'token', 'auth', 'login']):
                        auth_found = True
                    if 'jwt' in content.lower() or 'jsonwebtoken' in content.lower():
                        jwt_found = True
                
                auth_patterns[handler_name] = {
                    "has_auth": auth_found,
                    "uses_jwt": jwt_found
                }
        
        # Validate consistency
        auth_handlers = [h for h, p in auth_patterns.items() if p["has_auth"]]
        jwt_handlers = [h for h, p in auth_patterns.items() if p["uses_jwt"]]
        
        if len(auth_handlers) > 0 and len(auth_handlers) < len(handler_results):
            score -= 2.0
            missing_auth = [h for h in handler_results.keys() if h not in auth_handlers]
            issues.append(CrossStackIssue(
                issue_type="security_gap",
                severity="critical",
                description=f"Inconsistent authentication implementation. Missing in: {missing_auth}",
                affected_handlers=missing_auth,
                suggested_fix="Implement consistent authentication across all handlers"
            ))
        
        return {"score": max(0, score), "issues": issues}
    
    # Security Validators
    async def _validate_input_sanitization(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input sanitization across handlers"""
        score = 10.0
        issues = []
        
        security_patterns = [
            r'sanitize|escape|validate|joi\.|validator\.',
            r'xss|sql.*injection|csrf',
            r'helmet|cors|rate.*limit'
        ]
        
        for handler_name, result in handler_results.items():
            if hasattr(result, 'code_files'):
                has_sanitization = False
                
                for file_path, content in result.code_files.items():
                    if any(re.search(pattern, content, re.IGNORECASE) for pattern in security_patterns):
                        has_sanitization = True
                        break
                
                if not has_sanitization and handler_name in ['backend', 'frontend']:
                    score -= 3.0
                    issues.append(CrossStackIssue(
                        issue_type="security_gap",
                        severity="critical",
                        description=f"No input sanitization patterns found in {handler_name}",
                        affected_handlers=[handler_name],
                        suggested_fix="Add input validation and sanitization"
                    ))
        
        return {"score": max(0, score), "issues": issues}
    
    async def _validate_authentication_security(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate authentication security implementation"""
        score = 10.0
        issues = []
        
        backend_result = handler_results.get("backend")
        if backend_result and hasattr(backend_result, 'code_files'):
            has_bcrypt = False
            has_jwt = False
            has_rate_limit = False
            
            for content in backend_result.code_files.values():
                if 'bcrypt' in content.lower():
                    has_bcrypt = True
                if 'jwt' in content.lower() or 'jsonwebtoken' in content.lower():
                    has_jwt = True
                if 'rate' in content.lower() and 'limit' in content.lower():
                    has_rate_limit = True
            
            if not has_bcrypt:
                score -= 2.0
                issues.append(CrossStackIssue(
                    issue_type="security_gap",
                    severity="critical",
                    description="No password hashing (bcrypt) found in backend",
                    affected_handlers=["backend"],
                    suggested_fix="Implement bcrypt for password hashing"
                ))
            
            if not has_jwt:
                score -= 2.0
                issues.append(CrossStackIssue(
                    issue_type="security_gap",
                    severity="critical",
                    description="No JWT implementation found in backend",
                    affected_handlers=["backend"],
                    suggested_fix="Implement JWT for authentication"
                ))
            
            if not has_rate_limit:
                score -= 1.0
                issues.append(CrossStackIssue(
                    issue_type="security_gap",
                    severity="warning",
                    description="No rate limiting found in backend",
                    affected_handlers=["backend"],
                    suggested_fix="Add rate limiting middleware"
                ))
        
        return {"score": max(0, score), "issues": issues}
    
    # Placeholder validators (implement as needed)
    async def _validate_authorization_patterns(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    async def _validate_data_encryption(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    async def _validate_database_efficiency(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    async def _validate_api_response_patterns(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    async def _validate_caching_strategies(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    async def _validate_error_handling(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    async def _validate_logging_patterns(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    async def _validate_code_structure(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    async def _validate_documentation(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    async def _validate_naming_conventions(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    async def _validate_testing_readiness(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 8.0, "issues": []}
    
    def _prioritize_issues(self, quality_report: QualityReport) -> List[CrossStackIssue]:
        """Prioritize issues for refinement"""
        # For now, return critical issues first
        # This can be enhanced with more sophisticated prioritization
        return quality_report.critical_issues[:3]  # Top 3 critical issues
    
    async def _apply_coordinated_improvements(self, handler_results: Dict[str, Any], 
                                           priority_issues: List[str], 
                                           cycle: int) -> Dict[str, Any]:
        """Apply coordinated improvements across handlers"""
        
        # For now, return original results
        # This would be enhanced to actually apply improvements
        logger.info(f"🔧 Applying {len(priority_issues)} coordinated improvements (cycle {cycle})")
        
        # Placeholder for improvement logic
        return handler_results
    
    async def validate_contracts_only(self, handler_results: Dict[str, Any]) -> Dict[str, Any]:
        """Quick contract validation without full quality assessment"""
        
        contract_issues = await self._validate_api_consistency(handler_results)
        model_issues = await self._validate_data_model_consistency(handler_results)
        auth_issues = await self._validate_authentication_consistency(handler_results)
        
        return {
            "contract_score": (contract_issues["score"] + model_issues["score"] + auth_issues["score"]) / 3,
            "issues": contract_issues["issues"] + model_issues["issues"] + auth_issues["issues"],
            "validation_type": "contracts_only"
        }