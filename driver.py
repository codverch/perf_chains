# Import necessary libraries
import symbolizer
import perf_data_pb2
import seaborn as sns
import matplotlib.pyplot as plt
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


with open("debug.txt", "w") as f:
    for event in perf_sample_events:
        f.write(str(event) + "\n")

print("Setting up symbolizer")
# Set up symbolizer
symbolize = symbolizer.Symbolizer(PERF_DATA_LOCATION)

# Define location for uncategorized functions
uncat_file = "./uncategorized"

# Define tax categories
tax_categories = [
    "c_libraries",
    "application_logic",
    "compress",
    "encryption",
    "mem",
    "sync",
    "rpc",
    "serialization",
    "kernel"
]

# Read keyword files for each tax category
file_contents = {}
for tax in tax_categories:
    with open(f"bucketization/{tax}_keywords", "r") as f:
        file_contents[tax] = f.readlines()

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

# ============================================================================
# Function: plot_tax_sharing_all_functions
# Description: This function plots the tax sharing for all functions across all 
#              samples. It considers all the branch stacks in all the samples 
#              for evaluation.
# ============================================================================

def plot_tax_sharing_all_functions(perf_sample_events, ip_to_func_name):
    # Initialize x-axis (tax categories) and y-axis (percentage of branch mispredictions) data
    xs = tax_categories
    ys = [0 for _ in tax_categories]

    # Calculate total branch mispredictions across all samples and branch stacks
    total_branch_mispredictions = sum([len(event.sample_event.branch_stack) for event in perf_sample_events if event.sample_event.branch_stack])

    # Iterate over each sample event
    for (i, event) in enumerate(perf_sample_events):
        sample = event.sample_event

        # Iterate over each branch in the branch stack
        for branch in sample.branch_stack:
            instruction_pointer = branch.from_ip
            function_name = ip_to_func_name.get(instruction_pointer, None)

            cat = bucketize(function_name)

            if(cat is None):
                cat = "application_logic"

            ys[xs.index(cat)] += 1

    # Calculate percentage of branch mispredictions for each tax category
    ys_percentage = [(y / total_branch_mispredictions) * 100 for y in ys]

    # Create a bar plot
    ax = sns.barplot(x=xs, y=ys_percentage, palette="muted")

    # Customize plot appearance
    plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
    plt.xlabel("Tax Categories", fontsize=16)
    plt.ylabel("Percentage of Total Branch Mispredictions", fontsize=16)
    plt.title("Memcached Tax Sharing All Functions", fontsize=16)
    plt.savefig("branch_mispredictions_memcached/tax_sharing_all_functions.png", bbox_inches="tight")

    # Clear and close the plot to avoid overlapping with other plots
    plt.cla()
    plt.clf()

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

# Build the IP to function name mapping
with open("ip_map.pickle", "wb") as f:
    ip_to_func_name = build_ip_mapping(perf_sample_events)
    pickle.dump(ip_to_func_name, f)

# Work function to be called for processing
def work():
    plot_tax_sharing_all_functions(perf_sample_events, ip_to_func_name)

# Call the work function
work()
