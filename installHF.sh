## If unable to pip install sentence transformers, run this commands
## Assumption: project is in a venv with pip

mkdir -p $HOME/pip_tmp $HOME/pip_downloads

# Export for both pip and Python's tempfile module
export TMPDIR=$HOME/pip_tmp
export TEMP=$TMPDIR
export TMP=$TMPDIR

# Optional: remove stale temp files
rm -rf $TMPDIR/*

# Run pip download with full redirection
python -m pip download sentence-transformers -d $HOME/pip_downloads --no-cache-dir -v

# If the download works then do this
python -m pip install --no-index --find-links=$HOME/pip_downloads sentence-transformers


