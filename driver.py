import symbolizer
import perf_data_pb2
import collections
import seaborn as sns
import matplotlib.pyplot as plt
import functools
import cProfile
import pickle
import numpy as np

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
    "c_libraries",
    "compress",
    # "hash",
    "encryption",
    # "kernel",
    "mem",
    # "miscellaneous",
    "sync",
    "rpc",
    "serialization",
    "kernel",
    "application_logic",

]

plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

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
    
    chain_percents = [(cycles/chain_total_cycles)*100 if chain_total_cycles != 0 else 0 for cycles in chain_cycles]

    
    chain_percents.sort(reverse=True)

    cumulative = []
    for percent in chain_percents:
        if len(cumulative) == 0:
            cumulative.append(percent)
        else:
            cumulative.append(cumulative[-1]+percent)
    
    xs = [i/len(cumulative)*100 for i in range(len(cumulative))]
    ax = sns.lineplot(y=cumulative, x=xs)
    plt.xticks(size=14)
    plt.xlabel("Percent of Chains", fontsize=16)
    plt.ylabel("Percent of Cycles", fontsize=16)

    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    plt.savefig("results/chain_cdf.png", bbox_inches="tight")
    plt.cla()
    plt.clf()

def plot_tax_sharing(perf_sample_events, ip_to_func_name):
    tax_categories = [
    "c_libraries",
    "compress",
    # "hash",
    "encryption",
    # "kernel",
    "mem",
    # "miscellaneous",
    "sync",
    "rpc",
    "serialization",
    "application_logic",
    "kernel"
]
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
            func = ip_to_func_name.get(ip, None)
            if func is None or func == "":
                cat = "application_logic"
            else:
                cat = bucketize(func)
            # print(f"{i}\t{cat}")
            if cat not in taxes_found:
                ys[xs.index(cat)] += 1
                taxes_found.append(cat)
    print("Tax Sharing Raw Data")
    print(xs)
    print(ys)
    ys = [y/len(perf_sample_events)*100 for y in ys]
    xs = sorted(xs, key=(lambda x: ys[xs.index(x)]), reverse=True)
    ys.sort(reverse=True)
    ax = sns.barplot(x=xs, y=ys, errorbar=None, ci=None)

    plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
    plt.xlabel("Tax Categories", fontsize=16)
    plt.ylabel("Percent of Chains", fontsize=16)

    plt.savefig("results/tax_sharing.png", bbox_inches="tight")

    plt.cla()
    plt.clf()

def plot_sample_based_attribution(perf_sample_events, ip_to_func_name):
    tax_categories = [
        "c_libraries",
        "compress",
        "encryption",
        "mem",
        "sync",
        "rpc",
        "serialization",
        "application_logic",
        "kernel"
    ]

    store_cpu_cycles_by_tax = {tax: 0 for tax in tax_categories}

    for(i, event) in enumerate(perf_sample_events):
        sample = event.sample_event 
        taxes_found = []
        # Iterate through each sample and only look at the first branch
        if sample.branch_stack:
            branch = sample.branch_stack[0] # Sample only the top function
            instruction_pointer = branch.from_ip
            function_name = ip_to_func_name.get(instruction_pointer, None)
            if function_name == None or function_name == "":
                category = "application_logic"

            else:
                category = bucketize(function_name)
                store_cpu_cycles_by_tax[category] += branch.cycles

    total_cpu_cycles = sum(store_cpu_cycles_by_tax.values())

    # Percentage of CPU cycles
    percentage_cpu_cycles = {tax: (store_cpu_cycles_by_tax[tax] / total_cpu_cycles) * 100 for tax in store_cpu_cycles_by_tax.keys()}

    # Calculate percentage of CPU cycles for application logic
    application_logic_percentage = (store_cpu_cycles_by_tax['application_logic'] / total_cpu_cycles) * 100

    # Calculate percentage of CPU cycles for other tax categories
    other_tax_categories_percentage = 100 - application_logic_percentage

    # Plot the results
    plt.figure(figsize=(8, 6))
    plt.bar('application_logic', application_logic_percentage, color='black', label='Application Logic')
    plt.bar('application_logic', other_tax_categories_percentage, bottom=application_logic_percentage, color='maroon', label='Other Tax Categories')
    plt.xlabel('Category')
    plt.ylabel('Percentage of CPU Cycles (%)')
    plt.title('Percentage of CPU Cycles by Category')
    plt.legend()
    plt.xticks([])
    plt.ylim(0, 100)
    plt.text('application_logic', application_logic_percentage + 1, f"{application_logic_percentage:.2f}%", ha='center')
    plt.text('application_logic', 50, f"{other_tax_categories_percentage:.2f}%", ha='center')

    plt.savefig("results/sample_based_attribution_combined.png", bbox_inches="tight")
    # Show plot
    plt.show()


def plot_multiple_occurrences(perf_sample_events, ip_to_func_name):
    # List of tax categories
    tax_categories = [
        "c_libraries",
        "compress",
        "encryption",
        "mem",
        "sync",
        "rpc",
        "serialization",
        "application_logic",
        "kernel"
    ]

    # Initialize a dictionary to store CPU cycles for each tax category
    store_cpu_cycles_by_tax = {tax: 0 for tax in tax_categories}

    # Iterate through each sample
    for (i, event) in enumerate(perf_sample_events):
        sample = event.sample_event
        
        # Iterate through each branch stack in the sample
        for branch in sample.branch_stack:
            # Get the function name from the instruction pointer
            instruction_pointer = branch.from_ip
            function_name = ip_to_func_name.get(instruction_pointer, None)
            
            # Categorize the function into a tax category
            if function_name is None or function_name == "":
                category = "application_logic"
            else:
                category = bucketize(function_name)
            
            # Add the cycles to the total for the category
            store_cpu_cycles_by_tax[category] += branch.cycles

    # Calculate the total CPU cycles
    total_cpu_cycles = sum(store_cpu_cycles_by_tax.values())

    # Calculate the percentage of CPU cycles for each tax category
    percentage_cpu_cycles = {tax: (store_cpu_cycles_by_tax[tax] / total_cpu_cycles) * 100 for tax in store_cpu_cycles_by_tax.keys()}

    # Calculate the percentage of CPU cycles for the 'application_logic' category
    application_logic_percentage = (store_cpu_cycles_by_tax['application_logic'] / total_cpu_cycles) * 100

    # Calculate the percentage of CPU cycles for all other tax categories combined
    other_tax_categories_percentage = 100 - application_logic_percentage

    # Plot the results
    plt.figure(figsize=(8, 6))
    plt.bar('application_logic', application_logic_percentage, color='black', label='Application Logic')
    plt.bar('application_logic', other_tax_categories_percentage, bottom=application_logic_percentage, color='maroon', label='Other Tax Categories')
    plt.xlabel('Memcached')
    plt.ylabel('Percentage of CPU Cycles (%)')
    plt.title('Percentage of CPU Cycles by Category')
    plt.legend()
    plt.xticks([])
    plt.ylim(0, 100)
    plt.text('application_logic', application_logic_percentage + 1, f"{application_logic_percentage:.2f}%", ha='center')
    plt.text('application_logic', 50, f"{other_tax_categories_percentage:.2f}%", ha='center')

    # Save the plot as an image
    plt.savefig("results/multiple_occurrences.png", bbox_inches="tight")

    # Show the plot
    plt.show()



def tax_heatmap(perf_sample_events, ip_to_func_name):
    tax_categories = [
    "c_libraries",
    "compress",
    # "hash",
    "encryption",
    # "kernel",
    "mem",
    # "miscellaneous",
    "sync",
    "rpc",
    "serialization",
    # "application_logic",
    "kernel"

]
    bucketized_chains = []

    for (i, event) in enumerate(perf_sample_events):
        sample = event.sample_event
        taxes_found = []
        curr_chain = []
        for branch in sample.branch_stack:
            ip = branch.from_ip
            func = ip_to_func_name[ip]
            if func is None or func == "":
                cat = "kernel"
            else:
                cat = bucketize(func)
            curr_chain.append(cat)
        bucketized_chains.append(curr_chain)
    

    heatmap_hops = np.full((len(tax_categories), len(tax_categories)), -1)
    heatmap_annotation = np.zeros((len(tax_categories), len(tax_categories)))
    
    for i, from_tax in enumerate(tax_categories):
        for j, to_tax in enumerate(tax_categories):
            if from_tax == to_tax:
                continue
            heat_val = 0
            heat_cycles = 0
            path_count = 0
            for chain in bucketized_chains:
                min_hops = 33
                found = False
                for (chain_idx, bucket) in enumerate(chain):
                    if bucket == from_tax:
                        to_chains = chain[chain_idx:]
                        for (search_idx, curr_bucket) in enumerate(to_chains):
                            if curr_bucket == to_tax:
                                found = True
                                min_hops = min(min_hops, np.abs(search_idx-chain_idx))
                heat_val += min_hops if found else 0
                path_count += 1 if found else 0
            print(f"{from_tax}, {to_tax}: {heat_val}, {path_count}")
            heatmap_annotation[i, j] = path_count
            if path_count == 0: continue
            heatmap_hops[i, j] = heat_val/path_count
    ax =  sns.heatmap(heatmap_hops,
                xticklabels=tax_categories,
                yticklabels=tax_categories,
                annot=heatmap_annotation,
                fmt="g",
                linewidths=1,
                linecolor='black',
                vmax=20,
                annot_kws={"size": 7},
                cbar={"label": "# Function Calls Between"})
    
    plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
    # plt.yticks(rotation=45, ha="right", rotation_mode="anchor")

    cbar= ax.collections[0].colorbar
    cbar.set_label("# Function Calls Between", size=9)


    plt.savefig("results/tax_heatmap.png", bbox_inches="tight")

def tax_bars(perf_sample_events, ip_to_func_name):
    xs = tax_categories
    ys = [0 for _ in tax_categories]
    length = len(perf_sample_events)
    for (i, event) in enumerate(perf_sample_events):
        if i%100 == 0:
            print(f"{i}/{len(perf_sample_events)}")
        sample = event.sample_event
        if sample.branch_stack is None or len(sample.branch_stack) == 0:
            length -= 1
            continue
        ip = sample.branch_stack[0].from_ip
        func = ip_to_func_name[ip]
        if func is None or func == "":
            cat = "kernel"
        else:
            cat = bucketize(func)
        ys[xs.index(cat)] += 1
    ys = [y/length*100 for y in ys]
    # xs = sorted(xs, key=(lambda x: ys[xs.index(x)]), reverse=True)
    # ys.sort(reverse=True)
    print(xs)
    print(ys)
    print(sum(ys))
    return None


def build_ip_mapping(perf_sample_events):
    ip_to_func_name = {}
    for i, event in enumerate(perf_sample_events):
        if i%100 == 0:
            print(f"{i}/{len(perf_sample_events)}")
        sample_event = event.sample_event
        for branch in sample_event.branch_stack:
            if branch.from_ip in ip_to_func_name:
                continue
            ip_to_func_name[branch.from_ip] = symbolize.get_symbols(branch.from_ip)[branch.from_ip]
    return ip_to_func_name


with open("ip_map.pickle", "wb") as f:
    ip_to_func_name = build_ip_mapping(perf_sample_events)
    pickle.dump(ip_to_func_name, f)
    # ip_to_func_name = pickle.load(f)
    # print(ip_to_func_name.keys())

def work():
    print("Plotting chain cdf")
    plot_chain_cdf(perf_sample_events)
    print("plotting tax sharing")
    plot_tax_sharing(perf_sample_events, ip_to_func_name)
    print("tax")
    tax_bars(perf_sample_events, ip_to_func_name)
    print("plotting heatmap")
    tax_heatmap(perf_sample_events, ip_to_func_name)
    print("Plotting Sample Based Attribution")
    plot_sample_based_attribution(perf_sample_events, ip_to_func_name)
    print("Plotting Multiple Occurrences")
    plot_multiple_occurrences(perf_sample_events, ip_to_func_name)
    

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

