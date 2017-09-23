import subprocess
import json
import os
import argparse

'''
This script fixes up VMware images to prepare them for upload to Azure.

It was created because Azure requires:
"All of the VHDs must have sizes that are multiples of 1 MB.""

See: https://docs.microsoft.com/en-us/azure/virtual-machines/linux/create-uplo
ad-generic#general-linux-installation-notes for more information.

It only takes a single argument:
    * filename - specifies the VM filename to fix

It will output a .vhd file as the result.
'''

def get_args():
    '''Gets arguments for the rest of the script'''
    parser = argparse.ArgumentParser(description='Fixes VMware images ')
    parser.add_argument('-f', '--filename',
                        type=str,
                        help='VMDK filename',
                        required=True)
    args = parser.parse_args()

    return args

def get_size(name):
    '''Gets the size of the VMDK in bytes'''
    result = subprocess.check_output(["qemu-img","info","-f","vmdk","--output"
    ,"json",name])

    result_json = json.loads(result)

    return result_json['virtual-size']

def calc_disk(size):
    '''Takes the disk size and adds 1 MB to it'''
    mb = 1024 * 1024
    new_size = ((size / mb + 1) * mb)

    return new_size

def convert_to_raw(name):
    '''Converts the disk to raw format so we can resize it'''
    subprocess.check_output(["qemu-img","convert","-f","vmdk","-O","raw",
    name,name+".raw"])

def resize_disk(name,new_size):
    '''Resizes the disk with the result from calc_disk(size)'''
    subprocess.check_output(["qemu-img","resize","-f","raw",name+".raw",
    new_size])

def convert_to_vhd(name):
    '''Converts the disk to VHD. Note Azure doesn't work with vhdx'''
    subprocess.check_output(["qemu-img","convert","-f","raw","-O","vpc",
    "-o","subformat=fixed,force_size",name+".raw",name+".vhd"])

    os.remove(name+".raw") # Removes the temporary raw file

def main():
    # Gather arguments
    args = get_args()

    # Gets the size in bytes
    size = get_size(args.filename)

    # Adds 1MB to size to get new_size
    new_size = str(calc_disk(size))

    print "Size of VM is: " + str(size) + " bytes"
    print "New size of VM (Plus 1MB): " + str(new_size) + " bytes"

    # Convert to raw
    convert_to_raw(args.filename)

    # Resize disk to new boundary
    resize_disk(args.filename,new_size)

    # Convert to VHD
    convert_to_vhd(args.filename)

 __name__ == '__main__':
    main()
