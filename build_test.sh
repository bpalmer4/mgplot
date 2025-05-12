#!/bin/zsh
# make sure the version number is correct in both:
# (1) ~/mgplot/src/mgplot/__init__.py
# (2) ~/mgplot/pyproject.toml

cd ~/mgplot

if [ ! -d ./dist ]; then
    mkdir dist
fi
if [ -n "$(ls -A ./dist 2>/dev/null)" ]; then
  rm ./dist/*
fi

uv sync

uv build

uv pip install dist/mgplot*gz

~/mgplot/build_docs.sh

echo "And if everything is okay ..."
echo "uv publish --token MY_TOKEN_HERE"

