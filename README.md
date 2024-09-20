# code-review-comment-classification

Code Review Comment Classification


## Repository structure

- `api` - utilities for interaction with the Gerrit API
- `data` - domain classes of the problem
- `features` - feature extraction (FE) utilities
- `labels` - the dataset labeling application
- `simple` - one of the final models, using only classical machine learning (ML) techniques
- `solution` - one of the final models, achieving the best results


## Requirements
- Python 3.10.12
- Libraries that are needed to run the modules, found in the requirements.txt files in each module

To install all needed libraries simply run commands below
```
python install -r features/requirements.txt
python install -r labels/requirements.txt
python install -r simple/requirements.txt
python install -r solution/requirements.txt
```

## Running modules
```
# Run annotation tool (annotate new dataset entries)
python -m labels

# Generate dataset.xlsx from annotation data
python -m features

# Run the simple model (requires dataset.xlsx)
python -m simple
# Optimize the hyperparameters
python -m simple.hyperopt

# Train complex model (requires dataset.xlsx)
python -m solution
# Check training arguments
python -m solution -h
```

### Additional information
- Annotation tool - [labels/README.md](/labels/README.md)
- Description of metrics - [features/README.md](/features/README.md)