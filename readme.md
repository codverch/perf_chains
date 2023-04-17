
**make directory and add storage**
```
	sudo mkdir /mydata
	sudo /usr/local/etc/emulab/mkextrafs.pl /mydata
```

**setup protobuf compiler**
	install python 3.7
```
	sudo apt install python3.7
	sudo mv /usr/bin/python3 /usr/bin/python3-old
	sudo cp /usr/bin/python3.7 /usr/bin/python3
```
```
	sudo apt install protobuf-compiler
	pip3 install protobuf
```
**build pprof**
	download go
```
	wget https://go.dev/dl/go1.20.3.linux-amd64.tar.gz
	sudo tar -xzf go1.20.3.linux-amd64.tar.gz
	export PATH=$PATH:/mydata/go/bin
```
```
	go install github.com/google/pprof@latest
	export PATH=$PATH:$HOME/go/bin
```
**install bazel**
```
	sudo apt install apt-transport-https curl gnupg -y
	sudo curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor | sudo tee bazel-archive-keyring.gpg
	sudo mv bazel-archive-keyring.gpg /usr/share/keyrings
	echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
	sudo apt update && sudo apt install bazel
```
**build perf converter**
	dependencies: 
```
	sudo apt-get -y install g++ git libelf-dev libcap-dev
	sudo git clone https://github.com/google/perf_data_converter.git
	cd perf_data_converter
	sudo bazel build src:perf_to_profile
	cd src
	sudo bazel build quipper:perf_converter
	bazel-bin/src/quipper/perf_converter
	cd ..
	sudo cp bazel-bin/src/quipper/perf_converter /usr/local/bin/
```

**IF SPACE ISSUES**
```
	sudo systemctl stop docker
	sudo mv /var/lib/docker /mydata/docker
	sudo ln -s /mydata/docker/tmp /var/lib/docker/tmp
	sudo ln -s /mydata/docker/runtimes /var/lib/docker/runtimes
	sudo ln -s /mydata/docker/plugins /var/lib/docker/plugins
	sudo ln -s /mydata/docker/docker /var/lib/docker/docker
	sudo ln -s /mydata/docker/containers /var/lib/docker/containers
	sudo systemctl start docker
```
**How to run perf**  
	```sudo perf record -j any_call,any_ret -p <microservice_pid> -- sleep <time_in_seconds>```

**Setup:**  
	run perf
	generate the perf proto file 
		```sudo perf_converter -i perf.data -o perf.proto -O proto```
        
**How to use the tool:**  
	The tool gives you a list of all perf events. Each perf event has a sampled function (essentially the current function) and a branch stack (the last 16 functions that occurred before this function)
	If you're more interested in the format of the perf events, look at perf_data.proto.
	By default, it expects both `perf.data` and `perf_data.proto` to be present in the same directory as the tool itself .
	If you want to change this, modify the locations on lines 15 and 16 of the driver.
	From this, you can build on your own analyses.
	If you run into issues, with parsing the proto message, you may need to recompile the protos. You can do that with:
```
	protoc --python_out=. ./profile.proto
	protoc --python_out=. ./perf_data.proto	
```