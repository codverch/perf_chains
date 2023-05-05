import symbolizer
import perf_data_pb2
import collections
import seaborn as sns
import matplotlib.pyplot as plt
import functools
import cProfile
import pickle

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

uncat_file = "./uncategorized"

tax_categories = [
    "application_logic",
    "c_libraries",
    "compress",
    "hash",
    "kernel",
    "mem",
    "miscellaneous",
    "sync",
    "rpc",
    "serialization"
]


file_contents = {}

for tax in tax_categories:
    with open(f"bucketization/{tax}_keywords", "r") as f:
        file_contents[tax] = f.readlines()

memo = {}

def bucketize(function_name):
    if function_name in memo:
        return memo[function_name]
    for tax in tax_categories:
        lines = file_contents[tax]
        for func in lines:
            func = func.split("#")[0].strip()
            if func in function_name:
                memo[function_name] = tax
                return tax
    with open(uncat_file, "a") as uncat:
        uncat.write(function_name + "\n")
    memo[function_name] = "application_logic"
    return "application_logic"

# 
top_functions_chains={} 


def plot_chain_cdf(perf_sample_events):
    chain_cycles = []
    chain_total_cycles = 0
    for event in perf_sample_events:
        sample = event.sample_event
        curr_chain_cycles = 0
        for branch in sample.branch_stack:
            curr_chain_cycles += branch.cycles
        chain_cycles.append(curr_chain_cycles)
        chain_total_cycles += curr_chain_cycles
    
    chain_percents = [(cycles/chain_total_cycles)*100 for cycles in chain_cycles]
    
    chain_percents.sort(reverse=True)

    cumulative = []
    for percent in chain_percents:
        if len(cumulative) == 0:
            cumulative.append(percent)
        else:
            cumulative.append(cumulative[-1]+percent)
    
    xs = [i/len(cumulative)*100 for i in range(len(cumulative))]
    ax = sns.lineplot(y=cumulative, x=xs)

    plt.savefig("results/chain_cdf.png", bbox_inches="tight")
    plt.cla()
    plt.clf()

def plot_tax_sharing(perf_sample_events, ip_to_func_name):
    xs = tax_categories
    ys = [0 for _ in tax_categories]

    for (i, event) in enumerate(perf_sample_events):
        if i%100 == 0:
            print(f"{i}/{len(perf_sample_events)}")
        sample = event.sample_event
        taxes_found = []
        for branch in sample.branch_stack:
            ip = branch.from_ip
            # func = symbolize.get_symbols(ip)[ip]
            func = ip_to_func_name[ip]
            if func is None or func == "":
                cat = "kernel"
            else:
                cat = bucketize(func)
            if cat not in taxes_found:
                ys[xs.index(cat)] += 1
                taxes_found.append(cat)
    ys = [y/len(perf_sample_events)*100 for y in ys]
    ax = sns.barplot(x=xs, y=ys)

    plt.savefig("results/tax_sharing.png", bbox_inches="tight")

def build_ip_mapping(perf_sample_events):
    ip_to_func_name = {}
    for event in perf_sample_events:
        sample_event = event.sample_event
        for branch in sample_event.branch_stack:
            if branch.from_ip in ip_to_func_name:
                continue
            ip_to_func_name[branch.from_ip] = symbolize.get_symbols(branch.from_ip)[branch.from_ip]
    return ip_to_func_name


with open("ip_map.pickle", "rb") as f:
    # ip_to_func_name = build_ip_mapping(perf_sample_events)
    # pickle.dump(ip_to_func_name, f)
    ip_to_func_name = pickle.load(f)

def work():
    print("Plotting chain cdf")
    plot_chain_cdf(perf_sample_events)
    print("plotting tax sharing")
    plot_tax_sharing(perf_sample_events, ip_to_func_name)

work()

# for event in perf_sample_events:
#     sample = event.sample_event
#     curr_sample_function = symbolize.get_symbols([sample.ip])[sample.ip]
#     # print(curr_sample_function)
#     if curr_sample_function is not None and curr_sample_function != "":
#         cat = bucketize(curr_sample_function)
#     else:
#         cat = "kernel"
#     if cat not in ["UNKNOWN", "kernel"]:
#         print((cat, curr_sample_function))
#     # print(cat)
#     # if (curr_sample_function in top_n_functions): ## only get the top 10 functions
#     #     if curr_sample_function not in top_functions_chains:
#     #         top_functions_chains[curr_sample_function] = {} #this should be a map, which contains the function name,
#     #         # the value should be a map, where a+b:89 is the (key, value) pair
#     #     curr_chain = []
#     #     #
#     #     for branch in sample.branch_stack:
#     #         branch_from_ip = branch.from_ip
#     #         branch_to_ip = branch.to_ip
#     #         branch_from_symbol = symbolize.get_symbols([branch_from_ip])[branch_from_ip]
#     #         # branch_to_symbol = symbolize.get_symbols(branch_to_ip)[branch_to_ip]
#     #         curr_chain.append(branch_from_symbol)
#     #     ## each time we get the current chain.
#     #     # then we just generate the pair of the functions.
#     #     function_pair_map = top_functions_chains[curr_sample_function]
#     #     for i in range(len(curr_chain)-1):
#     #         key = curr_chain[i] + curr_chain[i+1]
#     #         if key not in function_pair_map:
#     #             function_pair_map[key] = 0
#     #         function_pair_map[key] = function_pair_map[key] + 1
        
        
# # print(top_functions_chains)      


