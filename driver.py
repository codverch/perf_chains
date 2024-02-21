# Import necessary libraries
import symbolizer
import perf_data_pb2
import collections
import seaborn as sns
import matplotlib.pyplot as plt
import functools
import cProfile
import pickle
import numpy as np

# Function to parse the protobuf file
def parse_perf_proto(perf_data_proto):
    with open(perf_data_proto, "rb") as proto_file:
        proto_string = proto_file.read()
        perf_data = perf_data_pb2.PerfDataProto().FromString(proto_string)
    return perf_data

# Function to get a list of sample events from the protobuf file
def get_events_list(perf_proto):
    return list(filter(lambda event: event.sample_event is not None,
                       perf_proto.events))

# Define locations of input files
PERF_DATA_LOCATION = "./perf.data"
PERF_PROTO_LOCATION = "./perf.proto"

print("Parsing Proto")
# Parse the protobuf file
perf_proto = parse_perf_proto(PERF_PROTO_LOCATION)
# Get a list of sample events
perf_sample_events = get_events_list(perf_proto)

print("setting up symbolizer")
# Set up symbolizer
symbolize = symbolizer.Symbolizer(PERF_DATA_LOCATION)

# Define location for uncategorized functions
uncat_file = "./uncategorized"

# Define tax categories
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

# Set plot parameters
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

# Read keyword files for each tax category
file_contents = {}
for tax in tax_categories:
    with open(f"bucketization/{tax}_keywords", "r") as f:
        file_contents[tax] = f.readlines()

# Memoization dictionary
memo = {}

# ============================================================================
# Function: bucketize
# Description: This function assigns functions to tax categories based on 
#              predefined keywords.
# ============================================================================

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
    # If function is not found in any tax category, write it to uncategorized file
    with open(uncat_file, "a") as uncat:
        uncat.write(function_name + "\n")
    memo[function_name] = "application_logic"
    return "application_logic"

top_functions_chains={} 


# ============================================================================
# Function: plot_tax_sharing_all_functions
# Description: This function plots the tax sharing for all functions across all 
#              samples. It considers all the branch stacks in all the samples 
#              for evaluation.
# ============================================================================

def plot_tax_sharing_all_functions(perf_sample_events, ip_to_func_name):
    # Define tax categories
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
    
    # Initialize x-axis (tax categories) and y-axis (percentage of CPU cycles) data
    xs = tax_categories
    ys = [0 for _ in tax_categories]

    # Calculate total CPU cycles across all samples and branch stacks
    total_cpu_cycles = sum([sum([branch.cycles for branch in event.sample_event.branch_stack]) for event in perf_sample_events if event.sample_event.branch_stack])

    # Iterate over each sample event
    for (i, event) in enumerate(perf_sample_events):
        if i % 100 == 0:
            print(f"{i}/{len(perf_sample_events)}") 
        sample = event.sample_event
        taxes_found = []

        # Iterate over each branch in the branch stack
        for branch in sample.branch_stack:
            instruction_pointer = branch.from_ip
            function_name = ip_to_func_name.get(instruction_pointer, None)
            
            # Categorize the function into a tax category
            if function_name is None or function_name == "":
                cat = "application_logic"
            else:
                cat = bucketize(function_name)
            
            # Update percentage of CPU cycles for the tax category
            if cat not in taxes_found:
                ys[xs.index(cat)] += branch.cycles / total_cpu_cycles * 100
                taxes_found.append(cat)

    # Print raw data for tax sharing
    print("Tax Sharing Raw Data for all functions")
    print(xs)
    print(ys)

    # Sort tax categories based on percentage of CPU cycles for better visualization
    xs = sorted(xs, key=(lambda x: ys[xs.index(x)]), reverse=True)
    ys.sort(reverse=True)

    # Create a bar plot
    ax = sns.barplot(x=xs, y=ys, palette="muted")

    # Customize plot appearance
    plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
    plt.xlabel("Tax Categories", fontsize=16)
    plt.ylabel("Percentage of CPU Cycles", fontsize=16)
    plt.title("Memcached Tax Sharing All functions", fontsize=16)
    plt.savefig("cpu_cycles_memcached/tax_sharing_all_functions.png", bbox_inches="tight")

    # Clear and close the plot to avoid overlapping with other plots
    plt.cla()
    plt.clf()

# ============================================================================
# Function: plot_all_branches_sample_attribution
# Description: This function calculates and plots the attribution of CPU cycles 
#              to different tax categories for all branch stacks in all samples.
# ============================================================================

def plot_all_branches_sample_attribution(perf_sample_events, ip_to_func_name):
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
                cat = "application_logic"
            else:
                cat = bucketize(function_name)
            
            # Add the cycles to the total for the category
            store_cpu_cycles_by_tax[cat] += branch.cycles

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

    # Save the plot as an image
    plt.title("Memcached All Branches Sample Attribution - CPU Cycles")
    plt.savefig("cpu_cycles_memcached/all_branches_sample_attribution.png", bbox_inches="tight")

    # Show the plot
    plt.show()

# =============================================================================
# Function: plot_tax_heatmap
# Description: This function generates a heatmap representing the frequency of function calls between different tax categories in the Memcached application,
#              across all samples, considering all branch stacks.
# =============================================================================

def plot_tax_heatmap(perf_sample_events, ip_to_func_name):
    # Define tax categories
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

    # Initialize list to store chains of tax categories for each branch stack
    bucketized_chains = []

    # Iterate over each sample event
    for (i, event) in enumerate(perf_sample_events):
        sample = event.sample_event
        curr_chain = []

        # Iterate over each branch in the branch stack
        for branch in sample.branch_stack:
            ip = branch.from_ip
            func = ip_to_func_name[ip]

            # Categorize the function into a tax category
            if func is None or func == "":
                cat = "application_logic"
            else:
                cat = bucketize(func)

            curr_chain.append(cat)
        bucketized_chains.append(curr_chain)

    # Initialize arrays for heatmap data
    heatmap_hops = np.full((len(tax_categories), len(tax_categories)), -1)
    heatmap_annotation = np.zeros((len(tax_categories), len(tax_categories)))

    # Calculate frequency of function calls between tax categories
    for i, from_tax in enumerate(tax_categories):
        for j, to_tax in enumerate(tax_categories):
            if from_tax == to_tax:
                continue
            heat_val = 0
            path_count = 0

            # Iterate over each chain of tax categories
            for chain in bucketized_chains:
                min_hops = 33
                found = False

                # Find the minimum number of function calls between from_tax and to_tax in each chain
                for (chain_idx, bucket) in enumerate(chain):
                    if bucket == from_tax:
                        to_chains = chain[chain_idx:]
                        for (search_idx, curr_bucket) in enumerate(to_chains):
                            if curr_bucket == to_tax:
                                found = True
                                min_hops = min(min_hops, np.abs(search_idx - chain_idx))

                heat_val += min_hops if found else 0
                path_count += 1 if found else 0

            # Store frequency of function calls in heatmap data arrays
            heatmap_annotation[i, j] = path_count
            if path_count == 0:
                continue
            heatmap_hops[i, j] = heat_val / path_count

    # Generate heatmap
    ax = sns.heatmap(heatmap_hops,
                     xticklabels=tax_categories,
                     yticklabels=tax_categories,
                     annot=heatmap_annotation,
                     fmt="g",
                     linewidths=1,
                     linecolor='black',
                     vmax=20,
                     annot_kws={"size": 7},
                     cbar={"label": "# Function Calls Between"})

    # Customize plot appearance
    plt.xticks(rotation=45, ha="right", rotation_mode="anchor")

    # Add color bar label
    cbar = ax.collections[0].colorbar
    cbar.set_label("# Function Calls Between", size=9)

    # Set plot title
    plt.title("Memcached Tax Heatmap")

    # Save the plot
    plt.savefig("cpu_cycles_memcached/tax_heatmap.png", bbox_inches="tight")


# =============================================================================
# Function: build_ip_mapping
# Description: This function builds a mapping of instruction pointers (IPs) to function names.
# It iterates over all sample events and their branch stacks to extract IPs and map them to function names using the symbolizer.
# =============================================================================

def build_ip_mapping(perf_sample_events):
    ip_to_func_name = {}
    for i, event in enumerate(perf_sample_events):
        # Print progress message every 100 events
        if i % 100 == 0:
            print(f"Processing {i}/{len(perf_sample_events)} samples")
        sample_event = event.sample_event
        for branch in sample_event.branch_stack:
            # Skip if IP is already mapped
            if branch.from_ip in ip_to_func_name:
                continue
            # Map IP to function name using symbolizer
            ip_to_func_name[branch.from_ip] = symbolize.get_symbols(branch.from_ip)[branch.from_ip]
    return ip_to_func_name


with open("ip_map.pickle", "wb") as f:
    ip_to_func_name = build_ip_mapping(perf_sample_events)
    pickle.dump(ip_to_func_name, f)
    # ip_to_func_name = pickle.load(f)
    # print(ip_to_func_name.keys())



def work():
    print("Plotting Tax Sharing All Functions")
    plot_tax_sharing_all_functions(perf_sample_events, ip_to_func_name)
    print("Plotting All Branches Sample Attribution")
    plot_all_branches_sample_attribution(perf_sample_events, ip_to_func_name)
    print("Plotting Tax Heatmap")
    plot_tax_heatmap(perf_sample_events, ip_to_func_name)

work()
