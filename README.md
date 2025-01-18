# Forensic_Image_File_Compressor

This is a script to compress training forensic image files (.i.e E01) and zero out all the unnecessary files.
Create a text file (Files_Folders_to_Keep.txt) and on each line, enter the file path, file extension and/or folder path of the items you want to KEEP.  
The script will copy the items identified in the text file and all the other files will be copied, but will have a zero byte file size.

Notes on the Files_Folders_to_Keep.txt:
\Windows\System32\config\  will copy the contents on the folder
\Windows\System32\contig\SAM will only copy the SAM file
\Windows\System32\CONFIG\   will not work as it is case sensitive.
\Windows\System32\config  will treat "config" as a file not a folder

How to use this.

Download Arsenal Image Mounter https[://]arsenalrecon.com/products/arsenal-image-mounter

Run Arsenal Image Mounter, mount your source forensic image file.  Make note of the volume letter assigned.

Once mounted, note the size of the allocated data.

Create a VHD the size of the allocated data.  Format it and mount it.  Make note of the volume letter assigned.

Run the script with administration privileges.   

Enter in the source volume, destination volume and the text file with the items you want to keep.

Once done, unmount the VHD and create a forensic image of the VHD.  You can also bitlocker the VHD to enhance your training, before you convert it to an E01.
