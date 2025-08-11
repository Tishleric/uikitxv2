@echo off
echo =====================================================
echo Price Updater Optimization Testing
echo =====================================================
echo.
echo This will test the optimized implementation.
echo NO PRODUCTION FILES WILL BE MODIFIED.
echo.

cd /d Z:\uikitxv2

echo Running optimization tests from project root...
echo Current directory: %CD%
echo.

python tests\diagnostics\run_optimization_tests.py

echo.
pause