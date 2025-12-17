#!/usr/bin/env python3
"""
Main gRPC Test Runner
Runs the complete gRPC testing pipeline:
1. Generate cURL commands
2. Execute test sets
3. Check and analyze results
"""

import sys
import argparse
import time
from pathlib import Path
from grpc_generator import GrpcGenerator
from grpc_executor import GrpcExecutor
from grpc_checker import GrpcChecker


def main():
    parser = argparse.ArgumentParser(description="Run gRPC tests for payment connectors")
    parser.add_argument("--env", default=".env.grpc", help="Environment file (default: .env.grpc)")
    parser.add_argument("--generate-only", action="store_true", help="Only generate cURL commands, don't execute")
    parser.add_argument("--check-only", action="store_true", help="Analyze existing results without running tests")
    parser.add_argument("--test-set", help="Run specific test set by name")

    args = parser.parse_args()

    try:
        if args.check_only:
            # Analyze existing results
            checker = GrpcChecker()
            results_dir = Path("grpc_test_results")

            if not results_dir.exists():
                print("No grpc_test_results directory found")
                sys.exit(1)

            results_files = list(results_dir.glob("test_results_*.json"))
            if not results_files:
                print("No test result files found")
                sys.exit(1)

            latest_file = max(results_files, key=lambda p: p.stat().st_mtime)
            print(f"\nAnalyzing results from: {latest_file}")

            analysis = checker.check_test_results(latest_file)
            report_file = results_dir / f"analysis_report_{latest_file.stem.replace('test_results_', '')}.md"

            checker.generate_report(analysis, report_file)
            return

        if args.generate_only:
            # Generate cURL commands only
            generator = GrpcGenerator(args.env)

            print(f"\n=== Generating gRPC Commands ===")
            print(f"Connector: {generator.connector_name}")
            print(f"Auth Type: {generator.auth_type}")
            print(f"Server: {generator.server_url}")

            operations = ["auth", "capture", "void", "refund", "sync"]
            for op in operations:
                try:
                    curl_cmd = generator.generate_grpc_curl(
                        op,
                        f"demo_{op}_{int(time.time())}",
                        transaction_id="txn_12345" if op != "auth" else None,
                        capture_method="MANUAL"
                    )
                    print(f"\n{op.upper()}:")
                    print(curl_cmd)
                except Exception as e:
                    print(f"Error generating {op}: {e}")

            generator.save_configuration()
            return

        # Run full test pipeline
        print(f"\n{'='*60}")
        print("gRPC Test Pipeline")
        print(f"Environment: {args.env}")
        print(f"{'='*60}")

        # Step 1: Generate and save configuration
        print("\nStep 1: Initializing...")
        generator = GrpcGenerator(args.env)
        generator.save_configuration()
        print(f"✓ Connector: {generator.connector_name}")
        print(f"✓ Auth Type: {generator.auth_type}")
        print(f"✓ Server: {generator.server_url}")

        # Step 2: Execute tests
        print("\nStep 2: Executing Tests...")
        executor = GrpcExecutor(args.env)

        # Filter test set if specified
        if args.test_set:
            test_sets = executor.test_sets
            filtered_sets = [ts for ts in test_sets if ts["name"].lower() == args.test_set.lower()]
            if not filtered_sets:
                print(f"Error: Test set '{args.test_set}' not found")
                sys.exit(1)
            executor.test_sets = filtered_sets
            print(f"Running only: {args.test_set}")

        results = executor.execute_all_tests()

        # Step 3: Analyze results
        print("\nStep 3: Analyzing Results...")
        checker = GrpcChecker()

        if "results_file" in results and results["results_file"]:
            results_file = Path(results["results_file"])
        else:
            # Find the latest results file
            results_dir = Path("grpc_test_results")
            if results_dir.exists():
                results_files = list(results_dir.glob("test_results_*.json"))
                if results_files:
                    results_file = max(results_files, key=lambda p: p.stat().st_mtime)
                else:
                    print("No results file found to analyze")
                    return
            else:
                print("No results directory found")
                return

        if results_file.exists():
            analysis = checker.check_test_results(results_file)

            # Print recommendations
            print("\nRecommendations:")
            for rec in analysis["recommendations"]:
                print(f"  {rec}")

            # Generate report
            report_file = results_file.parent / f"analysis_report_{results_file.stem.replace('test_results_', '')}.md"
            checker.generate_report(analysis, report_file)

        # Final status
        if results["summary"]["passed_sets"] == results["summary"]["total_sets"]:
            print(f"\n✅ All tests passed!")
            sys.exit(0)
        else:
            print(f"\n❌ Some tests failed")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()