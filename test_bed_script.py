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

# Try to import psutil for memory info. If not available, skip it.
try:
    import psutil
except ImportError:
    psutil = None

# Try to import scipy.stats for confidence interval calculations.
try:
    from scipy import stats
except ImportError:
    stats = None

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
        arr[idx] = (arr[idx] + 1) % 256
    del arr
    gc.collect()

# Disk test helper: using a configurable file size (default 5GB).
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
    # Ensure the file exists.
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
    # Ensure the source file exists.
    if not os.path.exists(source_file):
        with open(source_file, "wb") as f:
            f.write(os.urandom(disk_size))
    start = timeit.default_timer()
    shutil.copy(source_file, destination_file)
    end = timeit.default_timer()
    duration = end - start
    # Cleanup the copied file.
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
    
    # Compute 95% confidence interval for the mean.
    if n > 1:
        if stats:
            t_val = stats.t.ppf(1 - 0.025, n - 1)
        else:
            # Fallback t-value for df=4 (n=5) is about 2.776; this is a rough estimate.
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
    """
    Runs a test function using timeit.repeat() and returns the result dictionary.
    If disk_size is provided, it is passed to the test function.
    """
    if disk_size is not None:
        # Wrap test_func to include disk_size.
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
    Runs the test function a given number of times as a warm-up.
    """
    if disk_size is not None:
        wrapped_func = lambda: test_func(disk_size)
    else:
        wrapped_func = test_func
    for _ in range(warmup_count):
        wrapped_func()

def get_system_info():
    """
    Gather basic system information.
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

def output_results(system_info, test_results, out_format):
    """
    Format the output based on the chosen format: text, csv, or json.
    """
    if out_format == "json":
        # Combine system info and tests.
        output_dict = {
            'system_info': system_info,
            'tests': test_results
        }
        return json.dumps(output_dict, indent=4)
    elif out_format == "csv":
        # For CSV, produce rows with the test name and each statistic.
        csv_rows = []
        header = ['Test Name', 'Mean', 'Median', 'Std Dev', '25th Percentile', '75th Percentile', 'Min', 'Max', '95% CI Lower', '95% CI Upper', 'Times']
        csv_rows.append(header)
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
            csv_rows.append(row)
        # Convert CSV rows to a string.
        from io import StringIO
        sio = StringIO()
        writer = csv.writer(sio)
        writer.writerows(csv_rows)
        return sio.getvalue()
    else:  # plain text
        lines = []
        lines.append("System Information:")
        for key, value in system_info.items():
            lines.append(f"  {key}: {value}")
        lines.append("")
        for test in test_results:
            lines.append(f"Test: {test.get('name', 'Unknown')}")
            if 'statistics' in test:
                s = test['statistics']
                lines.append(f"  Times: {test.get('times', [])}")
                lines.append(f"  Mean: {s.get('mean', 0):.4f} sec")
                lines.append(f"  Median: {s.get('median', 0):.4f} sec")
                lines.append(f"  Std Dev: {s.get('std_dev', 0):.4f} sec")
                lines.append(f"  25th Percentile: {s.get('25th_percentile', 0):.4f} sec")
                lines.append(f"  75th Percentile: {s.get('75th_percentile', 0):.4f} sec")
                lines.append(f"  Min: {s.get('min', 0):.4f} sec")
                lines.append(f"  Max: {s.get('max', 0):.4f} sec")
                ci = s.get('95%_ci', (0, 0))
                lines.append(f"  95% CI: ({ci[0]:.4f}, {ci[1]:.4f}) sec")
            lines.append("")
        return "\n".join(lines)

###############################################
# Main function with CLI argument handling
###############################################

def main():
    parser = argparse.ArgumentParser(description="Enhanced Performance Testing using timeit.")
    
    # Test selection
    parser.add_argument(
        "--tests", "-t",
        nargs="+",
        default=["cpu", "memory", "disk"],
        choices=["cpu", "memory", "disk"],
        help="Specify which tests to run: cpu, memory, disk (default: all)"
    )
    # Output file (if not provided, output to terminal)
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file to write the results (default prints to terminal)"
    )
    # Timing configuration
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
    # Warm-up runs
    parser.add_argument(
        "--warmup", "-w",
        type=int,
        default=1,
        help="Number of warm-up runs for each test (default: 1)"
    )
    # Optional seed for reproducibility in CPU test (if provided)
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Optional random seed for reproducibility"
    )
    # Output format: text, csv, or json
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["text", "csv", "json"],
        default="text",
        help="Output format: text, csv, or json (default: text)"
    )
    # Disk file size in bytes (default 5GB)
    parser.add_argument(
        "--disk-size",
        type=int,
        default=5 * 1024 * 1024 * 1024,
        help="Size in bytes for disk tests (default: 5GB)"
    )
    
    args = parser.parse_args()

    # Optionally set the random seed (affects CPU test and others using random)
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    system_info = get_system_info()
    test_results = []

    ##################################
    # CPU Test
    ##################################
    if "cpu" in args.tests:
        print("Warming up CPU test...")
        warmup(cpu_test, args.warmup)
        print("Running CPU test...")
        try:
            cpu_result = run_test(cpu_test, "CPU Test", repeat=args.repeat, number=args.number)
            test_results.append(cpu_result)
        except Exception as e:
            test_results.append({'name': "CPU Test", 'error': str(e)})

    ##################################
    # Memory Test
    ##################################
    if "memory" in args.tests:
        print("Warming up Memory test...")
        warmup(memory_test, args.warmup)
        print("Running Memory test...")
        try:
            memory_result = run_test(memory_test, "Memory Test", repeat=args.repeat, number=args.number)
            test_results.append(memory_result)
        except MemoryError as e:
            test_results.append({'name': "Memory Test", 'error': str(e)})

    ##################################
    # Disk I/O Tests
    ##################################
    if "disk" in args.tests:
        # Disk Write Test
        print("Warming up Disk Write test...")
        warmup(disk_write_test, args.warmup, disk_size=args.disk_size)
        print("Running Disk Write test...")
        try:
            disk_write_result = run_test(disk_write_test, "Disk Write Test", repeat=args.repeat, number=args.number, disk_size=args.disk_size)
            test_results.append(disk_write_result)
        except Exception as e:
            test_results.append({'name': "Disk Write Test", 'error': str(e)})

        # Disk Read Test
        print("Warming up Disk Read test...")
        warmup(disk_read_test, args.warmup, disk_size=args.disk_size)
        print("Running Disk Read test...")
        try:
            disk_read_result = run_test(disk_read_test, "Disk Read Test", repeat=args.repeat, number=args.number, disk_size=args.disk_size)
            test_results.append(disk_read_result)
        except Exception as e:
            test_results.append({'name': "Disk Read Test", 'error': str(e)})

        # Disk Copy Test
        print("Warming up Disk Copy test...")
        warmup(disk_copy_test, args.warmup, disk_size=args.disk_size)
        print("Running Disk Copy test...")
        try:
            disk_copy_result = run_test(disk_copy_test, "Disk Copy Test", repeat=args.repeat, number=args.number, disk_size=args.disk_size)
            test_results.append(disk_copy_result)
        except Exception as e:
            test_results.append({'name': "Disk Copy Test", 'error': str(e)})
        
        # Clean up the test file if it exists.
        test_file = "disk_test_file.bin"
        if os.path.exists(test_file):
            os.remove(test_file)

    ##################################
    # Format and Output Results
    ##################################
    output_text = output_results(system_info, test_results, args.format)

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output_text)
            print(f"Results written to {args.output}")
        except Exception as e:
            print(f"Error writing to file: {e}")
            print(output_text)
    else:
        print("\nPerformance Test Results:\n")
        print(output_text)

if __name__ == "__main__":
    main()
