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
    # Define 2GB in bytes (using uint8 -> 1 byte per element)
    size_bytes = 2 * 1024 * 1024 * 1024  
    num_elements = size_bytes
    try:
        arr = np.zeros(num_elements, dtype=np.uint8)
    except MemoryError:
        raise MemoryError("Memory allocation failed. Not enough memory available for the test.")
    for _ in range(100_000):
        idx = random.randint(0, num_elements - 1)
        # Increment the value modulo 255
        arr[idx] = (arr[idx] + 1) % 255
    # Cleanup
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
            # os.urandom may take a while to generate 5GB. Adjust if necessary.
            f.write(os.urandom(5 * 1024 * 1024 * 1024))
    shutil.copy(source_file, destination_file)
    if os.path.exists(destination_file):
        os.remove(destination_file)

def run_test(test_func, test_name, repeat=5):
    """
    Run a given test function using timeit.repeat() and compute statistical measures.
    """
    # Each "repeat" runs the test function (number=1 execution per repeat)
    times = timeit.repeat(test_func, repeat=repeat, number=1)
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
    args = parser.parse_args()

    results = []

    if "cpu" in args.tests:
        print("Running CPU test 5 times...")
        try:
            cpu_results = run_test(cpu_test, "CPU Test")
            results.append(cpu_results)
        except Exception as e:
            results.append({'name': "CPU Test", 'error': str(e)})

    if "memory" in args.tests:
        print("Running Memory test 5 times...")
        try:
            memory_results = run_test(memory_test, "Memory Test")
            results.append(memory_results)
        except MemoryError as e:
            results.append({'name': "Memory Test", 'error': str(e)})

    if "disk" in args.tests:
        print("Running Disk I/O test 5 times...")
        try:
            disk_results = run_test(disk_io_test, "Disk I/O Test")
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
