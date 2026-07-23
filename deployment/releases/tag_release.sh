#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <tag_name>"
    exit 1
fi

TAG_NAME="$1"

echo "Tagging release $TAG_NAME..."
git tag -a "$TAG_NAME" -m "Release $TAG_NAME"
git push origin "$TAG_NAME"

echo "Release tagged and pushed."
