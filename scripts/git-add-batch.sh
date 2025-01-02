#!/bin/bash

BATCH_SIZE=200

for FILENAME in $(git ls-files --others --exclude-standard | head -n ${BATCH_SIZE} | sed -E "s/\"/\'/g");
do
    # git add --dry-run --ignore-errors ${FILENAME};
    git add --ignore-errors ${FILENAME};
done

git commit -m "Batch of files"
git push -u origin main
