#!/bin/bash

# Comprehensive test runner for all systems with coverage validation
# This script runs all test suites and validates coverage thresholds

set -e  # Exit on error

VENV_PYTHON="/home/calelin/dev/canary/venv/bin/python"
COVERAGE_THRESHOLD_95=95
COVERAGE_THRESHOLD_90=90
COVERAGE_THRESHOLD_100=100

echo "=================================="
echo "Running Comprehensive Test Suite"
echo "=================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
FAILED_SYSTEMS=()

# Function to check coverage threshold
check_coverage() {
    local system_name=$1
    local coverage=$2
    local threshold=$3

    if (( $(echo "$coverage >= $threshold" | bc -l) )); then
        echo -e "${GREEN}✓ $system_name: $coverage% (threshold: $threshold%)${NC}"
        return 0
    else
        echo -e "${RED}✗ $system_name: $coverage% (threshold: $threshold%)${NC}"
        FAILED_SYSTEMS+=("$system_name")
        return 1
    fi
}

# ==========================================
# Python Systems Tests
# ==========================================

echo "========================================="
echo "Python Systems - Running Tests"
echo "========================================="
echo ""

# AdTech Platform
echo "--- AdTech Platform ---"
cd /home/calelin/dev/canary/systems/adtech_platform
$VENV_PYTHON -m pytest test_adtech.py -v --cov=adtech_service --cov-report=term | tee /tmp/adtech_coverage.txt
ADTECH_COVERAGE=$(grep "TOTAL" /tmp/adtech_coverage.txt | awk '{print $NF}' | sed 's/%//')
check_coverage "AdTech Platform" "$ADTECH_COVERAGE" "$COVERAGE_THRESHOLD_95"
echo ""

# Book Subscription
echo "--- Book Subscription ---"
cd /home/calelin/dev/canary/systems/book_subscription
$VENV_PYTHON -m pytest test_book_subscription.py -v --cov=book_subscription_service --cov-report=term | tee /tmp/book_coverage.txt
BOOK_COVERAGE=$(grep "TOTAL" /tmp/book_coverage.txt | awk '{print $NF}' | sed 's/%//')
check_coverage "Book Subscription" "$BOOK_COVERAGE" "$COVERAGE_THRESHOLD_95"
echo ""

# ACE Causal Inference
echo "--- ACE Causal Inference ---"
cd /home/calelin/dev/canary/systems/ace_causal_inference
$VENV_PYTHON -m pytest test_ace_causal_inference.py -v --cov=ace_causal_inference_service --cov-report=term | tee /tmp/ace_coverage.txt
ACE_COVERAGE=$(grep "TOTAL" /tmp/ace_coverage.txt | awk '{print $NF}' | sed 's/%//')
check_coverage "ACE Causal Inference" "$ACE_COVERAGE" "$COVERAGE_THRESHOLD_95"
echo ""

# Lending Product
echo "--- Lending Product ---"
cd /home/calelin/dev/canary/systems/lending_product
$VENV_PYTHON -m pytest test_lending_product.py -v --cov=lending_product_service --cov-report=term | tee /tmp/lending_coverage.txt
LENDING_COVERAGE=$(grep "TOTAL" /tmp/lending_coverage.txt | awk '{print $NF}' | sed 's/%//')
check_coverage "Lending Product" "$LENDING_COVERAGE" "$COVERAGE_THRESHOLD_90"
echo ""

# ==========================================
# Final Summary
# ==========================================

echo ""
echo "========================================="
echo "Test Suite Summary"
echo "========================================="
echo ""

if [ ${#FAILED_SYSTEMS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All systems passed coverage thresholds!${NC}"
    echo ""
    echo "Coverage Results:"
    echo "  - AdTech Platform: $ADTECH_COVERAGE% (>= 95%)"
    echo "  - Book Subscription: $BOOK_COVERAGE% (>= 95%)"
    echo "  - ACE Causal Inference: $ACE_COVERAGE% (>= 95%)"
    echo "  - Lending Product: $LENDING_COVERAGE% (>= 90%)"
    exit 0
else
    echo -e "${RED}✗ The following systems failed coverage thresholds:${NC}"
    for system in "${FAILED_SYSTEMS[@]}"; do
        echo "  - $system"
    done
    echo ""
    echo "Coverage Results:"
    echo "  - AdTech Platform: $ADTECH_COVERAGE% (target: >= 95%)"
    echo "  - Book Subscription: $BOOK_COVERAGE% (target: >= 95%)"
    echo "  - ACE Causal Inference: $ACE_COVERAGE% (target: >= 95%)"
    echo "  - Lending Product: $LENDING_COVERAGE% (target: >= 90%)"
    exit 1
fi
