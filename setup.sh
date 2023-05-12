#Proto stuff
sudo apt install protobuf-compiler -y
pip3 install protobuf

#pprof stuff
wget https://go.dev/dl/go1.20.3.linux-amd64.tar.gz
sudo tar -xzf go1.20.3.linux-amd64.tar.gz
export PATH=$PATH:/mydata/go/bin
go install github.com/google/pprof@latest
export PATH=$PATH:$HOME/go/bin
sudo apt install apt-transport-https curl gnupg -y
sudo curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor | sudo tee bazel-archive-keyring.gpg
sudo mv bazel-archive-keyring.gpg /usr/share/keyrings
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
sudo apt update && sudo apt install bazel
sudo apt install apt-transport-https curl gnupg -y
sudo curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor | sudo tee bazel-archive-keyring.gpg
sudo mv bazel-archive-keyring.gpg /usr/share/keyrings
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
sudo apt update && sudo apt install bazel -y
sudo apt-get -y install g++ git libelf-dev libcap-dev
sudo git clone https://github.com/google/perf_data_converter.git
cd perf_data_converter
sudo bazel build src:perf_to_profile
cd src
sudo bazel build quipper:perf_converter
# bazel-bin/src/quipper/perf_converter
cd ..
sudo cp bazel-bin/src/quipper/perf_converter /usr/local/bin/
sudo cp bazel-bin/src/perf_to_profile /usr/local/bin/