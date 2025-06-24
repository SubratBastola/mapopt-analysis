# Deployment Guide for MAPopt Analysis Tool



## 📁 Project Structure Overview

The monolithic code has been reorganized into a professional Python package structure:

```
mapopt_analysis/
├── README.md                     # Main documentation
├── requirements.txt              # Python dependencies
├── setup.py                     # Package installation script
├── LICENSE                      # MIT license
├── .gitignore                   # Git ignore rules
├── DEPLOYMENT_GUIDE.md          # This file
├── mapopt_analysis/             # Main package directory
│   ├── __init__.py             # Package initialization
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Configuration constants
│   ├── gui/                    # GUI components
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main GUI window
│   │   └── dialogs.py          # Dialog windows
│   ├── core/                   # Core analysis algorithms
│   │   ├── __init__.py
│   │   ├── data_loader.py      # Data loading and preprocessing
│   │   ├── signal_processing.py # Signal processing utilities
│   │   ├── mapopt_calculator.py # MAPopt calculation engine
│   │   └── burden_metrics.py   # Burden calculation
│   ├── visualization/          # Plotting and visualization
│   │   ├── __init__.py
│   │   └── plots.py            # Plot management
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       ├── file_io.py          # File I/O operations
│       └── logger.py           # Logging utilities
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_data_loader.py     # Data loader tests
│   ├── test_signal_processing.py # Signal processing tests
│   └── test_mapopt_calculator.py # MAPopt calculation tests
└── examples/                   # Usage examples
    ├── sample_data.csv         # Sample data file
    └── basic_usage.py          # Basic usage example
```

## 🚀 GitHub Deployment Steps

### 1. Create GitHub Repository

```bash
# Create a new repository on GitHub first, then:
git clone https://github.com/yourusername/mapopt-analysis.git
cd mapopt-analysis
```

### 2. Copy Modular Code Structure

Copy all the files from the artifacts above into your repository directory following the structure shown.

### 3. Initialize Git Repository

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: Modularized MAPopt Analysis Tool

- Converted monolithic script to modular Python package
- Added comprehensive test suite
- Implemented CLI and GUI interfaces
- Added documentation and examples
- Set up proper packaging structure"

# Push to GitHub
git remote add origin https://github.com/yourusername/mapopt-analysis.git
git branch -M main
git push -u origin main
```

## 🔧 Development Setup

### 1. Clone and Setup Environment

```bash
git clone https://github.com/yourusername/mapopt-analysis.git
cd mapopt-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mapopt_analysis

# Run specific test file
pytest tests/test_data_loader.py -v
```

### 3. Code Quality Checks

```bash
# Format code
black mapopt_analysis/

# Lint code
flake8 mapopt_analysis/

# Type checking
mypy mapopt_analysis/
```

## 📦 Package Installation

### For Users

```bash
# Install from GitHub
pip install git+https://github.com/yourusername/mapopt-analysis.git

# Or clone and install locally
git clone https://github.com/yourusername/mapopt-analysis.git
cd mapopt-analysis
pip install .
```

### For Developers

```bash
git clone https://github.com/yourusername/mapopt-analysis.git
cd mapopt-analysis
pip install -e ".[dev]"
```

## 🎯 Usage Examples

### Command Line Interface

```bash
# Show help
mapopt-analysis --help

# Run GUI
mapopt-analysis

# Analyze a file
mapopt-analysis --file data.csv --output results/

# With specific time range
mapopt-analysis --file data.csv --output results/ --start 2.0 --end 20.0
```

### Python API

```python
from mapopt_analysis import DataLoader, MAPoptCalculator, BurdenCalculator

# Load and analyze data
loader = DataLoader()
data = loader.load_data("your_data.csv")

calculator = MAPoptCalculator()
time_vector, mapopt_series, fits_data = calculator.calculate_mapopt_series(data)

burden_calc = BurdenCalculator()
burden_calc.calculate_deviation_and_burden(data, time_vector, mapopt_series)
results = burden_calc.calculate_burden_metrics(time_vector, 0, 24)

print(f"Time Burden: {results['time_burden']:.1f}%")
```

## 🧪 Testing Strategy

### Test Categories

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **GUI Tests**: Test user interface components

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_mapopt_calculator.py

# With coverage report
pytest --cov=mapopt_analysis --cov-report=html

# Verbose output
pytest -v -s
```

## 📝 Documentation

### Adding Documentation

1. **Docstrings**: All functions and classes should have comprehensive docstrings
2. **Type Hints**: Use type hints for better code clarity
3. **Examples**: Include usage examples in docstrings
4. **README**: Keep README.md updated with new features

### Building Documentation (Optional)

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Initialize documentation
sphinx-quickstart docs/

# Build documentation
cd docs/
make html
```

## 🔄 Continuous Integration

### GitHub Actions Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=mapopt_analysis
```

## 📋 Release Process

### Version Management

1. Update version in `mapopt_analysis/__init__.py`
2. Update version in `setup.py`
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`

### Creating Releases

1. Go to GitHub repository
2. Click "Releases" → "Create a new release"
3. Choose tag version
4. Add release notes
5. Attach any binary distributions

## 🤝 Contributing Guidelines

### Development Workflow

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Run tests: `pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push branch: `git push origin feature/amazing-feature`
7. Create Pull Request

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive docstrings
- Maintain test coverage above 80%
- Update documentation for new features

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure package is installed in development mode
2. **GUI Issues**: Verify tkinter is available
3. **Performance**: Check parallel processing settings
4. **Dependencies**: Update requirements.txt for new dependencies

### Debug Mode

```bash
# Enable verbose logging
mapopt-analysis --file data.csv --verbose

# Python debugging
python -c "
import mapopt_analysis
print(mapopt_analysis.__version__)
print(mapopt_analysis.__file__)
"
```

## 📈 Monitoring and Maintenance

### Regular Tasks

- Update dependencies regularly
- Run full test suite before releases
- Monitor GitHub issues and discussions
- Update documentation as needed
- Review and merge pull requests

### Performance Monitoring

- Profile code for performance bottlenecks
- Monitor memory usage with large datasets
- Optimize parallel processing parameters
- Benchmark against previous versions

---
