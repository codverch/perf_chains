import symbolizer
import perf_data_pb2


def parse_perf_proto(perf_data_proto):
    with open(perf_data_proto, "rb") as proto_file:
        proto_string = proto_file.read()
        perf_data = perf_data_pb2.PerfDataProto().FromString(proto_string)
    return perf_data

def get_events_list(perf_proto):
    return list(filter(lambda event: event.sample_event is not None,
                       perf_proto.events))

PERF_DATA_LOCATION = "./perf.data"
PERF_PROTO_LOCATION = "./perf.proto"

print("Parsing Proto")
perf_proto = parse_perf_proto(PERF_PROTO_LOCATION)
perf_sample_events = get_events_list(perf_proto)

print("setting up symbolizer")
symbolize = symbolizer.Symbolizer(PERF_DATA_LOCATION)

print("starting code!")
top_n_function = {do_syscall_64, __GI___pthread_mutex_lock,  lru_maintainer_thread,  conn_cleanup, syscall_return_via_sysret,  ipt_do_table,  nf_hook_slow, ind_busiest_group,ipt_do_table,__fget, drive_machine, do_cache_free, ixgbe_poll, update_load_avg, __pthread_mutex_unlock_usercnt}
# Write your code here....
for event in perf_sample_events:
    sample = event.sample_event
    curr_sample_function = symbolize.get_symbols([sample.ip])[sample.ip]
    print("curr_sample_function name:")
    print(curr_sample_function)
    if (curr_sample_function in top_n_function):
        for branch in sample.branch_stack:
            branch_from_ip = branch.from_ip
            branch_to_ip = branch.to_ip
            branch_from_symbol = symbolize.get_symbols([branch_from_ip])[branch_from_ip]
            print("branch_from_symbol: ")
            print(branch_from_symbol)
            branch_to_symbol = symbolize.get_symbols([branch_to_ip])[branch_to_ip]
            print("branch_to_symbol: ")
            print(branch_to_symbol)