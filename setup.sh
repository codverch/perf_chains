#!/bin/bash

# <---------- Check and Install Python 3.5+ ---------->

if ! command -v python3 &>/dev/null; then
    # Install Python 3 if not present
    sudo apt install python3 -y
fi

# <---------- Install protobuf-compiler and protobuf Python package ---------->

# For efficient data serialization and seamless communication
sudo apt install protobuf-compiler -y
pip3 install protobuf

# <---------- Check if protobuf-compiler is installed ---------->

# protoc --version

# <---------- Download and Install Go ---------->

# Go is a programming language used for various development purposes
if ! command -v go &>/dev/null; then
    wget https://go.dev/dl/go1.20.3.linux-amd64.tar.gz
    sudo tar -C /usr/local -xzf go1.20.3.linux-amd64.tar.gz
    export PATH=$PATH:/usr/local/go/bin
    source ~/.bashrc
    rm go1.20.3.linux-amd64.tar.gz

    # <---------- Check if Go is installed ---------->

    # go version
fi

# Install pprof using go get
go install github.com/google/pprof@latest
export PATH=$PATH:$HOME/go/bin

# Install Bazel
if ! command -v bazel &>/dev/null; then
    sudo apt update && sudo apt install -y curl gnupg
    curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor > bazel.gpg
    sudo mv bazel.gpg /usr/share/keyrings/
    echo "deb [signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list > /dev/null
    sudo apt update && sudo apt install -y bazel
fi

# <---------- Check if Bazel is installed ---------->
# bazel --version

# <---------- Install perf_data_converter ---------->

sudo apt-get -y install g++ git libelf-dev libcap-dev
git clone https://github.com/google/perf_data_converter.git
cd perf_data_converter

# Make the .bazelrc file writable by the current user
chmod +x .bazelrc

# Change ownership of .bazelrc to the current user
sudo chown $USER .bazelrc

# Build perf_to_profile using Bazel
sudo bazel build src:perf_to_profile

# Check if the build fails due to an unrecognized option
if [ $? -ne 0 ]; then
    echo "Build failed. Removing the problematic line from .bazelrc."

    # Remove the line containing --noenable_bzlmod
    sed -i '/--noenable_bzlmod/d' .bazelrc
    
    # Retry the build
    sudo bazel build src:perf_to_profile
fi

cd src
sudo bazel build quipper:perf_converter
cd ..
sudo cp bazel-bin/src/quipper/perf_converter /usr/local/bin/
sudo cp bazel-bin/src/perf_to_profile /usr/local/bin/

echo "Setup complete!"
