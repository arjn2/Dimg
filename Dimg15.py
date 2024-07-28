import os
import subprocess
import sys
from tqdm import tqdm

# Global variables for disk image paths and selected partition
disk_image_path = None
new_disk_image_path = None
path = None
selected_partition = None
loop_device = None

# Helper function to run shell commands
def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}\n{result.stderr}")
    return result.stdout

def set_disk_location():
    global disk_image_path, path
    while True:
        disk_image_path = input("Enter the path to the disk image: ").strip()
        if os.path.exists(disk_image_path) and os.path.isfile(disk_image_path):
            break
        else:
            print("The specified disk image path does not exist or is not a file. Please re-enter.")

    print(f"Disk image path set to: {disk_image_path}")

    if new_disk_image_path is None:
        print("New disk image path is not set. Please set it.")
        prompt = input("To ignore and overwrite enter (i-ignore/n-no) ").strip().lower()
        if prompt == 'i':
            path = disk_image_path
        else:
            set_disk_copy_location()

    return main_menu()

def set_disk_copy_location():
    global new_disk_image_path, path
    while True:
        new_disk_image_path = input("Enter the path to the new disk image: ").strip()
        if os.path.exists(os.path.dirname(new_disk_image_path)):
            break
        else:
            print("The specified new disk image path does not exist. Please re-enter.")
    
    print(f"New disk image path set to: {new_disk_image_path}")
    path = new_disk_image_path

    qn = input("Do you want to start copying disk now (y/n): ").strip().lower()
    if qn == 'y':
        disk_copy()
    else:
        pass
    return main_menu()

def disk_copy():
    new_disk_image_path = get_new_image_path(new_disk_image_path)
    total_size = os.path.getsize(disk_image_path)
    with open(disk_image_path, 'rb') as src, open(new_disk_image_path, 'wb') as dst:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Copying to {new_disk_image_path}") as pbar:
            while True:
                buf = src.read(16 * 1024)
                if not buf:
                    break
                dst.write(buf)
                pbar.update(len(buf))

def get_new_image_path(original_path):
    base, ext = os.path.splitext(original_path)
    counter = 1
    new_path = f"{base}_new{counter}{ext}"
    while os.path.exists(new_path):
        counter += 1
        new_path = f"{base}_new{counter}{ext}"
    return new_path

def reset_path():
    global disk_image_path, new_disk_image_path, path, selected_partition, loop_device
    disk_image_path = None
    new_disk_image_path = None
    path = None
    selected_partition = None
    loop_device = None
    return main_menu()

def display_paths():
    print("\n----------------------------------------")
    if disk_image_path:
        print(f"Disk image path: {disk_image_path}")
    else:
        print("Disk image path: Not set")
    if new_disk_image_path:
        print(f"New disk image path: {new_disk_image_path}")
    else:
        print("New disk image path: Not set")
    print("----------------------------------------")

def setup_loop_device():
    global loop_device, path
    loop_device = run_command("sudo losetup -f").strip()
    run_command(f"sudo losetup -P {loop_device} {path}")

def teardown_loop_device():
    global loop_device
    if loop_device:
        run_command(f"sudo kpartx -d {loop_device}")
        run_command(f"sudo losetup -d {loop_device}")
        loop_device = None

def select_partition():
    global path, selected_partition, loop_device
    try:
        setup_loop_device()
        if sys.platform.startswith("linux"):
            output = run_command(f"sudo fdisk -l {loop_device}")
            print(output)
        else:
            print("Unsupported OS.")
        
        # Display partitions with selection option
        partitions = [line for line in output.splitlines() if f"{loop_device}p" in line]
        for idx, line in enumerate(partitions):
            print(f"{idx}. {line}")
        
        selection = input("Enter the number of the partition to select (e.g., 0, 1): ").strip()
        if selection.isdigit() and 0 <= int(selection) < len(partitions):
            selected_partition = partitions[int(selection)].split()[0]
            print(f"Selected partition: {selected_partition}")
        else:
            print("Invalid selection. No partition selected.")
            selected_partition = None
    except RuntimeError as e:
        print(e)
    explore_disk_image()

def explore_disk_image():
    global selected_partition
    if path is None:
        print("Disk image path is not set. Please set it first.")
        main_menu()
        return
    
    while True:
        display_paths()
        if selected_partition:
            print(f"\nSelected Partition: {selected_partition}\n")
        print("\nExplore Disk Menu:")
        print("1. List partitions")
        print("2. Select partition")
        print("3. Resize partition")
        print("4. Resize file system")
        print("5. Explore with GParted")
        print("6. Create new reduced image")
        print("7. Back to main menu")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == '1':
            list_partitions()
        elif choice == '2':
            select_partition()
        elif choice == '3':
            if not selected_partition:
                print("No partition selected. Please select a partition first.")
            else:
                resize_partition()
        elif choice == '4':
            if not selected_partition:
                print("No partition selected. Please select a partition first.")
            else:
                resize_file_system()
        elif choice == '5':
            if not selected_partition:
                print("No partition selected. Please select a partition first.")
            else:
                explore_with_gparted()
        elif choice == '6':
            if not selected_partition:
                print("No partition selected. Please select a partition first.")
            else:
                new_reduced_disk()
        elif choice == '7':
            main_menu()
            break
        else:
            print("Invalid choice. Please try again.")

def resize_file_system():
    global selected_partition
    if not selected_partition:
        print("No partition selected. Please select a partition first.")
        return explore_disk_image()
    
    try:
        

        # Check the partition type
        partition_info = run_command(f"sudo blkid {selected_partition}")
        if "TYPE=" not in partition_info or "ext" not in partition_info:
            print("Unsupported file system type. Only ext2/ext3/ext4 are supported.")
            return explore_disk_image()

        # Check and repair the file system
        run_command(f"sudo e2fsck -f -y {selected_partition}")

        # Check if the partition is mounted
        try:
            mount_info = run_command(f"mount | grep {selected_partition}")
            if mount_info:
                # Unmount the partition if it's mounted
                run_command(f"sudo umount {selected_partition}")
        except RuntimeError as e:
            print(f"Warning: {selected_partition} might not be mounted: {e}")

        # Resize the file system
        new_size = input("Enter the new size for the file system (e.g., 14G): ").strip()
        run_command(f"sudo resize2fs {selected_partition} {new_size}")

        print(f"File system on {selected_partition} resized to {new_size}")

    except RuntimeError as e:
        print(e)
    
    explore_disk_image()

def resize_partition():
    global selected_partition
    if not selected_partition:
        print("No partition selected. Please select a partition first.")
        return explore_disk_image()
    
    try:
        new_size = input("Enter the new size for the partition (e.g., 14G): ").strip()

        # Resize the partition
        run_command(f"sudo parted {loop_device} resizepart {selected_partition[-1]} {new_size}")

        print(f"Partition {selected_partition} resized to {new_size}")

    except RuntimeError as e:
        print(e)
    
    explore_disk_image()

def explore_with_gparted():
    global path
    try:
        setup_loop_device()
        if sys.platform.startswith("linux"):
            run_command(f"sudo gparted {loop_device}")
        else:
            print("GParted is only supported on Linux.")
    except RuntimeError as e:
        print(e)
    finally:
        teardown_loop_device()
    explore_disk_image()

def new_reduced_disk():
    global path
    try:
        setup_loop_device()

        # Get end sector of the last partition
        fdisk_output = run_command(f"sudo fdisk -l {loop_device}")
        print(fdisk_output)

        # Parse the fdisk output to find the end sector of the last partition
        lines = fdisk_output.strip().split('\n')
        end_sector = None
        for line in lines:
            if line.startswith(loop_device):
                parts = line.split()
                if len(parts) > 2 and parts[2].isdigit():
                    end_sector = int(parts[2])

        if end_sector is None:
            raise RuntimeError("Failed to determine the end sector of the last partition.")

        # Calculate the new image size
        sector_size = 512
        new_image_size = (end_sector + 1) * sector_size

        # Create the new reduced image
        new_image_path = get_new_image_path(path)
        run_command(f"dd if={path} of={new_image_path} bs=512 count={end_sector + 1}")

        print(f"New reduced image created at {new_image_path}")

    except RuntimeError as e:
        print(e)
    finally:
        teardown_loop_device()

    explore_disk_image()

def list_partitions():
    global path
    try:
        setup_loop_device()
        if sys.platform.startswith("linux"):
            output = run_command(f"sudo fdisk -l {loop_device}")
            print(output)
        else:
            print("Unsupported OS.")
    except RuntimeError as e:
        print(e)
    finally:
        teardown_loop_device()
    explore_disk_image()

def main_menu():
    while True:
        display_paths()
        print("\nMain Menu:")
        print("1. Set disk location")
        print("2. Set disk copy location")
        print("3. Explore disk")
        print("4. Reset paths")
        print("5. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == '1':
            set_disk_location()
        elif choice == '2':
            set_disk_copy_location()
        elif choice == '3':
            explore_disk_image()
        elif choice == '4':
            reset_path()
        elif choice == '5':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
