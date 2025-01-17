#!/bin/bash

# Define the repository URL and clone directory
REPO_URL="https://github.com/tunaspaghett/sonarr-debrid"
REPO_NAME="sonarr-debrid"
CLONE_DIR="$REPO_NAME"

# Function to update on Linux/Mac
function update_linux {
  echo "Pulling the latest changes from the repository..."
  git pull origin main > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo "Repository updated successfully!"
    check_for_new_release
  else
    echo "Error occurred while pulling changes."
  fi
}

# Function to check for new releases
function check_for_new_release {
  echo "Checking for new releases..."
  LATEST_RELEASE=$(curl -s "https://api.github.com/repos/tunaspaghett/sonarr-debrid/releases/latest" | jq -r '.tag_name')
  CURRENT_TAG=$(git describe --tags)
  
  if [ "$LATEST_RELEASE" != "$CURRENT_TAG" ]; then
    echo "A new release is available: $LATEST_RELEASE"
    echo "Updating to the latest release..."
    git fetch --tags > /dev/null 2>&1
    git checkout "tags/$LATEST_RELEASE" > /dev/null 2>&1
    echo "Updated to release $LATEST_RELEASE"
  else
    echo "Already on the latest release: $CURRENT_TAG"
  fi
}

# Check the operating system and call the appropriate function
update_linux
