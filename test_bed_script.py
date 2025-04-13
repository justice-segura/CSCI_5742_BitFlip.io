import os
import gc
import random
import shutil
import argparse
import timeit
import statistics
import numpy as np
import platform
import datetime
import math
import json
import csv
import psutil
from scipy import stats
import matplotlib.pyplot as plt

###############################################
# Test Functions
###############################################

def cpu_test():
    """
    CPU performance test: multiplies random numbers repeatedly.
    """
    result = 1
    for _ in range(10**7):  # Adjust iterations as needed.
        num = random.random()
        result *= num if result != 0 else 1

def memory_test():
    """
    Memory performance test:
    Allocates a 2GB array of np.uint8 and performs 100,000 random read/write operations.
    """
    size_bytes = 2 * 1024 * 1024 * 1024  # 2GB in bytes.
    num_elements = size_bytes  # Each np.uint8 uses 1 byte.
    try:
        arr = np.zeros(num_elements, dtype=np.uint8)
    except MemoryError:
        raise MemoryError("Memory allocation failed. Not enough memory available for the test.")
    for _ in range(100_000):
        idx = random.randint(0, num_elements - 1)
        # Use modulo 256 for full 8-bit range wrap-around.
        arr[idx] = (arr[idx] + 1) % 255
    del arr
    gc.collect()

def disk_write_test(disk_size):
    """
    Disk Write Test:
    Creates and writes a file of size 'disk_size' bytes using random data.
    """
    file_name = "disk_test_file.bin"
    start = timeit.default_timer()
    with open(file_name, "wb") as f:
        f.write(os.urandom(disk_size))
    end = timeit.default_timer()
    duration = end - start
    return duration

def disk_read_test(disk_size):
    """
    Disk Read Test:
    Reads the file created by disk_write_test in 1MB chunks.
    """
    file_name = "disk_test_file.bin"
    if not os.path.exists(file_name):
        with open(file_name, "wb") as f:
            f.write(os.urandom(disk_size))
    start = timeit.default_timer()
    with open(file_name, "rb") as f:
        while f.read(1024 * 1024):  # Read 1MB chunks.
            pass
    end = timeit.default_timer()
    duration = end - start
    return duration

def disk_copy_test(disk_size):
    """
    Disk Copy Test:
    Copies the file to a new file.
    """
    source_file = "disk_test_file.bin"
    destination_file = "disk_test_file_copy.bin"
    if not os.path.exists(source_file):
        with open(source_file, "wb") as f:
            f.write(os.urandom(disk_size))
    start = timeit.default_timer()
    shutil.copy(source_file, destination_file)
    end = timeit.default_timer()
    duration = end - start
    if os.path.exists(destination_file):
        os.remove(destination_file)
    return duration

###############################################
# Helper Functions for Analysis & Output
###############################################

def compute_statistics(times):
    n = len(times)
    mean_val = statistics.mean(times)
    median_val = statistics.median(times)
    std_val = statistics.stdev(times) if n > 1 else 0
    perc25 = statistics.quantiles(times, n=4)[0]  # 25th percentile
    perc75 = statistics.quantiles(times, n=4)[-1]  # 75th percentile
    min_val = min(times)
    max_val = max(times)
    
    if n > 1:
        if stats:
            t_val = stats.t.ppf(1 - 0.025, n - 1)
        else:
            t_val = 2.776  
        margin_error = t_val * (std_val / math.sqrt(n))
        ci_lower = mean_val - margin_error
        ci_upper = mean_val + margin_error
    else:
        ci_lower = ci_upper = mean_val
    
    return {
        'mean': mean_val,
        'median': median_val,
        'std_dev': std_val,
        '25th_percentile': perc25,
        '75th_percentile': perc75,
        'min': min_val,
        'max': max_val,
        '95%_ci': (ci_lower, ci_upper)
    }

def run_test(test_func, test_name, repeat, number, disk_size=None):
    if disk_size is not None:
        wrapped_func = lambda: test_func(disk_size)
    else:
        wrapped_func = test_func

    times = timeit.repeat(wrapped_func, repeat=repeat, number=number)
    stats_dict = compute_statistics(times)
    return {
        'name': test_name,
        'times': times,
        'statistics': stats_dict
    }

def warmup(test_func, warmup_count, disk_size=None):
    if disk_size is not None:
        wrapped_func = lambda: test_func(disk_size)
    else:
        wrapped_func = test_func
    for _ in range(warmup_count):
        wrapped_func()

def get_system_info():
    info = {
        'timestamp': datetime.datetime.now().isoformat(),
        'os': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': os.cpu_count()
    }
    if psutil:
        vm = psutil.virtual_memory()
        info['total_memory'] = vm.total
        info['available_memory'] = vm.available
    return info

def create_run_directory(base_dir="output"):
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)
    run_name = "run_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_dir, run_name)
    os.mkdir(run_dir)
    graphs_dir = os.path.join(run_dir, "graphs")
    os.mkdir(graphs_dir)
    return run_dir, graphs_dir

def generate_graphs(test_results, graphs_dir):
    """
    Generates line graphs for each test (iteration number vs time) and a
    comparison bar chart. Graphs are saved in the specified graphs_dir.
    Returns a tuple (line_graph_files, comp_chart_file) where:
      - line_graph_files is a dict mapping test names to their graph file names.
      - comp_chart_file is the file name for the comparison bar chart.
    """
    line_graph_files = {}
    if plt is None:
        print("Matplotlib is not installed. Skipping graph generation.")
        return line_graph_files, None

    # Create line graphs for individual tests.
    for test in test_results:
        if "statistics" in test and "times" in test:
            times = test["times"]
            iterations = list(range(1, len(times) + 1))
            plt.figure()
            plt.plot(iterations, times, marker='o')
            plt.title(f"{test['name']} Timing per Iteration")
            plt.xlabel("Run Iteration")
            plt.ylabel("Time (s)")
            plt.grid(True)
            plt.tight_layout()
            # File name: lower-case, no spaces, appended with _line.png.
            file_name = test["name"].lower().replace(" ", "_") + "_line.png"
            file_path = os.path.join(graphs_dir, file_name)
            plt.savefig(file_path)
            plt.close()
            line_graph_files[test["name"]] = file_name

    # Create a comparison bar chart of mean times with 95% CI error bars.
    valid_tests = [test for test in test_results if "statistics" in test]
    comp_chart_file = None
    if valid_tests:
        names = [test['name'] for test in valid_tests]
        means = [test['statistics']['mean'] for test in valid_tests]
        errors = [(test['statistics']['95%_ci'][1] - test['statistics']['95%_ci'][0]) / 2 for test in valid_tests]
        plt.figure()
        plt.bar(names, means, yerr=errors, capsize=5)
        plt.title("Average Test Times with 95% Confidence Intervals")
        plt.xlabel("Test")
        plt.ylabel("Mean Time (s)")
        plt.grid(True, axis='y')
        plt.tight_layout()
        comp_chart_file = "comparison_bar_chart.png"
        comp_chart_path = os.path.join(graphs_dir, comp_chart_file)
        plt.savefig(comp_chart_path)
        plt.close()
    return line_graph_files, comp_chart_file

def generate_csv(test_results, out_dir):
    """
    Generates a CSV file containing raw test results and summary statistics.
    The CSV is saved as 'results.csv' in the out_dir.
    """
    csv_file = os.path.join(out_dir, "results.csv")
    header = ['Test Name', 'Mean', 'Median', 'Std Dev', '25th Percentile', '75th Percentile', 'Min', 'Max', '95% CI Lower', '95% CI Upper', 'Times']
    rows = [header]
    for test in test_results:
        stats_d = test.get('statistics', {})
        row = [
            test.get('name', ''),
            f"{stats_d.get('mean', 0):.4f}",
            f"{stats_d.get('median', 0):.4f}",
            f"{stats_d.get('std_dev', 0):.4f}",
            f"{stats_d.get('25th_percentile', 0):.4f}",
            f"{stats_d.get('75th_percentile', 0):.4f}",
            f"{stats_d.get('min', 0):.4f}",
            f"{stats_d.get('max', 0):.4f}",
            f"{stats_d.get('95%_ci', (0,0))[0]:.4f}",
            f"{stats_d.get('95%_ci', (0,0))[1]:.4f}",
            test.get('times', [])
        ]
        rows.append(row)
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return csv_file

def generate_markdown(system_info, test_results, line_graph_files, comp_chart_file):
    """
    Generates a Markdown report (write-up.md) with system info, test details,
    and embedded graphs. Graph image paths are relative to the report.
    """
    md_lines = []
    md_lines.append("# Performance Test Results")
    md_lines.append("")
    md_lines.append("## System Information")
    for key, value in system_info.items():
        md_lines.append(f"- **{key.capitalize().replace('_', ' ')}:** {value}")
    md_lines.append("")
    md_lines.append("## Test Results")
    for test in test_results:
        md_lines.append(f"### {test.get('name', 'Unknown')}")
        if "statistics" in test:
            s = test["statistics"]
            md_lines.append(f"- **Mean Time:** {s.get('mean', 0):.4f} seconds")
            md_lines.append(f"- **Median Time:** {s.get('median', 0):.4f} seconds")
            md_lines.append(f"- **Standard Deviation:** {s.get('std_dev', 0):.4f} seconds")
            md_lines.append(f"- **25th Percentile:** {s.get('25th_percentile', 0):.4f} seconds")
            md_lines.append(f"- **75th Percentile:** {s.get('75th_percentile', 0):.4f} seconds")
            md_lines.append(f"- **Min Time:** {s.get('min', 0):.4f} seconds")
            md_lines.append(f"- **Max Time:** {s.get('max', 0):.4f} seconds")
            ci = s.get('95%_ci', (0, 0))
            md_lines.append(f"- **95% Confidence Interval:** ({ci[0]:.4f}, {ci[1]:.4f}) seconds")
        else:
            md_lines.append("- **Error:** " + test.get("error", "Unknown error"))
        # Include line graph image if available.
        if test.get("name") in line_graph_files:
            img_file = os.path.join("graphs", line_graph_files[test.get("name")])
            md_lines.append("")
            md_lines.append(f"![{test.get('name')} Line Graph]({img_file})")
        md_lines.append("")
    # Include the comparison chart if generated.
    if comp_chart_file:
        md_lines.append("## Comparison of Test Means")
        comp_chart_path = os.path.join("graphs", comp_chart_file)
        md_lines.append(f"![Comparison Bar Chart]({comp_chart_path})")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append(f"*Report generated on {datetime.datetime.now().isoformat()}*")
    return "\n".join(md_lines)

###############################################
# Main function with CLI argument handling
###############################################

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Performance Testing with CSV output, Markdown write-up, and graphs in an output directory structure."
    )
    
    parser.add_argument(
        "--tests", "-t",
        nargs="+",
        default=["cpu", "memory", "disk"],
        choices=["cpu", "memory", "disk"],
        help="Specify which tests to run: cpu, memory, disk (default: all)"
    )
    parser.add_argument(
        "--repeat", "-r",
        type=int,
        default=5,
        help="Number of repetitions per test (default: 5)"
    )
    parser.add_argument(
        "--number", "-n",
        type=int,
        default=1,
        help="Number of executions per repetition (default: 1)"
    )
    parser.add_argument(
        "--warmup", "-w",
        type=int,
        default=1,
        help="Number of warm-up runs for each test (default: 1)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Optional random seed for reproducibility"
    )
    parser.add_argument(
        "--disk-size",
        type=int,
        default=5 * 1024 * 1024 * 1024,
        help="Size in bytes for disk tests (default: 5GB)"
    )
    
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    system_info = get_system_info()
    test_results = []

    # CPU Test
    if "cpu" in args.tests:
        print("Warming up CPU test...")
        warmup(cpu_test, args.warmup)
        print("Running CPU test...")
        try:
            cpu_result = run_test(cpu_test, "CPU Test", repeat=args.repeat, number=args.number)
            test_results.append(cpu_result)
        except Exception as e:
            test_results.append({'name': "CPU Test", 'error': str(e)})

    # Memory Test
    if "memory" in args.tests:
        print("Warming up Memory test...")
        warmup(memory_test, args.warmup)
        print("Running Memory test...")
        try:
            memory_result = run_test(memory_test, "Memory Test", repeat=args.repeat, number=args.number)
            test_results.append(memory_result)
        except MemoryError as e:
            test_results.append({'name': "Memory Test", 'error': str(e)})

    # Disk I/O Tests
    if "disk" in args.tests:
        print("Warming up Disk Write test...")
        warmup(disk_write_test, args.warmup, disk_size=args.disk_size)
        print("Running Disk Write test...")
        try:
            disk_write_result = run_test(disk_write_test, "Disk Write Test", repeat=args.repeat, number=args.number, disk_size=args.disk_size)
            test_results.append(disk_write_result)
        except Exception as e:
            test_results.append({'name': "Disk Write Test", 'error': str(e)})

        print("Warming up Disk Read test...")
        warmup(disk_read_test, args.warmup, disk_size=args.disk_size)
        print("Running Disk Read test...")
        try:
            disk_read_result = run_test(disk_read_test, "Disk Read Test", repeat=args.repeat, number=args.number, disk_size=args.disk_size)
            test_results.append(disk_read_result)
        except Exception as e:
            test_results.append({'name': "Disk Read Test", 'error': str(e)})

        print("Warming up Disk Copy test...")
        warmup(disk_copy_test, args.warmup, disk_size=args.disk_size)
        print("Running Disk Copy test...")
        try:
            disk_copy_result = run_test(disk_copy_test, "Disk Copy Test", repeat=args.repeat, number=args.number, disk_size=args.disk_size)
            test_results.append(disk_copy_result)
        except Exception as e:
            test_results.append({'name': "Disk Copy Test", 'error': str(e)})

        test_file = "disk_test_file.bin"
        if os.path.exists(test_file):
            os.remove(test_file)

    # Create run output directories.
    run_dir, graphs_dir = create_run_directory()

    # Generate graphs (line graphs per test and comparison chart).
    line_graph_files, comp_chart_file = generate_graphs(test_results, graphs_dir)

    # Generate CSV with raw results.
    csv_file = generate_csv(test_results, run_dir)

    # Generate Markdown report (write-up.md).
    markdown_content = generate_markdown(system_info, test_results, line_graph_files, comp_chart_file)
    md_file_path = os.path.join(run_dir, "write-up.md")
    with open(md_file_path, "w") as md_file:
        md_file.write(markdown_content)

    print(f"\nResults saved in: {os.path.abspath(run_dir)}")
    print(f"- CSV: {csv_file}")
    print(f"- Markdown report: {md_file_path}")

if __name__ == "__main__":
    main()
