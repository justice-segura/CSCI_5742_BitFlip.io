import os
import gc
import random
import shutil
import argparse
import timeit
import statistics
import numpy as np

def cpu_test():
    """
    CPU performance test: multiplies random numbers repeatedly.
    """
    result = 1
    for _ in range(10**7):  # Adjust iterations as needed
        num = random.random()
        result *= num if result != 0 else 1

def memory_test():
    """
    Memory performance test:
    Allocates a 2GB array of np.uint8 and performs 100,000 random read/write operations.
    """
    size_bytes = 2 * 1024 * 1024 * 1024  # 2GB in bytes
    num_elements = size_bytes  # Each element of np.uint8 is 1 byte
    try:
        arr = np.zeros(num_elements, dtype=np.uint8)
    except MemoryError:
        raise MemoryError("Memory allocation failed. Not enough memory available for the test.")
    for _ in range(100_000):
        idx = random.randint(0, num_elements - 1)
        # Increment the value modulo 255
        arr[idx] = (arr[idx] + 1) % 255
    del arr
    gc.collect()

def disk_io_test():
    """
    Disk I/O test:
    Copies a large 5GB file from one location to another.
    """
    source_file = "large_test_file.bin"
    destination_file = "large_test_file_copy.bin"

    # Create a 5GB file if it doesn't exist
    if not os.path.exists(source_file):
        print("Creating a 5GB test file. This may take a while...")
        with open(source_file, "wb") as f:
            f.write(os.urandom(5 * 1024 * 1024 * 1024))
    shutil.copy(source_file, destination_file)
    if os.path.exists(destination_file):
        os.remove(destination_file)

def run_test(test_func, test_name, repeat, number):
    """
    Run a given test function using timeit.repeat() and compute statistical measures.
    """
    times = timeit.repeat(test_func, repeat=repeat, number=number)
    mean_time = statistics.mean(times)
    median_time = statistics.median(times)
    std_dev_time = statistics.stdev(times) if repeat > 1 else 0
    return {
        'name': test_name,
        'times': times,
        'mean': mean_time,
        'median': median_time,
        'std_dev': std_dev_time
    }

def main():
    parser = argparse.ArgumentParser(description="Performance Testing using timeit.")
    parser.add_argument(
        "--tests", "-t",
        nargs="+",
        default=["cpu", "memory", "disk"],
        choices=["cpu", "memory", "disk"],
        help="Specify which tests to run: cpu, memory, disk (default: all)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file to write the results (default prints to terminal)"
    )
    parser.add_argument(
        "--repeat", "-r",
        type=int,
        default=5,
        help="Number of times each test is repeated using timeit (default: 5)"
    )
    parser.add_argument(
        "--number", "-n",
        type=int,
        default=1,
        help="Number of executions per timeit repetition (default: 1)"
    )
    args = parser.parse_args()

    results = []

    if "cpu" in args.tests:
        print("Running CPU test...")
        try:
            cpu_results = run_test(cpu_test, "CPU Test", repeat=args.repeat, number=args.number)
            results.append(cpu_results)
        except Exception as e:
            results.append({'name': "CPU Test", 'error': str(e)})

    if "memory" in args.tests:
        print("Running Memory test...")
        try:
            memory_results = run_test(memory_test, "Memory Test", repeat=args.repeat, number=args.number)
            results.append(memory_results)
        except MemoryError as e:
            results.append({'name': "Memory Test", 'error': str(e)})

    if "disk" in args.tests:
        print("Running Disk I/O test...")
        try:
            disk_results = run_test(disk_io_test, "Disk I/O Test", repeat=args.repeat, number=args.number)
            results.append(disk_results)
        except Exception as e:
            results.append({'name': "Disk I/O Test", 'error': str(e)})

    # Format the output
    output_lines = []
    for res in results:
        output_lines.append(f"Test: {res.get('name', 'Unknown')}")
        if 'error' in res:
            output_lines.append(f"Error: {res['error']}")
        else:
            output_lines.append(f"Times: {res['times']}")
            output_lines.append(f"Mean: {res['mean']:.4f} seconds")
            output_lines.append(f"Median: {res['median']:.4f} seconds")
            output_lines.append(f"Std Dev: {res['std_dev']:.4f} seconds")
        output_lines.append("")  # Blank line for separation

    output_text = "\n".join(output_lines)

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
