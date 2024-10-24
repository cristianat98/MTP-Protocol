# MTP-Protocol
Repository to save the protocol for the MTP project

# Steps for installing the script

# Steps for running the Script
Mount USB (TX/RX)
sudo fdisk -l (check if the disk is sda/sdb...)
sudo mount /dev/sda /mnt/usb

TX
cd /home/<user>/mtp/QM_Test
sudo cp /mnt/usb/<name>.txt Fitxer.txt
sudo python3 QM_TestB.py
0

RX
cd /home/<user>/mtp/QM_Test
sudo python3 QM_TestB.py
1

After receive file:
RX
sudo cp _file_received.txt /mnt/usb

Unmount USB (TX/RX)
sudo umount /mnt/usb
