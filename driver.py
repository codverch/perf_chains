import symbolizer
import perf_data_pb2
import collections


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
top_n_functions = {"__pthread_mutex_unlock_usercnt", 
"__GI___pthread_mutex_lock", 
"lru_maintainer_thread",
"bipbuf_peek_all",
"lru_pull_tail",
"clock_nanosleep",
"nanosleep",
"item_trylock",
"do_item_remove",
"item_is_flushed"}
# Write your code here....

# what should the map contain?
# the name of the top functions, 
# 
top_functions_chains={} 


for event in perf_sample_events:
    sample = event.sample_event
    curr_sample_function = symbolize.get_symbols([sample.ip])[sample.ip]
    if (curr_sample_function in top_n_functions): ## only get the top 10 functions
        if curr_sample_function not in top_functions_chains:
            top_functions_chains[curr_sample_function] = {} #this should be a map, which contains the function name,
            # the value should be a map, where a+b:89 is the (key, value) pair
        curr_chain = []
        #
        for branch in sample.branch_stack:
            branch_from_ip = branch.from_ip
            branch_to_ip = branch.to_ip
            branch_from_symbol = symbolize.get_symbols([branch_from_ip])[branch_from_ip]
            # branch_to_symbol = symbolize.get_symbols(branch_to_ip)[branch_to_ip]
            curr_chain.append(branch_from_symbol)
        ## each time we get the current chain.
        # then we just generate the pair of the functions.
        function_pair_map = top_functions_chains[curr_sample_function]
        for i in range(len(curr_chain)-1):
            key = curr_chain[i] + curr_chain[i+1]
            if key not in function_pair_map:
                function_pair_map[key] = 0
            function_pair_map[key] = function_pair_map[key] + 1
        
        
print(top_functions_chains)      


