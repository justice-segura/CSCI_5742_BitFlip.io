import os
import gc
import random
import shutil
import time
import numpy as np

def test_cpu_performance():
    """
    Baseline load test for CPU performance.
    Generates random numbers and multiplies them repeatedly.
    """
    print("Starting CPU performance test...")
    start_time = time.time()
    result = 1
    for _ in range(10**7):  # Adjust the range for desired load
        num = random.random()
        result *= num if result != 0 else 1  # Avoid zero multiplication
    end_time = time.time()
    print(f"CPU performance test completed in {end_time - start_time:.2f} seconds.")

def test_memory_performance():
    """
    Memory Performance Test:
    This test allocates a large array of approximately 2GB using np.uint8 (each element is 1 byte).
    It then performs 100,000 random read/write operations on the array.
    
    WARNING: This test requires at least 2GB of free memory.
    """
    print("Starting memory test...")
    # Define the total size in bytes (2GB).
    size_bytes = 2 * 1024 * 1024 * 1024  # 2GB in bytes
    num_elements = size_bytes  # Since np.uint8 uses 1 byte per element
    try:
        # Allocate the array; this may raise a MemoryError if insufficient memory is available.
        arr = np.zeros(num_elements, dtype=np.uint8)
    except MemoryError:
        print("Memory allocation failed. Not enough memory available for the test.")
        return

    start_time = time.time()
    for _ in range(100_000):
        idx = random.randint(0, num_elements - 1)
        # Perform a read-modify-write operation (incrementing the byte value modulo 256)
        arr[idx] = (arr[idx] + 1) % 256
    end_time = time.time()
    print(f"Memory test completed in {end_time - start_time:.2f} seconds.")
    # Clean up the allocated array
    del arr
    # Optionally, you can force garbage collection to free up memory immediately.
    gc.collect()
    # Print a message indicating completion
    # and the amount of memory used.
    print(f"Memory test completed. Allocated {size_bytes / (1024 * 1024):.2f} MB.")

def test_disk_io_performance():
    """
    Disk I/O performance test.
    Copies a large 5GB file from one directory to another.
    """
    print("Starting disk I/O performance test...")
    source_file = "large_test_file.bin"
    destination_file = "large_test_file_copy.bin"

    # Create a 5GB file if it doesn't exist
    if not os.path.exists(source_file):
        print("Creating a 5GB test file...")
        with open(source_file, "wb") as f:
            f.write(os.urandom(5 * 1024 * 1024 * 1024))  # 5GB of random data

    start_time = time.time()
    shutil.copy(source_file, destination_file)
    end_time = time.time()

    print(f"Disk I/O performance test completed in {end_time - start_time:.2f} seconds.")

    # Clean up the copied file
    if os.path.exists(destination_file):
        os.remove(destination_file)

if __name__ == "__main__":
    test_cpu_performance()
    test_memory_performance()
    test_disk_io_performance()