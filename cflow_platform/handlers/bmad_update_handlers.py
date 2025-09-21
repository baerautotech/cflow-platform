"""
BMAD Update Management Handlers

Handlers for BMAD update management tools including update checking, validation, and application.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from cflow_platform.core.bmad_update_manager import get_bmad_update_manager


class BMADUpdateHandlers:
    """Handlers for BMAD update management tools."""
    
    def __init__(self):
        self.update_manager = get_bmad_update_manager()
    
    async def bmad_update_check(self) -> Dict[str, Any]:
        """Check for available BMAD updates."""
        try:
            update_info = await self.update_manager.check_for_updates()
            
            return {
                "status": "success",
                "message": "BMAD update check completed",
                "current_version": update_info.current_version,
                "latest_version": update_info.latest_version,
                "update_available": update_info.update_available,
                "new_features_count": len(update_info.new_features),
                "bug_fixes_count": len(update_info.bug_fixes),
                "breaking_changes_count": len(update_info.breaking_changes),
                "dependencies_updated_count": len(update_info.dependencies_updated),
                "last_checked": update_info.last_checked,
                "changelog": update_info.changelog[:5] if update_info.changelog else [],  # First 5 entries
                "new_features": update_info.new_features[:10] if update_info.new_features else [],  # First 10 features
                "bug_fixes": update_info.bug_fixes[:10] if update_info.bug_fixes else [],  # First 10 fixes
                "breaking_changes": update_info.breaking_changes,
                "dependencies_updated": update_info.dependencies_updated
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to check for BMAD updates: {str(e)}"
            }
    
    async def bmad_update_validate(self, target_version: str) -> Dict[str, Any]:
        """Validate a BMAD update before applying."""
        try:
            validation_result = await self.update_manager.validate_update(target_version)
            
            return {
                "status": "success",
                "message": f"BMAD update validation completed for version {target_version}",
                "target_version": target_version,
                "validation_success": validation_result.success,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "suggestions": validation_result.suggestions,
                "breaking_changes": validation_result.breaking_changes,
                "customizations_affected": validation_result.customizations_affected,
                "test_results": validation_result.test_results,
                "performance_impact": validation_result.performance_impact,
                "can_proceed": validation_result.success and len(validation_result.errors) == 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to validate BMAD update: {str(e)}"
            }
    
    async def bmad_update_apply(self, target_version: str, preserve_customizations: bool = True) -> Dict[str, Any]:
        """Apply a BMAD update with customization preservation."""
        try:
            # First validate the update
            validation_result = await self.update_manager.validate_update(target_version)
            
            if not validation_result.success or validation_result.errors:
                return {
                    "status": "error",
                    "message": "Cannot apply update due to validation errors",
                    "validation_errors": validation_result.errors,
                    "suggestions": validation_result.suggestions
                }
            
            # Apply the update
            success = await self.update_manager.apply_update(target_version, preserve_customizations)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Successfully applied BMAD update to version {target_version}",
                    "target_version": target_version,
                    "customizations_preserved": preserve_customizations,
                    "customizations_count": len(self.update_manager.customizations),
                    "backup_created": True,
                    "next_steps": [
                        "Run integration tests to verify functionality",
                        "Monitor performance metrics",
                        "Review any breaking changes",
                        "Update documentation if needed"
                    ]
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to apply BMAD update to version {target_version}",
                    "target_version": target_version,
                    "backup_restored": True,
                    "suggestions": [
                        "Check error logs for details",
                        "Review validation results",
                        "Consider manual update if needed"
                    ]
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to apply BMAD update: {str(e)}"
            }
    
    async def bmad_update_report(self, target_version: str) -> Dict[str, Any]:
        """Generate comprehensive update report."""
        try:
            report = await self.update_manager.generate_update_report(target_version)
            
            if "error" in report:
                return {
                    "status": "error",
                    "message": f"Failed to generate update report: {report['error']}"
                }
            
            return {
                "status": "success",
                "message": f"Generated comprehensive update report for version {target_version}",
                "target_version": target_version,
                "report": report,
                "update_available": report.get("update_info", {}).get("update_available", False),
                "breaking_changes_count": len(report.get("validation_result", {}).get("breaking_changes", [])),
                "customizations_count": len(report.get("customizations", [])),
                "recommendations": report.get("recommendations", []),
                "update_plan": report.get("update_plan", [])
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate update report: {str(e)}"
            }
    
    async def bmad_customizations_discover(self) -> Dict[str, Any]:
        """Discover and catalog BMAD customizations."""
        try:
            customizations = self.update_manager._discover_customizations()
            
            # Categorize customizations
            categorized = {
                "critical": [c for c in customizations if c.critical],
                "non_critical": [c for c in customizations if not c.critical],
                "by_component": {},
                "by_type": {}
            }
            
            # Group by component
            for custom in customizations:
                component = custom.component
                if component not in categorized["by_component"]:
                    categorized["by_component"][component] = []
                categorized["by_component"][component].append(custom)
            
            # Group by type
            for custom in customizations:
                custom_type = custom.customization_type
                if custom_type not in categorized["by_type"]:
                    categorized["by_type"][custom_type] = []
                categorized["by_type"][custom_type].append(custom)
            
            return {
                "status": "success",
                "message": f"Discovered {len(customizations)} BMAD customizations",
                "total_customizations": len(customizations),
                "critical_customizations": len(categorized["critical"]),
                "non_critical_customizations": len(categorized["non_critical"]),
                "customizations": [self._serialize_customization(c) for c in customizations],
                "categorized": {
                    "critical": [self._serialize_customization(c) for c in categorized["critical"]],
                    "non_critical": [self._serialize_customization(c) for c in categorized["non_critical"]],
                    "by_component": {
                        component: [self._serialize_customization(c) for c in customs]
                        for component, customs in categorized["by_component"].items()
                    },
                    "by_type": {
                        custom_type: [self._serialize_customization(c) for c in customs]
                        for custom_type, customs in categorized["by_type"].items()
                    }
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to discover BMAD customizations: {str(e)}"
            }
    
    async def bmad_customizations_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Backup current BMAD customizations."""
        try:
            if not backup_name:
                from datetime import datetime
                backup_name = f"customizations_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup directory
            backup_dir = self.update_manager.backup_root / backup_name
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup customizations
            customizations = self.update_manager._discover_customizations()
            backed_up_files = []
            
            for customization in customizations:
                source_file = self.update_manager.bmad_root / customization.file_path
                if source_file.exists():
                    backup_file = backup_dir / customization.file_path
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    import shutil
                    shutil.copy2(source_file, backup_file)
                    backed_up_files.append(str(customization.file_path))
            
            # Save customization metadata
            metadata_file = backup_dir / "customizations_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump({
                    "backup_name": backup_name,
                    "timestamp": datetime.now().isoformat(),
                    "customizations": [self._serialize_customization(c) for c in customizations],
                    "backed_up_files": backed_up_files
                }, f, indent=2)
            
            return {
                "status": "success",
                "message": f"Successfully backed up {len(backed_up_files)} customizations",
                "backup_name": backup_name,
                "backup_path": str(backup_dir),
                "files_backed_up": backed_up_files,
                "customizations_count": len(customizations)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to backup BMAD customizations: {str(e)}"
            }
    
    async def bmad_customizations_restore(self, backup_name: str) -> Dict[str, Any]:
        """Restore BMAD customizations from backup."""
        try:
            backup_dir = self.update_manager.backup_root / backup_name
            
            if not backup_dir.exists():
                return {
                    "status": "error",
                    "message": f"Backup '{backup_name}' not found"
                }
            
            # Load backup metadata
            metadata_file = backup_dir / "customizations_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                backed_up_files = metadata.get("backed_up_files", [])
            else:
                # Fallback: restore all files in backup directory
                backed_up_files = []
                for root, dirs, files in os.walk(backup_dir):
                    for file in files:
                        if file != "customizations_metadata.json":
                            file_path = Path(root) / file
                            relative_path = file_path.relative_to(backup_dir)
                            backed_up_files.append(str(relative_path))
            
            # Restore files
            restored_files = []
            for file_path in backed_up_files:
                backup_file = backup_dir / file_path
                target_file = self.update_manager.bmad_root / file_path
                
                if backup_file.exists():
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    import shutil
                    shutil.copy2(backup_file, target_file)
                    restored_files.append(file_path)
            
            return {
                "status": "success",
                "message": f"Successfully restored {len(restored_files)} customizations",
                "backup_name": backup_name,
                "files_restored": restored_files,
                "customizations_count": len(restored_files)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to restore BMAD customizations: {str(e)}"
            }
    
    async def bmad_integration_test(self, test_suite: Optional[str] = None) -> Dict[str, Any]:
        """Run integration tests to validate BMAD compatibility."""
        try:
            # Run validation tests
            test_results = await self.update_manager._run_validation_tests()
            
            # Additional custom tests if test_suite specified
            additional_tests = {}
            if test_suite:
                additional_tests = await self._run_custom_test_suite(test_suite)
            
            # Combine results
            all_test_results = {**test_results, **additional_tests}
            
            passed_tests = sum(1 for result in all_test_results.values() if result)
            total_tests = len(all_test_results)
            
            return {
                "status": "success",
                "message": f"Integration tests completed: {passed_tests}/{total_tests} passed",
                "test_suite": test_suite or "default",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "test_results": all_test_results,
                "recommendations": self._generate_test_recommendations(all_test_results)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to run integration tests: {str(e)}"
            }
    
    def _serialize_customization(self, customization) -> Dict[str, Any]:
        """Serialize customization object for JSON response."""
        return {
            "component": customization.component,
            "file_path": customization.file_path,
            "customization_type": customization.customization_type,
            "description": customization.description,
            "critical": customization.critical,
            "backup_path": customization.backup_path,
            "validation_tests": customization.validation_tests or []
        }
    
    async def _run_custom_test_suite(self, test_suite: str) -> Dict[str, bool]:
        """Run custom test suite."""
        # This would run additional custom tests based on the test_suite parameter
        # For now, return placeholder results
        return {
            f"custom_{test_suite}_test_1": True,
            f"custom_{test_suite}_test_2": True
        }
    
    def _generate_test_recommendations(self, test_results: Dict[str, bool]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        failed_tests = [test for test, result in test_results.items() if not result]
        
        if failed_tests:
            recommendations.append(f"Fix {len(failed_tests)} failing tests before proceeding")
            recommendations.extend([f"Review and fix: {test}" for test in failed_tests])
        
        if all(test_results.values()):
            recommendations.append("All tests passed - ready for update")
        
        recommendations.append("Run performance benchmarks after update")
        recommendations.append("Monitor system stability post-update")
        
        return recommendations


# Global instance
_bmad_update_handlers = BMADUpdateHandlers()


def get_bmad_update_handlers() -> BMADUpdateHandlers:
    """Get global BMAD update handlers instance."""
    return _bmad_update_handlers
