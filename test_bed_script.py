import argparse
import gc
import numpy as np
import os
import random
import shutil
import timeit

from helpers import (
    get_system_info,
    run_test,
    warmup,
    create_run_directory,
    generate_csv,
    generate_markdown,
    generate_graphs
)

################################################# CPU Tests ##################################################

def cpu_test():
    """
    CPU performance test: 
    Multiplies random numbers repeatedly.
    """
    result = 1
    for _ in range(10**7):  # Adjust iterations as needed.
        num = random.random()
        result *= num if result != 0 else 1

################################################ Memory Tests ################################################

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

############################################### Disk I/O Tests ###############################################

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
