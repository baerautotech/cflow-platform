"""
BMAD Update Management System

This module provides comprehensive update management for BMAD-method updates,
including automated testing, validation, and customization preservation.
"""

import os
import json
import yaml
import asyncio
import hashlib
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import git
import requests
from packaging import version

from cflow_platform.core.config.vault_config import get_vault_config


@dataclass
class BMADUpdateInfo:
    """Information about a BMAD update."""
    current_version: str
    latest_version: str
    update_available: bool
    changelog: List[Dict[str, Any]]
    breaking_changes: List[str]
    new_features: List[str]
    bug_fixes: List[str]
    dependencies_updated: List[str]
    api_changes: List[Dict[str, Any]]
    last_checked: str


@dataclass
class CustomizationMapping:
    """Mapping of customizations to BMAD components."""
    component: str  # bmad-core, expansion-packs, docs, tools
    file_path: str
    customization_type: str  # override, extension, integration, configuration
    description: str
    critical: bool  # Whether this customization is critical for platform operation
    backup_path: Optional[str] = None
    validation_tests: List[str] = None


@dataclass
class UpdateValidationResult:
    """Result of update validation."""
    success: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    breaking_changes: List[str]
    customizations_affected: List[str]
    test_results: Dict[str, bool]
    performance_impact: Optional[Dict[str, Any]] = None


class BMADUpdateManager:
    """Manages BMAD updates with customization preservation."""
    
    def __init__(self):
        self.vault_config = get_vault_config()
        self.bmad_root = Path(__file__).parent.parent.parent / "vendor" / "bmad"
        self.backup_root = Path(__file__).parent.parent.parent / ".bmad_backups"
        self.customizations_file = self.bmad_root.parent / "bmad_customizations.json"
        self.update_log_file = self.bmad_root.parent / "bmad_update_log.json"
        self.cflow_platform_root = Path(__file__).parent.parent.parent
        
        # Ensure backup directory exists
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        # Load customizations
        self.customizations = self._load_customizations()
        
        # GitHub API configuration
        self.github_api_base = "https://api.github.com/repos/bmadcode/BMAD-METHOD"
        self.github_token = self.vault_config.get_config_value_sync("GITHUB_TOKEN", "github")
    
    def _load_customizations(self) -> List[CustomizationMapping]:
        """Load customization mappings from file."""
        if not self.customizations_file.exists():
            return []
        
        try:
            with open(self.customizations_file, 'r') as f:
                data = json.load(f)
            
            return [CustomizationMapping(**item) for item in data.get('customizations', [])]
        except Exception as e:
            print(f"[WARN] BMAD Update Manager: Failed to load customizations: {e}")
            return []
    
    def _save_customizations(self) -> None:
        """Save customization mappings to file."""
        try:
            data = {
                "customizations": [asdict(custom) for custom in self.customizations],
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "version": "1.0"
            }
            
            with open(self.customizations_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"[ERROR] BMAD Update Manager: Failed to save customizations: {e}")
    
    def _discover_customizations(self) -> List[CustomizationMapping]:
        """Automatically discover customizations in the BMAD vendor directory."""
        customizations = []
        
        # Scan for customizations in BMAD directory
        for root, dirs, files in os.walk(self.bmad_root):
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.bmad_root)
                
                # Check if file has been modified (customized)
                if self._is_file_customized(file_path):
                    component = self._determine_component(relative_path)
                    customization_type = self._determine_customization_type(file_path)
                    
                    customizations.append(CustomizationMapping(
                        component=component,
                        file_path=str(relative_path),
                        customization_type=customization_type,
                        description=f"Customized {file_path.name}",
                        critical=self._is_critical_customization(relative_path),
                        validation_tests=self._get_validation_tests(relative_path)
                    ))
        
        # Check for cflow-platform integration points
        integration_points = self._discover_integration_points()
        customizations.extend(integration_points)
        
        return customizations
    
    def _is_file_customized(self, file_path: Path) -> bool:
        """Check if a file has been customized (not original BMAD)."""
        # This is a simplified check - in practice, you'd use git history
        # or checksums to determine if files have been modified
        
        # Check for cflow-platform specific markers
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for cflow-platform specific markers
            markers = [
                "cflow_platform",
                "cerebral",
                "Cerebral",
                "BMAD-Cerebral integration",
                "headless integration"
            ]
            
            return any(marker in content for marker in markers)
            
        except Exception:
            return False
    
    def _determine_component(self, relative_path: Path) -> str:
        """Determine which BMAD component a file belongs to."""
        path_str = str(relative_path)
        
        if "bmad-core" in path_str:
            return "bmad-core"
        elif "expansion-packs" in path_str:
            return "expansion-packs"
        elif "docs" in path_str:
            return "docs"
        elif "tools" in path_str:
            return "tools"
        else:
            return "other"
    
    def _determine_customization_type(self, file_path: Path) -> str:
        """Determine the type of customization."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "override" in content.lower() or "replaces" in content.lower():
                return "override"
            elif "extends" in content.lower() or "extends" in content.lower():
                return "extension"
            elif "integration" in content.lower():
                return "integration"
            elif "config" in file_path.name.lower():
                return "configuration"
            else:
                return "modification"
                
        except Exception:
            return "unknown"
    
    def _is_critical_customization(self, relative_path: Path) -> bool:
        """Determine if a customization is critical for platform operation."""
        path_str = str(relative_path)
        
        # Critical files for cflow-platform integration
        critical_patterns = [
            "core-config.yaml",
            "bmad-kb.md",
            "workflows/",
            "templates/",
            "README.md"
        ]
        
        return any(pattern in path_str for pattern in critical_patterns)
    
    def _get_validation_tests(self, relative_path: Path) -> List[str]:
        """Get validation tests for a customization."""
        path_str = str(relative_path)
        
        tests = []
        
        if "workflows" in path_str:
            tests.extend([
                "test_bmad_workflow_engine",
                "test_basic_workflow_implementations"
            ])
        
        if "templates" in path_str:
            tests.extend([
                "test_bmad_templates",
                "test_document_generation"
            ])
        
        if "core-config" in path_str:
            tests.extend([
                "test_bmad_configuration",
                "test_agent_initialization"
            ])
        
        return tests
    
    def _discover_integration_points(self) -> List[CustomizationMapping]:
        """Discover cflow-platform integration points with BMAD."""
        integration_points = []
        
        # Check cflow-platform files that reference BMAD
        cflow_files = [
            "cflow_platform/core/bmad_workflow_engine.py",
            "cflow_platform/core/basic_workflow_implementations.py",
            "cflow_platform/handlers/bmad_handlers.py",
            "cflow_platform/tests/test_bmad_integration.py"
        ]
        
        for file_path in cflow_files:
            full_path = self.cflow_platform_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if "vendor/bmad" in content:
                        integration_points.append(CustomizationMapping(
                            component="cflow-platform",
                            file_path=file_path,
                            customization_type="integration",
                            description=f"cflow-platform integration with BMAD in {Path(file_path).name}",
                            critical=True,
                            validation_tests=["test_bmad_integration"]
                        ))
                        
                except Exception as e:
                    print(f"[WARN] BMAD Update Manager: Failed to analyze {file_path}: {e}")
        
        return integration_points
    
    async def check_for_updates(self) -> BMADUpdateInfo:
        """Check for available BMAD updates."""
        try:
            # Get current version from vendor directory
            current_version = self._get_current_version()
            
            # Get latest version from GitHub API
            latest_version, changelog = await self._get_latest_version_info()
            
            # Parse changelog for breaking changes, features, etc.
            breaking_changes = self._extract_breaking_changes(changelog)
            new_features = self._extract_new_features(changelog)
            bug_fixes = self._extract_bug_fixes(changelog)
            dependencies_updated = self._extract_dependencies_updated(changelog)
            api_changes = self._extract_api_changes(changelog)
            
            return BMADUpdateInfo(
                current_version=current_version,
                latest_version=latest_version,
                update_available=version.parse(latest_version) > version.parse(current_version),
                changelog=changelog,
                breaking_changes=breaking_changes,
                new_features=new_features,
                bug_fixes=bug_fixes,
                dependencies_updated=dependencies_updated,
                api_changes=api_changes,
                last_checked=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            print(f"[ERROR] BMAD Update Manager: Failed to check for updates: {e}")
            return BMADUpdateInfo(
                current_version="unknown",
                latest_version="unknown",
                update_available=False,
                changelog=[],
                breaking_changes=[],
                new_features=[],
                bug_fixes=[],
                dependencies_updated=[],
                api_changes=[],
                last_checked=datetime.now(timezone.utc).isoformat()
            )
    
    def _get_current_version(self) -> str:
        """Get current BMAD version from vendor directory."""
        try:
            # Try to get version from git tag or version file
            if (self.bmad_root / ".git").exists():
                repo = git.Repo(self.bmad_root)
                tags = repo.tags
                if tags:
                    # Get the latest tag
                    latest_tag = sorted(tags, key=lambda t: version.parse(t.name.lstrip('v')))[-1]
                    return latest_tag.name.lstrip('v')
            
            # Fallback: check for version in core config
            config_file = self.bmad_root / "bmad-core" / "core-config.yaml"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('version', '1.0.0')
            
            return "1.0.0"  # Default version
            
        except Exception as e:
            print(f"[WARN] BMAD Update Manager: Failed to get current version: {e}")
            return "1.0.0"
    
    async def _get_latest_version_info(self) -> Tuple[str, List[Dict[str, Any]]]:
        """Get latest version and changelog from GitHub API."""
        try:
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            
            # Get latest release
            response = requests.get(f"{self.github_api_base}/releases/latest", headers=headers)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip('v')
            
            # Get changelog from release notes
            changelog = [{
                "version": latest_version,
                "date": release_data["published_at"],
                "notes": release_data["body"],
                "url": release_data["html_url"]
            }]
            
            return latest_version, changelog
            
        except Exception as e:
            print(f"[ERROR] BMAD Update Manager: Failed to get latest version info: {e}")
            return "1.0.0", []
    
    def _extract_breaking_changes(self, changelog: List[Dict[str, Any]]) -> List[str]:
        """Extract breaking changes from changelog."""
        breaking_changes = []
        
        for entry in changelog:
            notes = entry.get("notes", "").lower()
            
            # Look for breaking change indicators
            if any(keyword in notes for keyword in ["breaking", "breaking change", "incompatible", "deprecated"]):
                # Extract the breaking change description
                lines = entry.get("notes", "").split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ["breaking", "breaking change", "incompatible", "deprecated"]):
                        breaking_changes.append(line.strip())
        
        return breaking_changes
    
    def _extract_new_features(self, changelog: List[Dict[str, Any]]) -> List[str]:
        """Extract new features from changelog."""
        new_features = []
        
        for entry in changelog:
            notes = entry.get("notes", "")
            lines = notes.split('\n')
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ["feature", "new", "added", "enhancement"]):
                    if line.strip().startswith(('*', '-', '+', '•')):
                        new_features.append(line.strip())
        
        return new_features
    
    def _extract_bug_fixes(self, changelog: List[Dict[str, Any]]) -> List[str]:
        """Extract bug fixes from changelog."""
        bug_fixes = []
        
        for entry in changelog:
            notes = entry.get("notes", "")
            lines = notes.split('\n')
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ["fix", "bug", "issue", "resolved"]):
                    if line.strip().startswith(('*', '-', '+', '•')):
                        bug_fixes.append(line.strip())
        
        return bug_fixes
    
    def _extract_dependencies_updated(self, changelog: List[Dict[str, Any]]) -> List[str]:
        """Extract dependency updates from changelog."""
        dependencies = []
        
        for entry in changelog:
            notes = entry.get("notes", "")
            lines = notes.split('\n')
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ["dependency", "package", "npm", "pip", "update"]):
                    if line.strip().startswith(('*', '-', '+', '•')):
                        dependencies.append(line.strip())
        
        return dependencies
    
    def _extract_api_changes(self, changelog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract API changes from changelog."""
        api_changes = []
        
        for entry in changelog:
            notes = entry.get("notes", "")
            lines = notes.split('\n')
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ["api", "endpoint", "interface", "method"]):
                    if line.strip().startswith(('*', '-', '+', '•')):
                        api_changes.append({
                            "description": line.strip(),
                            "type": "api_change",
                            "version": entry.get("version", "unknown")
                        })
        
        return api_changes
    
    async def validate_update(self, target_version: str) -> UpdateValidationResult:
        """Validate an update before applying it."""
        errors = []
        warnings = []
        suggestions = []
        breaking_changes = []
        customizations_affected = []
        test_results = {}
        
        try:
            # Check for breaking changes
            update_info = await self.check_for_updates()
            breaking_changes = update_info.breaking_changes
            
            if breaking_changes:
                warnings.append(f"Breaking changes detected: {len(breaking_changes)} changes")
                suggestions.append("Review breaking changes and update customizations accordingly")
            
            # Check which customizations will be affected
            for customization in self.customizations:
                if self._customization_will_be_affected(customization, target_version):
                    customizations_affected.append(customization.file_path)
                    if customization.critical:
                        errors.append(f"Critical customization affected: {customization.file_path}")
                        suggestions.append(f"Backup and update customization: {customization.file_path}")
            
            # Run validation tests
            test_results = await self._run_validation_tests()
            
            # Check for performance impact
            performance_impact = await self._assess_performance_impact(target_version)
            
            success = len(errors) == 0 and all(test_results.values())
            
            return UpdateValidationResult(
                success=success,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                breaking_changes=breaking_changes,
                customizations_affected=customizations_affected,
                test_results=test_results,
                performance_impact=performance_impact
            )
            
        except Exception as e:
            return UpdateValidationResult(
                success=False,
                errors=[f"Validation failed: {str(e)}"],
                warnings=[],
                suggestions=["Fix validation errors before proceeding"],
                breaking_changes=[],
                customizations_affected=[],
                test_results={}
            )
    
    def _customization_will_be_affected(self, customization: CustomizationMapping, target_version: str) -> bool:
        """Check if a customization will be affected by the update."""
        # This is a simplified check - in practice, you'd analyze the diff
        # between current and target versions
        
        # Critical customizations are always considered affected
        if customization.critical:
            return True
        
        # Check if the component has changes in the target version
        # This would require analyzing the changelog or git diff
        return True  # Simplified for now
    
    async def _run_validation_tests(self) -> Dict[str, bool]:
        """Run validation tests to ensure platform compatibility."""
        test_results = {}
        
        # Run cflow-platform tests
        test_commands = [
            "python -m pytest cflow_platform/tests/test_bmad_integration.py -v",
            "python -m pytest cflow_platform/tests/test_basic_workflow_implementations.py -v",
            "python -m pytest cflow_platform/tests/test_bmad_workflow_engine.py -v"
        ]
        
        for test_cmd in test_commands:
            try:
                result = subprocess.run(
                    test_cmd.split(),
                    cwd=self.cflow_platform_root,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                test_name = test_cmd.split()[-1].replace('.py', '').replace('test_', '')
                test_results[test_name] = result.returncode == 0
                
                if result.returncode != 0:
                    print(f"[WARN] BMAD Update Manager: Test {test_name} failed: {result.stderr}")
                    
            except Exception as e:
                test_name = test_cmd.split()[-1].replace('.py', '').replace('test_', '')
                test_results[test_name] = False
                print(f"[ERROR] BMAD Update Manager: Test {test_name} failed: {e}")
        
        return test_results
    
    async def _assess_performance_impact(self, target_version: str) -> Optional[Dict[str, Any]]:
        """Assess the performance impact of the update."""
        # This would run performance benchmarks and compare results
        # For now, return a placeholder
        return {
            "memory_usage_change": "unknown",
            "startup_time_change": "unknown",
            "workflow_execution_time_change": "unknown",
            "recommendations": ["Run performance benchmarks after update"]
        }
    
    async def apply_update(self, target_version: str, preserve_customizations: bool = True) -> bool:
        """Apply a BMAD update while preserving customizations."""
        try:
            # Create backup
            backup_path = await self._create_backup()
            
            # Apply update
            success = await self._apply_git_update(target_version)
            
            if not success:
                # Restore from backup
                await self._restore_backup(backup_path)
                return False
            
            # Restore customizations
            if preserve_customizations:
                await self._restore_customizations(backup_path)
            
            # Update customization mappings
            self.customizations = self._discover_customizations()
            self._save_customizations()
            
            # Log update
            await self._log_update(target_version, backup_path)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] BMAD Update Manager: Failed to apply update: {e}")
            return False
    
    async def _create_backup(self) -> Path:
        """Create a backup of the current BMAD directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_root / f"bmad_backup_{timestamp}"
        
        try:
            shutil.copytree(self.bmad_root, backup_path)
            print(f"[INFO] BMAD Update Manager: Created backup at {backup_path}")
            return backup_path
        except Exception as e:
            print(f"[ERROR] BMAD Update Manager: Failed to create backup: {e}")
            raise
    
    async def _apply_git_update(self, target_version: str) -> bool:
        """Apply the update using git."""
        try:
            if not (self.bmad_root / ".git").exists():
                print("[ERROR] BMAD Update Manager: Not a git repository")
                return False
            
            repo = git.Repo(self.bmad_root)
            
            # Fetch latest changes
            repo.remotes.origin.fetch()
            
            # Checkout target version
            repo.git.checkout(f"v{target_version}")
            
            print(f"[INFO] BMAD Update Manager: Updated to version {target_version}")
            return True
            
        except Exception as e:
            print(f"[ERROR] BMAD Update Manager: Failed to apply git update: {e}")
            return False
    
    async def _restore_customizations(self, backup_path: Path) -> None:
        """Restore customizations from backup."""
        try:
            for customization in self.customizations:
                if customization.critical:
                    source_file = backup_path / customization.file_path
                    target_file = self.bmad_root / customization.file_path
                    
                    if source_file.exists() and target_file.exists():
                        shutil.copy2(source_file, target_file)
                        print(f"[INFO] BMAD Update Manager: Restored customization: {customization.file_path}")
                        
        except Exception as e:
            print(f"[ERROR] BMAD Update Manager: Failed to restore customizations: {e}")
    
    async def _restore_backup(self, backup_path: Path) -> None:
        """Restore from backup in case of update failure."""
        try:
            if backup_path.exists():
                shutil.rmtree(self.bmad_root)
                shutil.copytree(backup_path, self.bmad_root)
                print(f"[INFO] BMAD Update Manager: Restored from backup: {backup_path}")
                
        except Exception as e:
            print(f"[ERROR] BMAD Update Manager: Failed to restore from backup: {e}")
    
    async def _log_update(self, target_version: str, backup_path: Path) -> None:
        """Log the update for audit purposes."""
        try:
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": target_version,
                "backup_path": str(backup_path),
                "customizations_restored": len(self.customizations),
                "success": True
            }
            
            # Load existing log
            log_data = []
            if self.update_log_file.exists():
                with open(self.update_log_file, 'r') as f:
                    log_data = json.load(f)
            
            # Add new entry
            log_data.append(log_entry)
            
            # Save updated log
            with open(self.update_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"[ERROR] BMAD Update Manager: Failed to log update: {e}")
    
    async def generate_update_report(self, target_version: str) -> Dict[str, Any]:
        """Generate a comprehensive update report."""
        try:
            # Check for updates
            update_info = await self.check_for_updates()
            
            # Validate update
            validation_result = await self.validate_update(target_version)
            
            # Discover customizations
            customizations = self._discover_customizations()
            
            # Generate report
            report = {
                "update_info": asdict(update_info),
                "validation_result": asdict(validation_result),
                "customizations": [asdict(custom) for custom in customizations],
                "recommendations": self._generate_recommendations(validation_result, customizations),
                "update_plan": self._generate_update_plan(validation_result, customizations),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            return report
            
        except Exception as e:
            return {
                "error": str(e),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
    
    def _generate_recommendations(self, validation_result: UpdateValidationResult, customizations: List[CustomizationMapping]) -> List[str]:
        """Generate recommendations for the update."""
        recommendations = []
        
        if validation_result.breaking_changes:
            recommendations.append("Review breaking changes carefully before updating")
        
        if validation_result.customizations_affected:
            recommendations.append(f"Backup and review {len(validation_result.customizations_affected)} affected customizations")
        
        if not validation_result.test_results or not all(validation_result.test_results.values()):
            recommendations.append("Fix failing tests before applying update")
        
        if validation_result.errors:
            recommendations.append("Resolve critical errors before proceeding")
        
        recommendations.append("Run full test suite after update")
        recommendations.append("Monitor performance metrics post-update")
        
        return recommendations
    
    def _generate_update_plan(self, validation_result: UpdateValidationResult, customizations: List[CustomizationMapping]) -> List[str]:
        """Generate a step-by-step update plan."""
        plan = [
            "1. Create full backup of vendor/bmad directory",
            "2. Run validation tests to ensure compatibility",
            "3. Review breaking changes and affected customizations",
            "4. Apply BMAD update using git checkout",
            "5. Restore critical customizations from backup",
            "6. Update customization mappings",
            "7. Run comprehensive test suite",
            "8. Verify platform functionality",
            "9. Monitor performance metrics",
            "10. Document update in changelog"
        ]
        
        return plan


# Global instance
_bmad_update_manager = None


def get_bmad_update_manager() -> BMADUpdateManager:
    """Get global BMAD update manager instance."""
    global _bmad_update_manager
    if _bmad_update_manager is None:
        _bmad_update_manager = BMADUpdateManager()
    return _bmad_update_manager


# CLI interface
async def main():
    """CLI interface for BMAD update management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="BMAD Update Manager")
    parser.add_argument("command", choices=["check", "validate", "update", "report"], help="Command to execute")
    parser.add_argument("--version", help="Target version for update")
    parser.add_argument("--preserve-customizations", action="store_true", default=True, help="Preserve customizations during update")
    
    args = parser.parse_args()
    
    manager = get_bmad_update_manager()
    
    if args.command == "check":
        update_info = await manager.check_for_updates()
        print(f"Current version: {update_info.current_version}")
        print(f"Latest version: {update_info.latest_version}")
        print(f"Update available: {update_info.update_available}")
        
        if update_info.update_available:
            print(f"\nNew features: {len(update_info.new_features)}")
            print(f"Bug fixes: {len(update_info.bug_fixes)}")
            print(f"Breaking changes: {len(update_info.breaking_changes)}")
    
    elif args.command == "validate":
        if not args.version:
            print("Error: --version required for validate command")
            return
        
        validation_result = await manager.validate_update(args.version)
        print(f"Validation success: {validation_result.success}")
        
        if validation_result.errors:
            print(f"Errors: {validation_result.errors}")
        if validation_result.warnings:
            print(f"Warnings: {validation_result.warnings}")
        if validation_result.suggestions:
            print(f"Suggestions: {validation_result.suggestions}")
    
    elif args.command == "update":
        if not args.version:
            print("Error: --version required for update command")
            return
        
        success = await manager.apply_update(args.version, args.preserve_customizations)
        print(f"Update success: {success}")
    
    elif args.command == "report":
        if not args.version:
            print("Error: --version required for report command")
            return
        
        report = await manager.generate_update_report(args.version)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
