#!/bin/bash

echo "=========================================="
echo "Running Comprehensive Test Suite"
echo "=========================================="
echo ""

SYSTEMS_DIR="/home/calelin/dev/canary/systems"
VENV="/home/calelin/dev/canary/venv/bin/python"
FAILED_TESTS=()
PASSED_TESTS=()

# Function to run tests for a system
run_system_tests() {
    local system=$1
    local test_file=$2
    
    echo "=========================================="
    echo "Testing: $system"
    echo "=========================================="
    
    if [ -f "$SYSTEMS_DIR/$system/$test_file" ]; then
        cd "$SYSTEMS_DIR/$system"
        if $VENV -m pytest "$test_file" --cov="${system%_*}_*" --cov-report=term -q 2>&1 | tee /tmp/${system}_test_output.log; then
            PASSED_TESTS+=("$system")
            echo "✅ $system tests PASSED"
        else
            FAILED_TESTS+=("$system")
            echo "❌ $system tests FAILED"
        fi
        echo ""
    else
        echo "⚠️  No test file found: $test_file"
        echo ""
    fi
}

# Test ACE Causal Inference
run_system_tests "ace_causal_inference" "test_ace_*.py"

# Test AdTech Platform
run_system_tests "adtech_platform" "test_adtech_platform.py"

# Test Book Subscription
run_system_tests "book_subscription" "test_book_subscription.py"

# Test Lending Product (if it has tests)
run_system_tests "lending_product" "test_lending_product.py"

echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo ""
echo "✅ Passed Systems (${#PASSED_TESTS[@]}):"
for system in "${PASSED_TESTS[@]}"; do
    echo "  - $system"
done

echo ""
if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo "❌ Failed Systems (${#FAILED_TESTS[@]}):"
    for system in "${FAILED_TESTS[@]}"; do
        echo "  - $system"
    done
    exit 1
else
    echo "🎉 All systems passed!"
    exit 0
fi
