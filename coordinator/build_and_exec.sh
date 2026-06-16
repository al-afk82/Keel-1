#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define colors for clean terminal output status updates
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

BUILD_DIR="build"
EXECUTABLE="hackathon_drift_coordinator"

echo -e "${BLUE}[1/4] Cleaning previous build artifacts...${NC}"
echo -e "${BLUE}[1/4] Checking build artifacts...${NC}"
if [ ! -d "$BUILD_DIR" ]; then
    mkdir "$BUILD_DIR"
fi
echo -e "${BLUE}[2/4] Generating build files via CMake (Release Mode)...${NC}"
cd "$BUILD_DIR"
cmake -DCMAKE_BUILD_TYPE=Release ..

echo -e "${BLUE}[3/4] Compiling source tree binaries...${NC}"
# Use all available CPU cores automatically
make -j$(nproc)

echo -e "${GREEN}[4/4] Compilation successful! Launching service target...${NC}"
echo "--------------------------------------------------------"

# Check if the binary exists before executing
if [ -f "./$EXECUTABLE" ]; then
    ./"$EXECUTABLE"
else
    echo -e "${RED}Error: Executable target '$EXECUTABLE' not found in build directory.${NC}"
    exit 1
fi
