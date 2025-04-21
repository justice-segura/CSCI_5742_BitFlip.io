# Investigating NVMe as an Alternative to RAM
## Repository Outline
```
.
├── README.md
├── output (Directory Storing all executed runs with images and output)
│   ├── run_20250413_152949 (Baseline Test with Swapspace)
│   │   ├── graphs
│   │   │   ├── comparison_bar_chart.png
│   │   │   ├── cpu_test_line.png
│   │   │   ├── disk_copy_test_line.png
│   │   │   ├── disk_read_test_line.png
│   │   │   ├── disk_write_test_line.png
│   │   │   └── memory_test_line.png
│   │   ├── results.csv
│   │   └── write-up.md
│   ├── run_20250413_154651 (Baseline Test with no Swapspace and Memory Stress Tested)
│   │   ├── graphs
│   │   │   ├── comparison_bar_chart.png
│   │   │   ├── cpu_test_line.png
│   │   │   ├── disk_copy_test_line.png
│   │   │   ├── disk_read_test_line.png
│   │   │   ├── disk_write_test_line.png
│   │   │   └── memory_test_line.png
│   │   ├── results.csv
│   │   └── write-up.md
│   ├── run_20250420_210823 (Test1: RAID0 Swapspace Test and Memory Stress Tested)
│   │   ├── graphs
│   │   │   ├── comparison_bar_chart.png
│   │   │   ├── cpu_test_line.png
│   │   │   ├── disk_copy_test_line.png
│   │   │   ├── disk_read_test_line.png
│   │   │   ├── disk_write_test_line.png
│   │   │   └── memory_test_line.png
│   │   ├── results.csv
│   │   └── write-up.md
│   └── run_20250420_211500 (Test1: RAID0 Swapspace Test and Memory Stress Tested)
│       ├── graphs
│       │   ├── comparison_bar_chart.png
│       │   ├── cpu_test_line.png
│       │   ├── disk_copy_test_line.png
│       │   ├── disk_read_test_line.png
│       │   ├── disk_write_test_line.png
│       │   └── memory_test_line.png
│       ├── results.csv
│       └── write-up.md
└── test_bed_script.py (Script containing all functions to execute the test)
```

## test_bed_script.py Description
<TBD>

# Test Setup
## Steps taken for raid environment:                                                         
                                                                                          
1. Go into su privilege                                                                   
        `su`                                                                              
1. Set raid0 enviornment                                                                  
        `modprobe raid0`                                                                  
1. Set raid0 module to load every boot                                                    
        `echo raid0 >> /etc/modules-load.d/raid0.conf`                                    
1. Find Paritions that currently exist                                                    
        `fdisk -l`                                                                        
1. Find `/dev/nvme1n1` which isn't used and use that for the next command                 
1. Run `fdisk /dev/nvme1n1` which will open the commands to change the disk               
1. Create a new partition using `n` and `2` for booting and partiioning software          
1. Select partition Type `p` Primary Partition and choose 1                               
1. Use the full size of the disk which should be default                                  
1. Change partition type to Linux RAID AutoDetect                                         
        `t` and then `fd`                                                                 
1. Write the changes                                                                      
        `w`                                                                               
1. Confirm changes were made with `fdisk -l`                                              
1. Create RAID0 Array                                                                     
        `mdadm --create /dev/md0 --level=0 --raid-devices=1 /dev/nvme1n1p1 --force`       
1. Confirm there is nothing in the swap table                                             
        `cat /proc/swaps`                                                                 
1. Make Swap Space from the newly created RAID0 partition                                 
        `mkswap /dev/md0`                                                                 
1. Swap Space on for the partition                                                        
        `swapon /dev/md0`                                                                 
1. Confirm the swapspace is using by looking at the swap file                             
        `cat /proc/swaps`

## Running the Tests
1. Have memory stressed so it can't be used for swap space (Terminal A)
        `stress-ng --vm 1 --vm-bytes 100% --vm-keep --timeout 600s`
1. Confirm the Memory is fully utilized (Terminal B)
        `free -m`
1. Navigate to Python Script
        `cd /Documents/CSCI_5742_BitFlip.io`
1. Run `su` to get privilege
        `su` (password `root`)
1. Run the python script
        `python test_bed_script.py`
1. Once script has completed, found it easiest to push the changes to GitHub to see the results in Markdown

## Pushing to GitHub
Configuring GitHub credentials to work was a bit of a pain.  Had to create a personal access token with all the credentials and then when pushing, put in username like normal and then the token as the password. This was the easiest route I had found.
