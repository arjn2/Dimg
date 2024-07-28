import os
import subprocess
import sys

# Global variables for disk image paths
disk_image_path = None
new_disk_image_path = None
path = None

# Helper function to run shell commands
def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}\n{result.stderr}")
    return result.stdout

def set_disk_location():
    global disk_image_path, path
    # disk_image_path = input("Enter the path to the disk image: ").strip()
    # print(f"Disk image path set to: {disk_image_path}")
    while True:
        disk_image_path = input("Enter the path to the disk image: ").strip()
        if os.path.exists(disk_image_path):
                if os.path.isfile(disk_image_path):
                    break
                else:
                    print("The specified file not exist, pls recheck it,,")
        else:
            print("The specified disk image path does not exist. Please re-enter.")

    if new_disk_image_path is None:
        print("New disk image path is not set. Please set it.")
        prompt = input("To Ignore and overwrite enter (i-ignore/n-no) ").strip().lower()
        if prompt == 'i':
            path = disk_image_path
        else:
            set_disk_copy_location()

    return main_menu()

def set_disk_copy_location():
    global new_disk_image_path, path
    new_disk_image_path = input("Enter the path to the new disk image: ").strip()
    print(f"New disk image path set to: {new_disk_image_path}")
    path = new_disk_image_path

    qn=input("Do you want to start copying disk now (y/n):")
    if(qn=='y'):
        disk_copy()
    else:
        pass
    return main_menu()

def disk_copy():
    new_disk_image_path = get_new_image_path(os.path.join(new_disk_image_path, os.path.basename(disk_image_path)))
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
    if original_path == new_disk_image_path:
        counter = 1
        new_path = f"{base}_new{counter}{ext}"
        while os.path.exists(new_path):
            counter += 1
            new_path = f"{base}_new{counter}{ext}"
    else:
        new_path = f"{base}"

    return new_path

def reset_path():
    global disk_image_path,new_disk_image_path,path
    disk_image_path = None
    new_disk_image_path = None
    path = None
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

def explore_disk_image():
    if path is None:
        print("Disk image path is not set. Please set it first.")
        main_menu()
        return
    
    while True:
        display_paths()
        print("\nExplore Disk Menu:")
        print("1. List partitions")
        print("2. Resize partition")
        print("3. Explore with GParted")
        print("4. Back to main menu")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == '1':
            list_partitions()
        elif choice == '2':
            resize_partition()
        elif choice == '3':
            explore_with_gparted()
        elif choice == '4':
            main_menu()
            break
        else:
            print("Invalid choice. Please try again.")

def list_partitions():
    global path
    try:
        if sys.platform.startswith("linux"):
            output = run_command(f"sudo fdisk -l {path}")
            print(output)
        elif sys.platform.startswith("win"):
            script_path = os.path.join(os.getenv('TEMP'), 'list_partitions.txt')
            with open(script_path, 'w') as script:
                script.write(f'Select vdisk file="{path}"\n')
                script.write('detail vdisk\n')
                script.write('exit\n')
            output = run_command(f"diskpart /s {script_path}")
            print(output)
            os.remove(script_path)
        else:
            print("Unsupported OS.")
    except RuntimeError as e:
        print(e)
    explore_disk_image()

def resize_partition():
    global path
    try:
        partition_number = input("Enter the partition number to resize: ").strip()
        new_size = input("Enter the new size (e.g., 17G): ").strip()
        
        if sys.platform.startswith("linux"):
            run_command(f"sudo parted {path} resizepart {partition_number} {new_size}")
        elif sys.platform.startswith("win"):
            script_path = os.path.join(os.getenv('TEMP'), 'resize_partition.txt')
            with open(script_path, 'w') as script:
                script.write(f'Select vdisk file="{path}"\n')
                script.write(f'Select partition {partition_number}\n')
                script.write(f'Resize partition {partition_number} size={new_size}\n')
                script.write('exit\n')
            run_command(f"diskpart /s {script_path}")
            os.remove(script_path)
        else:
            print("Unsupported OS.")
        
        print(f"Partition {partition_number} resized to {new_size} in {path}.")
    except RuntimeError as e:
        print(e)
    explore_disk_image()

# def explore_with_gparted():
#     global path
#     try:
#         if sys.platform.startswith("linux"):
#             # Setup loop device
#             # loop_device = run_command(f"sudo losetup -Pf {path}").strip()
#             # run_command(f"sudo partprobe {loop_device}")
#             # run_command(f"sudo kpartx -av {loop_device}")
#             # run_command(f"sudo gparted {loop_device}")
#             # run_command(f"sudo kpartx -d {loop_device}")
#             # run_command(f"sudo losetup -d {loop_device}")
#             loop_device = run_command("sudo losetup -f").strip()
#             run_command(f"sudo losetup -P /dev/loop0 {path}")
#             run_command(f"sudo partprobe /dev/loop0")
#             run_command(f"sudo kpartx -av /dev/loop0")
#             run_command(f"sudo gparted /dev/loop0")
#             run_command(f"sudo kpartx -d /dev/loop0")
#             run_command(f"sudo losetup -d /dev/loop0")
#         else:
#             print("GParted is only supported on Linux.")
#     except RuntimeError as e:
#         print(e)

#         try:
#             run_command(f"sudo kpartx -d {loop_device}")
#             run_command(f"sudo losetup -d {loop_device}")
#         except Exception as cleanup_error:
#             print(f"Cleanup failed: {cleanup_error}")
#     explore_disk_image()

def explore_with_gparted():
    global path
    loop_device = None
    try:
        if sys.platform.startswith("linux"):
            # Find an available loop device
            loop_device = run_command("sudo losetup -f").strip()
            run_command(f"sudo losetup -P {loop_device} {path}")
            run_command(f"sudo partprobe {loop_device}")
            run_command(f"sudo kpartx -av {loop_device}")
            run_command(f"sudo gparted {loop_device}")
            run_command(f"sudo kpartx -d {loop_device}")
        else:
            print("GParted is only supported on Linux.")
    except RuntimeError as e:
        print(e)
    finally:
        # Ensure cleanup if something goes wrong or after GParted is closed
        if loop_device:
            try:
                run_command(f"sudo losetup -d {loop_device}")
            except RuntimeError as cleanup_error:
                print(f"Cleanup failed: {cleanup_error}")
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
        elif choice=='5':
            disk_copy()
        elif choice=='6':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
