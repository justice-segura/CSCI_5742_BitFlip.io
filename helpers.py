import csv
import datetime
import math
import matplotlib.pyplot as plt
import os
import platform
import psutil
from scipy import stats
import statistics
import timeit

def compute_statistics(times):
    """
    Computes statistics from a list of times.
    Returns a dictionary with mean, median, std deviation, percentiles,
    min, max, and 95% confidence interval.
    """
    tests_executed = len(times)
    mean_val = statistics.mean(times)
    median_val = statistics.median(times)
    std_val = statistics.stdev(times) if tests_executed > 1 else 0
    perc25 = statistics.quantiles(times, n=4)[0]  # 25th percentile
    perc75 = statistics.quantiles(times, n=4)[-1]  # 75th percentile
    min_val = min(times)
    max_val = max(times)
    
    if tests_executed > 1:
        if stats:
            t_val = stats.t.ppf(1 - 0.025, tests_executed - 1)
        else:
            t_val = 2.776  
        margin_error = t_val * (std_val / math.sqrt(tests_executed))
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
    """
    Runs a test function and computes its execution time.
    Returns a dictionary with test name, execution times, and statistics.
    """
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
    """
    Runs a test function for warm-up iterations to prepare the system.
    This is useful for disk tests to ensure the OS caches are warmed up.
    """
    if disk_size is not None:
        wrapped_func = lambda: test_func(disk_size)
    else:
        wrapped_func = test_func
    for _ in range(warmup_count):
        wrapped_func()

def get_system_info():
    """
    Returns a dictionary with system information such as OS, Python version,
    CPU count, and memory details (if available).
    """
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
    """
    Creates a directory structure for storing test results.
    The base directory is 'output' by default. Inside, it creates a
    timestamped run directory and a 'graphs' subdirectory for graphs.
    Returns a tuple (run_dir, graphs_dir) with the paths to the created directories.
    """
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