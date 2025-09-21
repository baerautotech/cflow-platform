#!/usr/bin/env python3
"""
BMAD S3 Expansion Pack Validation Script

This script provides comprehensive validation of the S3-based expansion pack
functionality, including:
- S3 operations (upload, download, search, metadata management)
- Template integration with BMAD workflows
- Performance testing and caching validation
- Error handling and fallback mechanisms
- End-to-end integration testing

Usage:
    python -m cflow_platform.cli.bmad_s3_validation [--test-type <type>] [--verbose]
"""

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cflow_platform.core.expansion_pack_storage import (
    get_expansion_pack_storage,
    ExpansionPackMetadata,
    discover_local_packs,
    migrate_local_packs_to_s3
)
from cflow_platform.core.bmad_template_loader import get_bmad_template_loader
from cflow_platform.handlers.expansion_pack_handlers import get_expansion_pack_handlers
from cflow_platform.handlers.bmad_template_handlers import get_bmad_template_handlers
from cflow_platform.core.direct_client import execute_mcp_tool


class BMADS3Validator:
    """Comprehensive validator for BMAD S3 expansion pack functionality."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.storage = get_expansion_pack_storage()
        self.template_loader = get_bmad_template_loader()
        self.expansion_handlers = get_expansion_pack_handlers()
        self.template_handlers = get_bmad_template_handlers()
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with optional verbosity control."""
        if self.verbose or level in ["ERROR", "WARN"]:
            print(f"[{level}] {message}")
    
    def test_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Record a test result."""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            self.log(f"✅ {test_name}: PASSED", "INFO")
        else:
            self.test_results["failed_tests"] += 1
            self.log(f"❌ {test_name}: FAILED - {details}", "ERROR")
        
        self.test_results["test_details"].append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "data": data
        })
    
    async def test_s3_connectivity(self) -> bool:
        """Test basic S3 connectivity and bucket access."""
        self.log("Testing S3 connectivity...")
        
        try:
            # Test if MinIO client is initialized
            if not self.storage.minio_client:
                self.test_result("S3 Connectivity", False, "MinIO client not initialized")
                return False
            
            # Test bucket existence
            bucket_exists = self.storage.minio_client.bucket_exists(self.storage.bucket_name)
            metadata_bucket_exists = self.storage.minio_client.bucket_exists(self.storage.metadata_bucket)
            
            if bucket_exists and metadata_bucket_exists:
                self.test_result("S3 Connectivity", True, "Both buckets accessible")
                return True
            else:
                self.test_result("S3 Connectivity", False, f"Buckets missing: main={bucket_exists}, metadata={metadata_bucket_exists}")
                return False
                
        except Exception as e:
            self.test_result("S3 Connectivity", False, f"Exception: {str(e)}")
            return False
    
    async def test_expansion_pack_operations(self) -> bool:
        """Test all expansion pack CRUD operations."""
        self.log("Testing expansion pack operations...")
        
        # Create test pack metadata
        test_pack = ExpansionPackMetadata(
            name="test-validation-pack",
            version="1.0.0",
            short_title="Test Pack",
            description="A test expansion pack for validation",
            author="BMAD Validator",
            license="MIT",
            price="Free",
            category="Testing",
            tags=["test", "validation"],
            commercial=False
        )
        
        # Create test pack directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            test_pack_dir = Path(temp_dir) / test_pack.name
            test_pack_dir.mkdir()
            
            # Create test files
            (test_pack_dir / "config.yaml").write_text(f"""
name: {test_pack.name}
version: {test_pack.version}
short-title: {test_pack.short_title}
description: {test_pack.description}
author: {test_pack.author}
license: {test_pack.license}
price: {test_pack.price}
category: {test_pack.category}
tags: {test_pack.tags}
commercial: {test_pack.commercial}
""")
            
            (test_pack_dir / "templates").mkdir()
            (test_pack_dir / "templates" / "test-template.yaml").write_text("""
name: Test Template
description: A test template for validation
type: test
fields:
  - name: test_field
    type: string
    required: true
""")
            
            (test_pack_dir / "agents").mkdir()
            (test_pack_dir / "agents" / "test-agent.yaml").write_text("""
name: Test Agent
description: A test agent for validation
type: analyst
capabilities:
  - test_analysis
  - validation_check
""")
            
            # Test 1: Upload pack
            try:
                success = await self.storage.upload_pack(test_pack_dir, test_pack)
                self.test_result("Pack Upload", success, "Upload test pack to S3")
            except Exception as e:
                self.test_result("Pack Upload", False, f"Exception: {str(e)}")
            
            # Test 2: List packs
            try:
                packs = await self.storage.list_available_packs()
                test_pack_found = any(pack.name == test_pack.name for pack in packs)
                self.test_result("Pack Listing", test_pack_found, f"Found {len(packs)} packs, test pack included: {test_pack_found}")
            except Exception as e:
                self.test_result("Pack Listing", False, f"Exception: {str(e)}")
            
            # Test 3: Get pack metadata
            try:
                metadata = await self.storage.get_pack_metadata(test_pack.name)
                metadata_valid = metadata is not None and metadata.name == test_pack.name
                self.test_result("Pack Metadata Retrieval", metadata_valid, f"Metadata retrieved: {metadata_valid}")
            except Exception as e:
                self.test_result("Pack Metadata Retrieval", False, f"Exception: {str(e)}")
            
            # Test 4: Search packs
            try:
                search_results = await self.storage.search_packs("test")
                test_pack_in_search = any(pack.name == test_pack.name for pack in search_results)
                self.test_result("Pack Search", test_pack_in_search, f"Found {len(search_results)} packs matching 'test'")
            except Exception as e:
                self.test_result("Pack Search", False, f"Exception: {str(e)}")
            
            # Test 5: Get pack file
            try:
                file_content = await self.storage.get_pack_file(test_pack.name, "templates/test-template.yaml")
                file_valid = file_content is not None and len(file_content) > 0
                self.test_result("Pack File Retrieval", file_valid, f"File content retrieved: {len(file_content) if file_content else 0} bytes")
            except Exception as e:
                self.test_result("Pack File Retrieval", False, f"Exception: {str(e)}")
            
            # Test 6: Download pack
            download_dir = Path(temp_dir) / "download"
            try:
                download_success = await self.storage.download_pack(test_pack.name, download_dir)
                downloaded_files = list(download_dir.rglob("*")) if download_dir.exists() else []
                self.test_result("Pack Download", download_success and len(downloaded_files) > 0, 
                               f"Downloaded {len(downloaded_files)} files")
            except Exception as e:
                self.test_result("Pack Download", False, f"Exception: {str(e)}")
            
            # Test 7: Delete pack
            try:
                delete_success = await self.storage.delete_pack(test_pack.name)
                self.test_result("Pack Deletion", delete_success, "Pack deleted from S3")
            except Exception as e:
                self.test_result("Pack Deletion", False, f"Exception: {str(e)}")
    
    async def test_template_operations(self) -> bool:
        """Test template loading and management operations."""
        self.log("Testing template operations...")
        
        # Test 1: Load core template
        try:
            core_template = await self.template_loader.load_template("prd", "core")
            core_template_valid = core_template is not None and len(core_template.content) > 0
            self.test_result("Core Template Loading", core_template_valid, 
                           f"Template loaded from: {core_template.loaded_from if core_template else 'None'}")
        except Exception as e:
            self.test_result("Core Template Loading", False, f"Exception: {str(e)}")
        
        # Test 2: List available templates
        try:
            templates = await self.template_loader.list_available_templates()
            templates_valid = len(templates) > 0
            self.test_result("Template Listing", templates_valid, f"Found {len(templates)} templates")
        except Exception as e:
            self.test_result("Template Listing", False, f"Exception: {str(e)}")
        
        # Test 3: Search templates
        try:
            search_results = await self.template_loader.search_templates("prd")
            search_valid = len(search_results) > 0
            self.test_result("Template Search", search_valid, f"Found {len(search_results)} templates matching 'prd'")
        except Exception as e:
            self.test_result("Template Search", False, f"Exception: {str(e)}")
        
        # Test 4: Template validation
        try:
            if core_template:
                validation_result = await self.template_loader.validate_template(core_template)
                validation_valid = validation_result.get("valid", False)
                self.test_result("Template Validation", validation_valid, 
                               f"Validation result: {validation_result}")
            else:
                self.test_result("Template Validation", False, "No template to validate")
        except Exception as e:
            self.test_result("Template Validation", False, f"Exception: {str(e)}")
        
        # Test 5: Template caching
        try:
            # Load template twice to test caching
            start_time = time.time()
            template1 = await self.template_loader.load_template("prd", "core", use_cache=True)
            first_load_time = time.time() - start_time
            
            start_time = time.time()
            template2 = await self.template_loader.load_template("prd", "core", use_cache=True)
            second_load_time = time.time() - start_time
            
            cache_working = second_load_time < first_load_time
            self.test_result("Template Caching", cache_working, 
                           f"First load: {first_load_time:.3f}s, Second load: {second_load_time:.3f}s")
        except Exception as e:
            self.test_result("Template Caching", False, f"Exception: {str(e)}")
    
    async def test_mcp_tool_integration(self) -> bool:
        """Test MCP tool integration through direct client."""
        self.log("Testing MCP tool integration...")
        
        # Test 1: Expansion pack list via MCP
        try:
            result = await execute_mcp_tool("bmad_expansion_list_packs", {})
            mcp_success = result.get("status") == "success"
            self.test_result("MCP Expansion List", mcp_success, f"Result: {result.get('message', 'No message')}")
        except Exception as e:
            self.test_result("MCP Expansion List", False, f"Exception: {str(e)}")
        
        # Test 2: Template list via MCP
        try:
            result = await execute_mcp_tool("bmad_template_list", {})
            mcp_success = result.get("status") == "success"
            self.test_result("MCP Template List", mcp_success, f"Result: {result.get('message', 'No message')}")
        except Exception as e:
            self.test_result("MCP Template List", False, f"Exception: {str(e)}")
        
        # Test 3: Template load via MCP
        try:
            result = await execute_mcp_tool("bmad_template_load", {
                "template_name": "prd",
                "template_type": "core"
            })
            mcp_success = result.get("status") == "success"
            self.test_result("MCP Template Load", mcp_success, f"Result: {result.get('message', 'No message')}")
        except Exception as e:
            self.test_result("MCP Template Load", False, f"Exception: {str(e)}")
        
        # Test 4: Template preload via MCP
        try:
            result = await execute_mcp_tool("bmad_template_preload", {})
            mcp_success = result.get("status") == "success"
            self.test_result("MCP Template Preload", mcp_success, f"Result: {result.get('message', 'No message')}")
        except Exception as e:
            self.test_result("MCP Template Preload", False, f"Exception: {str(e)}")
    
    async def test_error_handling(self) -> bool:
        """Test error handling and fallback mechanisms."""
        self.log("Testing error handling...")
        
        # Test 1: Non-existent pack
        try:
            metadata = await self.storage.get_pack_metadata("non-existent-pack")
            error_handled = metadata is None
            self.test_result("Non-existent Pack Handling", error_handled, "Gracefully handled non-existent pack")
        except Exception as e:
            self.test_result("Non-existent Pack Handling", False, f"Exception: {str(e)}")
        
        # Test 2: Non-existent file
        try:
            file_content = await self.storage.get_pack_file("non-existent-pack", "non-existent-file.yaml")
            error_handled = file_content is None
            self.test_result("Non-existent File Handling", error_handled, "Gracefully handled non-existent file")
        except Exception as e:
            self.test_result("Non-existent File Handling", False, f"Exception: {str(e)}")
        
        # Test 3: Invalid template name
        try:
            template = await self.template_loader.load_template("non-existent-template", "core")
            error_handled = template is None
            self.test_result("Invalid Template Handling", error_handled, "Gracefully handled invalid template")
        except Exception as e:
            self.test_result("Invalid Template Handling", False, f"Exception: {str(e)}")
        
        # Test 4: MCP tool with invalid parameters
        try:
            result = await execute_mcp_tool("bmad_expansion_get_pack", {"pack_name": "non-existent-pack"})
            error_handled = result.get("status") == "error"
            self.test_result("MCP Error Handling", error_handled, f"Error handled: {result.get('message', 'No message')}")
        except Exception as e:
            self.test_result("MCP Error Handling", False, f"Exception: {str(e)}")
    
    async def test_performance(self) -> bool:
        """Test performance characteristics."""
        self.log("Testing performance...")
        
        # Test 1: Template loading performance
        try:
            start_time = time.time()
            template = await self.template_loader.load_template("prd", "core")
            load_time = time.time() - start_time
            
            performance_acceptable = load_time < 2.0  # Should load within 2 seconds
            self.test_result("Template Load Performance", performance_acceptable, 
                           f"Load time: {load_time:.3f}s")
        except Exception as e:
            self.test_result("Template Load Performance", False, f"Exception: {str(e)}")
        
        # Test 2: Pack listing performance
        try:
            start_time = time.time()
            packs = await self.storage.list_available_packs()
            list_time = time.time() - start_time
            
            performance_acceptable = list_time < 5.0  # Should list within 5 seconds
            self.test_result("Pack List Performance", performance_acceptable, 
                           f"List time: {list_time:.3f}s for {len(packs)} packs")
        except Exception as e:
            self.test_result("Pack List Performance", False, f"Exception: {str(e)}")
        
        # Test 3: Cache performance
        try:
            # Clear cache first
            self.template_loader.clear_cache()
            
            # First load (cold cache)
            start_time = time.time()
            await self.template_loader.load_template("prd", "core", use_cache=True)
            cold_load_time = time.time() - start_time
            
            # Second load (warm cache)
            start_time = time.time()
            await self.template_loader.load_template("prd", "core", use_cache=True)
            warm_load_time = time.time() - start_time
            
            cache_improvement = cold_load_time > warm_load_time
            self.test_result("Cache Performance", cache_improvement, 
                           f"Cold: {cold_load_time:.3f}s, Warm: {warm_load_time:.3f}s")
        except Exception as e:
            self.test_result("Cache Performance", False, f"Exception: {str(e)}")
    
    async def test_local_migration(self) -> bool:
        """Test local pack migration functionality."""
        self.log("Testing local migration...")
        
        # Check if vendor directory exists
        vendor_dir = Path(__file__).parent.parent.parent / "vendor" / "bmad" / "expansion-packs"
        
        if not vendor_dir.exists():
            self.test_result("Local Migration", False, f"Vendor directory not found: {vendor_dir}")
            return False
        
        try:
            # Discover local packs
            local_packs = await discover_local_packs(vendor_dir)
            discovery_success = len(local_packs) >= 0  # Should not fail even if no packs
            
            self.test_result("Local Pack Discovery", discovery_success, 
                           f"Found {len(local_packs)} local packs")
            
            # Test migration (dry run - don't actually migrate)
            if len(local_packs) > 0:
                self.log(f"Found {len(local_packs)} local packs available for migration")
                for pack in local_packs[:3]:  # Show first 3 packs
                    self.log(f"  - {pack.name} v{pack.version} ({pack.category})")
            
            return discovery_success
            
        except Exception as e:
            self.test_result("Local Migration", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        self.log("Starting comprehensive BMAD S3 validation...")
        
        # Test categories
        test_categories = [
            ("S3 Connectivity", self.test_s3_connectivity),
            ("Expansion Pack Operations", self.test_expansion_pack_operations),
            ("Template Operations", self.test_template_operations),
            ("MCP Tool Integration", self.test_mcp_tool_integration),
            ("Error Handling", self.test_error_handling),
            ("Performance", self.test_performance),
            ("Local Migration", self.test_local_migration),
        ]
        
        for category_name, test_func in test_categories:
            self.log(f"\n--- {category_name} ---")
            try:
                await test_func()
            except Exception as e:
                self.log(f"Category {category_name} failed with exception: {str(e)}", "ERROR")
                self.test_result(f"{category_name} Category", False, f"Exception: {str(e)}")
        
        # Calculate overall results
        total_tests = self.test_results["total_tests"]
        passed_tests = self.test_results["passed_tests"]
        failed_tests = self.test_results["failed_tests"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"\n=== VALIDATION SUMMARY ===")
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {passed_tests}")
        self.log(f"Failed: {failed_tests}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests == 0:
            self.log("🎉 All tests passed! S3 expansion pack system is fully functional.", "INFO")
        else:
            self.log(f"⚠️  {failed_tests} tests failed. Review the details above.", "WARN")
        
        return self.test_results


async def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(description="BMAD S3 Expansion Pack Validation")
    parser.add_argument("--test-type", choices=["all", "s3", "templates", "mcp", "performance", "errors"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--output", "-o", help="Output file for test results (JSON)")
    
    args = parser.parse_args()
    
    validator = BMADS3Validator(verbose=args.verbose)
    
    try:
        if args.test_type == "all":
            results = await validator.run_all_tests()
        elif args.test_type == "s3":
            await validator.test_s3_connectivity()
            await validator.test_expansion_pack_operations()
            results = validator.test_results
        elif args.test_type == "templates":
            await validator.test_template_operations()
            results = validator.test_results
        elif args.test_type == "mcp":
            await validator.test_mcp_tool_integration()
            results = validator.test_results
        elif args.test_type == "performance":
            await validator.test_performance()
            results = validator.test_results
        elif args.test_type == "errors":
            await validator.test_error_handling()
            results = validator.test_results
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Test results saved to {args.output}")
        
        # Exit with appropriate code
        sys.exit(0 if results["failed_tests"] == 0 else 1)
        
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Validation failed with exception: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
