#!/usr/bin/env python3
"""
Comprehensive Test Runner for All Systems

This script runs all test suites and generates coverage reports
to achieve 100% test coverage across all implemented systems.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
import logging


class TestRunner:
    """Runs comprehensive tests across all systems."""

    def __init__(self, project_root: str = "/home/calelin/dev/canary"):
        """Initialize test runner."""
        self.project_root = Path(project_root)
        self.systems = [
            "task-manager",
            "task-master", 
            "systems/tinyurl",
            "systems/newsfeed",
            "systems/google-docs",
            "systems/quora",
            "systems/load_balancer",
            "systems/monitoring"
        ]
        self.coverage_results = {}
        self.test_results = {}
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test_runner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def run_system_tests(self, system_path: str) -> Tuple[bool, Dict]:
        """Run tests for a specific system."""
        system_dir = self.project_root / system_path
        
        if not system_dir.exists():
            self.logger.warning(f"System directory not found: {system_path}")
            return False, {"error": "Directory not found"}

        self.logger.info(f"Running tests for {system_path}")
        
        # Check if requirements.txt exists
        requirements_file = system_dir / "requirements.txt"
        if requirements_file.exists():
            self.logger.info(f"Installing requirements for {system_path}")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to install requirements for {system_path}: {e}")
                return False, {"error": f"Requirements installation failed: {e}"}

        # Find test files
        test_files = list(system_dir.glob("test_*.py"))
        if not test_files:
            self.logger.warning(f"No test files found in {system_path}")
            return False, {"error": "No test files found"}

        # Run tests with coverage
        coverage_results = {}
        test_success = True
        
        for test_file in test_files:
            self.logger.info(f"Running {test_file.name}")
            
            try:
                # Run with coverage
                result = subprocess.run([
                    sys.executable, "-m", "coverage", "run", "--source=.", "--omit=test_*.py", str(test_file)
                ], cwd=system_dir, capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.logger.error(f"Tests failed for {test_file.name}: {result.stderr}")
                    test_success = False
                
                # Generate coverage report
                coverage_result = subprocess.run([
                    sys.executable, "-m", "coverage", "report", "--format=json"
                ], cwd=system_dir, capture_output=True, text=True)
                
                if coverage_result.returncode == 0:
                    coverage_data = json.loads(coverage_result.stdout)
                    coverage_results[test_file.name] = coverage_data
                else:
                    self.logger.error(f"Coverage report failed for {test_file.name}")
                    
            except Exception as e:
                self.logger.error(f"Error running tests for {test_file.name}: {e}")
                test_success = False

        return test_success, coverage_results

    def run_all_tests(self) -> Dict:
        """Run tests for all systems."""
        self.logger.info("Starting comprehensive test run")
        start_time = time.time()
        
        overall_success = True
        total_coverage = 0
        system_count = 0
        
        for system in self.systems:
            self.logger.info(f"Testing system: {system}")
            
            success, coverage_data = self.run_system_tests(system)
            
            self.test_results[system] = {
                "success": success,
                "coverage_data": coverage_data
            }
            
            if not success:
                overall_success = False
            
            # Calculate coverage percentage
            if coverage_data and not isinstance(coverage_data, dict) or "error" not in coverage_data:
                for test_file, data in coverage_data.items():
                    if isinstance(data, dict) and "totals" in data:
                        coverage_pct = data["totals"].get("percent_covered", 0)
                        total_coverage += coverage_pct
                        system_count += 1
                        self.logger.info(f"{system}/{test_file}: {coverage_pct:.1f}% coverage")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate average coverage
        avg_coverage = total_coverage / system_count if system_count > 0 else 0
        
        results = {
            "overall_success": overall_success,
            "total_duration": duration,
            "average_coverage": avg_coverage,
            "system_results": self.test_results,
            "timestamp": time.time()
        }
        
        self.logger.info(f"Test run completed in {duration:.2f} seconds")
        self.logger.info(f"Overall success: {overall_success}")
        self.logger.info(f"Average coverage: {avg_coverage:.1f}%")
        
        return results

    def generate_coverage_report(self) -> str:
        """Generate comprehensive coverage report."""
        report_lines = [
            "# Comprehensive Test Coverage Report",
            f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Overall Success: {'✅' if self.test_results.get('overall_success', False) else '❌'}",
            f"- Average Coverage: {self.test_results.get('average_coverage', 0):.1f}%",
            f"- Total Duration: {self.test_results.get('total_duration', 0):.2f}s",
            "",
            "## System Details",
            ""
        ]
        
        for system, data in self.test_results.get("system_results", {}).items():
            report_lines.append(f"### {system}")
            report_lines.append(f"- Success: {'✅' if data.get('success', False) else '❌'}")
            
            coverage_data = data.get("coverage_data", {})
            if isinstance(coverage_data, dict) and "error" not in coverage_data:
                for test_file, coverage_info in coverage_data.items():
                    if isinstance(coverage_info, dict) and "totals" in coverage_info:
                        totals = coverage_info["totals"]
                        coverage_pct = totals.get("percent_covered", 0)
                        report_lines.append(f"- {test_file}: {coverage_pct:.1f}% coverage")
                        
                        # Add detailed coverage info
                        if "covered_lines" in totals and "num_statements" in totals:
                            covered = totals["covered_lines"]
                            total = totals["num_statements"]
                            report_lines.append(f"  - Lines: {covered}/{total}")
                        
                        if "missing_lines" in coverage_info:
                            missing = coverage_info["missing_lines"]
                            if missing:
                                report_lines.append(f"  - Missing lines: {missing}")
            else:
                report_lines.append(f"- Error: {coverage_data.get('error', 'Unknown error')}")
            
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        # Save report to file
        report_file = self.project_root / "coverage_report.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        self.logger.info(f"Coverage report saved to: {report_file}")
        return report_content

    def check_coverage_threshold(self, threshold: float = 90.0) -> bool:
        """Check if coverage meets threshold."""
        avg_coverage = self.test_results.get("average_coverage", 0)
        meets_threshold = avg_coverage >= threshold
        
        if meets_threshold:
            self.logger.info(f"✅ Coverage threshold met: {avg_coverage:.1f}% >= {threshold}%")
        else:
            self.logger.warning(f"❌ Coverage threshold not met: {avg_coverage:.1f}% < {threshold}%")
        
        return meets_threshold

    def run_performance_tests(self) -> Dict:
        """Run performance tests for critical systems."""
        self.logger.info("Running performance tests")
        
        performance_results = {}
        
        # Test TinyURL system performance
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'systems', 'tinyurl'))
            from tinyurl_service import TinyURLService
            import time
            
            service = TinyURLService(":memory:")
            
            # Test URL shortening performance
            start_time = time.time()
            for i in range(100):
                service.shorten_url(f"https://example.com/page{i}")
            shorten_time = time.time() - start_time
            
            performance_results["tinyurl"] = {
                "shorten_100_urls": f"{shorten_time:.3f}s",
                "avg_per_url": f"{shorten_time/100*1000:.2f}ms"
            }
            
        except Exception as e:
            self.logger.error(f"TinyURL performance test failed: {e}")
            performance_results["tinyurl"] = {"error": str(e)}
        
        # Test Newsfeed system performance
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'systems', 'newsfeed'))
            from newsfeed_service import NewsfeedService
            
            service = NewsfeedService(":memory:")
            
            # Test newsfeed generation performance
            start_time = time.time()
            for i in range(50):
                service.get_newsfeed(limit=20)
            feed_time = time.time() - start_time
            
            performance_results["newsfeed"] = {
                "generate_50_feeds": f"{feed_time:.3f}s",
                "avg_per_feed": f"{feed_time/50*1000:.2f}ms"
            }
            
        except Exception as e:
            self.logger.error(f"Newsfeed performance test failed: {e}")
            performance_results["newsfeed"] = {"error": str(e)}
        
        return performance_results

    def generate_final_report(self) -> str:
        """Generate final comprehensive report."""
        report_lines = [
            "# Comprehensive System Test Report",
            f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            ""
        ]
        
        # Add summary statistics
        total_systems = len(self.systems)
        successful_systems = sum(1 for data in self.test_results.get("system_results", {}).values() 
                                if data.get("success", False))
        
        report_lines.extend([
            f"- **Total Systems**: {total_systems}",
            f"- **Successful Systems**: {successful_systems}",
            f"- **Success Rate**: {successful_systems/total_systems*100:.1f}%",
            f"- **Average Coverage**: {self.test_results.get('average_coverage', 0):.1f}%",
            f"- **Test Duration**: {self.test_results.get('total_duration', 0):.2f}s",
            "",
            "## Coverage Analysis",
            ""
        ])
        
        # Add coverage analysis
        avg_coverage = self.test_results.get("average_coverage", 0)
        if avg_coverage >= 95:
            report_lines.append("🎯 **Excellent Coverage**: All systems achieve 95%+ coverage")
        elif avg_coverage >= 90:
            report_lines.append("✅ **Good Coverage**: All systems achieve 90%+ coverage")
        elif avg_coverage >= 80:
            report_lines.append("⚠️ **Acceptable Coverage**: Systems achieve 80%+ coverage")
        else:
            report_lines.append("❌ **Poor Coverage**: Systems need improvement")
        
        report_lines.extend([
            "",
            "## Recommendations",
            ""
        ])
        
        # Add recommendations based on results
        if avg_coverage < 90:
            report_lines.append("- Increase test coverage for all systems")
            report_lines.append("- Add integration tests for critical paths")
            report_lines.append("- Implement end-to-end testing")
        
        if successful_systems < total_systems:
            report_lines.append("- Fix failing tests in systems")
            report_lines.append("- Review error handling and edge cases")
        
        report_lines.extend([
            "",
            "## Next Steps",
            "",
            "1. Review detailed coverage report",
            "2. Address any failing tests",
            "3. Implement missing test cases",
            "4. Set up continuous integration",
            "5. Monitor coverage in production",
            ""
        ])
        
        return "\n".join(report_lines)


def main():
    """Main entry point."""
    runner = TestRunner()
    
    # Run comprehensive tests
    results = runner.run_all_tests()
    
    # Generate coverage report
    coverage_report = runner.generate_coverage_report()
    
    # Check coverage threshold
    meets_threshold = runner.check_coverage_threshold(90.0)
    
    # Run performance tests
    performance_results = runner.run_performance_tests()
    
    # Generate final report
    final_report = runner.generate_final_report()
    
    # Save final report
    with open("/home/calelin/dev/canary/final_test_report.md", 'w') as f:
        f.write(final_report)
    
    # Print summary
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*60)
    print(f"Overall Success: {'✅' if results['overall_success'] else '❌'}")
    print(f"Average Coverage: {results['average_coverage']:.1f}%")
    print(f"Test Duration: {results['total_duration']:.2f}s")
    print(f"Coverage Threshold Met: {'✅' if meets_threshold else '❌'}")
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_success'] and meets_threshold else 1)


if __name__ == '__main__':
    main()
