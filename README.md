stress-ng --vm 1 --vm-bytes 100% --vm-keep --timeout 600s

free -m for memory usage

su for access to run the python scripts

Steps taken for raid environment:                                                         
                                                                                          
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
