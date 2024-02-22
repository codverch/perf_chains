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
        # Print the contents of the protobuf file into a human-readable format in a text file
        with open("perf_data.txt", "w") as text_file:
            text_file.write(str(perf_data))
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
    "application_logic",
    "compress",
    # "hash",
    "encryption",
    # "kernel",
    "mem",
    # "miscellaneous",
    "sync",
    "rpc",
    "serialization",
    "kernel"
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
# Define location for categorized functions
cat_file = "./categorized.txt"

def bucketize(function_name):
    for tax in tax_categories:
        lines = file_contents[tax]
        for func in lines:
            func = func.split("#")[0].strip()
            if func in function_name:
                with open(cat_file, "a") as cat:
                    cat.write(f"{function_name}: {tax}\n")
                return tax  # Exit the loop once a category is found
    with open(uncat_file, "a") as uncat:
        uncat.write(function_name + "\n")
    return None



top_functions_chains={} 


# ============================================================================
# Function: plot_tax_sharing_all_functions
# Description: This function plots the tax sharing for all functions across all 
#              samples. It considers all the branch stacks in all the samples 
#              for evaluation.
# ============================================================================

def plot_tax_sharing_all_functions(perf_sample_events, ip_to_func_name):
 
    # Initialize x-axis (tax categories) and y-axis (percentage of CPU cycles) data
    xs = tax_categories
    ys = [0 for _ in tax_categories]

    # Calculate total CPU cycles across all samples and branch stacks
    total_cpu_cycles = sum([sum([branch.cycles for branch in event.sample_event.branch_stack]) for event in perf_sample_events if event.sample_event.branch_stack])

    # Iterate over each sample event
    for (i, event) in enumerate(perf_sample_events):
        sample = event.sample_event
        taxes_found = []

        # Iterate over each branch in the branch stack
        for branch in sample.branch_stack:
            instruction_pointer = branch.from_ip
            function_name = ip_to_func_name.get(instruction_pointer, None)

            cat = bucketize(function_name)

            if(cat is None):
                cat = "application_logic"

            if cat not in taxes_found:
                ys[xs.index(cat)] += (branch.cycles / total_cpu_cycles) * 100
                # taxes_found.append(cat)

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

def plot_tax_sharing_top_functions(perf_sample_events, ip_to_func_name):
 
    # Initialize x-axis (tax categories) and y-axis (percentage of CPU cycles) data
    xs = tax_categories
    ys = [0 for _ in tax_categories]

    # Calculate total CPU cycles across all samples and first branch stack
    total_cpu_cycles = sum([event.sample_event.branch_stack[0].cycles for event in perf_sample_events if event.sample_event.branch_stack])

    # Iterate over each sample event
    for (i, event) in enumerate(perf_sample_events):
        sample = event.sample_event
        taxes_found = []

        # Iterate over first branch stacks in each sample
        if sample.branch_stack:
            branch = sample.branch_stack[0]
            instruction_pointer = branch.from_ip
            function_name = ip_to_func_name.get(instruction_pointer, None)
            cat = bucketize(function_name)

            if(cat is None):
                cat = "application_logic"

            if cat not in taxes_found:
                ys[xs.index(cat)] += (branch.cycles / total_cpu_cycles) * 100
                # taxes_found.append(cat)

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
    plt.title("Memcached Tax Sharing Top functions", fontsize=16)
    plt.savefig("cpu_cycles_memcached/tax_sharing_top_functions.png", bbox_inches="tight")

    # Clear and close the plot to avoid overlapping with other plots
    plt.cla()
    plt.clf()



def plot_all_branches_sample_attribution(perf_sample_events, ip_to_func_name):

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

            # Bucketize the function name
            cat = bucketize(function_name)

            if(cat is None):
                cat = "application_logic"
            
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
    print("Plotting Tax Sharing Top Functions")
    plot_tax_sharing_top_functions(perf_sample_events, ip_to_func_name)
    print("Plotting Tax Sharing All Functions")
    plot_tax_sharing_all_functions(perf_sample_events, ip_to_func_name)
    print("Plotting All Branches Sample Attribution")
    plot_all_branches_sample_attribution(perf_sample_events, ip_to_func_name)
    
work()