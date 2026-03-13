# pytest.ini - Pytest configuration for Supply Chain Intelligence

[pytest]
# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Paths
testpaths = tests

# Coverage
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=supply_chain_intelligence
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
    --cov-fail-under=70
    --maxfail=5

# Markers
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    supply_chain: marks supply chain specific tests
    performance: marks performance tests

# Warnings
filterwarnings =
    error
    ignore::UserWarning
    ignore::DeprecationWarning

# Minimum Python
minversion = 3.8

# Logging
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

# Timeout
timeout = 300
