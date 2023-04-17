import subprocess
import tempfile
import gzip
import profile_pb2

pprof_location = "/users/mrancic/go/bin/pprof"

def get_pprof_proto(
    perf_data_file,
    pprof_extra_argv=[]
):
    with tempfile.TemporaryDirectory() as tmp_dir:
        pprof_command = [pprof_location,
                        "-proto",
                        "-output",
                        f"{tmp_dir}/pprof.pb.gz",
                        perf_data_file
                        ] + pprof_extra_argv
        print("generating profile")
        pprof_res = subprocess.run(pprof_command, capture_output=True)
        print(pprof_res)
        if pprof_res.returncode != 0:
            print("Error generating pprof output")
            print(pprof_res.stderr)
            return None
        with open(f"{tmp_dir}/pprof.pb.gz", "rb") as zipped_file:
            unzipped = gzip.GzipFile(fileobj=zipped_file).read()
            return profile_pb2.Profile().FromString(unzipped)

get_pprof_proto("../perf.data")

