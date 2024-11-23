#!/bin/bash

# Ensure the WORKDIR is provided
WORKDIR=$1

# Load build.json
BUILD_JSON="$WORKDIR/data/builds.json"

# Parse the JSON and execute the commands
jq -c '.toBuild[]' $BUILD_JSON | while IFS= read -r item; do
  CMD=$(echo "$item" | jq -r '.cmd')
  PATH=$(echo "$item" | jq -r '.path' | sed "s|{{workdir}}|$WORKDIR|")

  echo "Executing: cd $PATH && $CMD"

  # Execute the build command
  cd $PATH && $CMD
done
