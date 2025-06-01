#!/bin/zsh
# make sure the version number is correct:
# ~/mgplot/pyproject.toml

# --- cd mgplot home and activate environment
cd ~/mgplot
deactivate
source .venv/bin/activate

# --- clean out the dist folder
if [ ! -d ./dist ]; then
    mkdir dist
fi
if [ -n "$(ls -A ./dist 2>/dev/null)" ]; then
  rm ./dist/*
fi

# --- remove old arrangement, sync and build
rm uv.lock
uv sync
uv build

# --- install new mgplot locally
uv pip install dist/mgplot*gz

# --- build documentation
~/mgplot/build-docs.sh

# --- if everything is good publish and git
echo "\nAnd if everything is okay ..."
echo "uv publish --token MY_TOKEN_HERE"
echo "And don't forget to upload to github"
