#!/bin/bash

set -e   # Fails on any error in the following loop
export PYTHONPATH=$PWD/docs/_pydoc # Make the renderers available to pydoc
cd docs/_pydoc
rm -rf temp && mkdir temp
cd temp
for file in ../config/* ; do
    echo "Converting $file..."
    pydoc-markdown "$file"
done
