def plot_tax_sharing_top_function(perf_sample_events, ip_to_func_name):
    xs = tax_categories
    ys = [0 for _ in tax_categories]

    for (i, event) in enumerate(perf_sample_events):
        if i % 100 == 0:
            print(f"{i}/{len(perf_sample_events)}")
        sample = event.sample_event
        taxes_found = []
        
        if sample.branch_stack:
            branch = sample.branch_stack[0] # Sample only the top function
            ip = branch.from_ip
            func = ip_to_func_name.get(ip, None)
            if func is None or func == "":
                cat = "application_logic"
            else:
                cat = bucketize(func)

            if cat not in taxes_found:
                ys[xs.index(cat)] += 1
                taxes_found.append(cat)

    print("Tax Sharing Raw Data for top function")
    print(xs)
    print(ys)
    ys = [y/len(perf_sample_events)*100 for y in ys] # Normalized to total number of samples
    xs = sorted(xs, key=(lambda x: ys[xs.index(x)]), reverse=True)
    ys.sort(reverse=True)
    ax = sns.barplot(x=xs, y=ys, errorbar=None, ci=None)

    plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
    plt.xlabel("Tax Categories", fontsize=16)
    plt.ylabel("Percent of Chains", fontsize=16)
    plt.title("Memcached Tax Sharing Top Function", fontsize=16)
    plt.savefig("test/tax_sharing_top_function.png", bbox_inches="tight")

    plt.cla()
    plt.clf()

def plot_tax_sharing_all_functions(perf_sample_events, ip_to_func_name):
    xs = tax_categories
    ys = [0 for _ in tax_categories]

    for (i, event) in enumerate(perf_sample_events):
        if i % 100 == 0:
            print(f"{i}/{len(perf_sample_events)}")
        sample = event.sample_event
        taxes_found = []

        for branch in sample.branch_stack:
            instruction_pointer = branch.from_ip
            function_name = ip_to_func_name.get(instruction_pointer, None)
            
            # Categorize the function into a tax category
            if function_name is None or function_name == "":
                cat = "application_logic"
            else:
                cat = bucketize(function_name)
            
            if cat not in taxes_found:
                ys[xs.index(cat)] += 1
                taxes_found.append(cat)

    print("Tax Sharing Raw Data for all functions")
    print(xs)
    print(ys)
    ys = [y/len(perf_sample_events)*100 for y in ys] # Normalized to total number of samples
    xs = sorted(xs, key=(lambda x: ys[xs.index(x)]), reverse=True)
    ys.sort(reverse=True)
    ax = sns.barplot(x=xs, y=ys, errorbar=None, ci=None)

    plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
    plt.xlabel("Tax Categories", fontsize=16)
    plt.ylabel("Percent of Chains", fontsize=16)
    plt.title("Memcached Tax Sharing All Functions", fontsize=16)
    plt.savefig("test/tax_sharing_all_functions.png", bbox_inches="tight")