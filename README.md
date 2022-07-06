# Automation Demo

---
###Demo 1

####demo1-1-backup.py <br>

The purpose of this script is to demonstrate backing up the devices in the demo lab topology.<br>

To execute, just run the command followed by a file with the hostnames in it: <br><br>
&nbsp;&nbsp;&nbsp;Example: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python demo1-1-backup.py *filename.ext*<br>

----
### Demo 2

####demo1-2-inventory.py

The purpose of this script is to demonstrate taking an inventory of the devices, using the same input file as demo1-1.<br><br>
We will capture and report on the following:
- Hostname of device
- Hardware 
- Serial Number
- Software Version
- Uptime information
- Interfaces with IP and status 


&nbsp;&nbsp;&nbsp;Example: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python demo1-2-backup.py *filename.ext*<br>

---
### Demo 3

####demo1-3-lldp.py

The purpose of this script is to demonstrate pulling the lldp neighbor information from each device.  Once <br> 
we have that data, we will then parse it out using NTCTemplates to pull remote hostname and interface from the output.<BR>
<br>Once we have that, we will construct a configuration file for each router that will configure the interface with the <br>
remote information and push that config to the device.<br>
<br>We will also show the before interface descriptions and the after interface descriptions to show the changes. 
<br><br>
&nbsp;&nbsp;&nbsp;Example: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python demo1-3-backup.py *filename.ext*<br>
---

### Demo 4

#### demo1-4-commands.py

The purpose of this script is to allow you a way to provide a list of devices and commands.  The list will then iterate<br>
over the commands and save the output to a file.  This should be way for you to gather lots of data quickly.
<br><br>
&nbsp;&nbsp;&nbsp;Example: <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;python demo1-3-commands.py *devices.txt* *commands.txt* <br>


