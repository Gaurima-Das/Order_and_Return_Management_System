#!/bin/bash

echo "Running Unit Tests with Coverage..."
echo ""

pytest Test_Cases/ --cov=app --cov-report=html:Test_Cases/coverage_html --cov-report=term-missing --cov-report=xml:Test_Cases/coverage.xml -v

echo ""
echo "Coverage report generated at: Test_Cases/coverage_html/index.html"
echo ""

