#!/bin/zsh
# make sure the version number is correct in both:
# (1) ~/mgplot/src/mgplot/__init__.py
# (2) ~/mgplot/pyproject.toml

cd ~/mgplot

# --- remove old arrangement
rm -rf .venv
rm uv.lock

# --- clean out the dist folder
if [ ! -d ./dist ]; then
    mkdir dist
fi
if [ -n "$(ls -A ./dist 2>/dev/null)" ]; then
  rm ./dist/*
fi

# --- sync and build
uv sync
uv build

# --- install locally
uv pip install dist/mgplot*gz

# --- build documentation
~/mgplot/build-docs.sh

# --- if everything is good publish and git
echo "\nAnd if everything is okay ..."
echo "uv publish --token MY_TOKEN_HERE"
echo "And don't forget to upload to github"
