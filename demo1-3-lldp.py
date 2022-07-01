import os
import sys
from datetime import datetime
from signal import signal, SIGINT
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
import getpass
import pwinput
from ntc_templates.parse import parse_output


# Logging configs if we need to run this on
def enablelogging():
    import logging
    logging.basicConfig(filename='debuging.log', level=logging.DEBUG)

# Signal handler to watch for ctrl-break - and if entered to exit the script.
def handler(signal_received, frame):
    os.system('cls' if os.name == 'nt' else 'clear')
    print('\n\nBreak detected, exiting gracefully.\n')
    print('Have a nice day!\n\n')
    exit(0)

# Clear the screen and print welcome banner
def welcome():
    os.system('cls' if os.name == 'nt' else 'clear')
    print('***********************')
    print('*   demo1-3-lldp.py   *')
    print(f'* {dt_string} *')
    print('***********************')
    print('\n')

# Get the current date and time, and then format at MM/DD/YY HH:MM:SS
def timeinfo():
    global dt_string, dt_save
    now = datetime.now()
    dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
    dt_save = now.strftime("  %b-%d  %H-%M")
    print(dt_string)
    return(dt_string)

# Pause section used for troubleshooting only
def time2pause():
    pausing = input('Press any key to continue...')
    return

# Read commands passed from command line
# Looking for the file that contains the Cisco devices we want to connect to
def getarg(argv=sys.argv[1:]):
    global datafile
    # Checking to make sure the data file was passed
    if len(argv) != 1:
        print('Please enter a command line variable containing the devices you want to connect to.\n\n\tExample:\tdemo1-1-backup.py routers.txt')
        sys.exit()
    else:
        # We will try to open the file passed, if its invalid - will raise and print error returned.
        try:
            with open(argv[0]) as f:
                datafile = f.readlines()
        except Exception as e:
            print(f'An error occurred.\n\n{e}')

    return datafile


# Get username and password information
def userdata():
    global getuser, getpwd1, envuser
    envuser = getpass.getuser()
    getuser = (input(f'Enter your username, or press enter for {envuser}: ') or envuser)
    getpwd1 = pwinput.pwinput('Please enter your password: ')
    getpwd2 = pwinput.pwinput('Please verify your password: ')
    print('\n')

    # Checking to make sure passwords match - prevents invalid password login attempts
    while getpwd1 != getpwd2:
        print('Passwords do not match, please try again...\n')
        getpwd1 = pwinput.pwinput('Please enter your password:')
        getpwd2 = pwinput.pwinput('Please verify your password:')
        print('\n')

    # Print the output from above - used for debugging only
    #print(f'User {getuser}\nPass {getpwd1}')

    return(getuser, getpwd1)

# Perform the lldp neighbor and update the configuration.
def interfaceupdate(datafile, getuser, getpwd1, errorcount, successcount):

    # Create empty list that we can append the hostnames to
    devicelist = []

    # Read the input data file, assign it to connecthost
    # Strip off any carriage returns that may have ben read in as well
    for line in datafile:
        # Strip carriage return from line read fromfile
        hostconnect = line.strip()

        # Checking for a blank line as it would have two characters
        if len(line) < 2:
            print('Looks like a blank line, skipping.\nPlease check input file.\n')
            continue
        print(f'\nAttempting to connect to {hostconnect}...')

        devicelist.append(hostconnect)

        # Defining connection strings
        cisco1 = {
            "device_type": "cisco_ios",
            "host": hostconnect,
            "username": getuser,
            "password": getpwd1,
        }

        errorlog = open('demo1-3-errors.log', 'w')
        header_string = (f'! Created on {dt_string} by {envuser} \n')
        errorlog.write(header_string)
        errorlog.write('-' * len(header_string) + '\n')

        # Connect to the host specified and pull the hostname.  This will be used to create the output file.
        command = "show run | inc hostname"
        try:
            with ConnectHandler(**cisco1) as net_connect:
                output = net_connect.send_command(command)
                hostname = output.split(' ')
                # print(hostname[1])
                tempvar = hostname[1].split('-')

                savefile = open(hostname[1] + '-lldp.cfg', 'w')
                savefile.write(header_string)
                savefile.write('! ' + '-' * len(header_string) + '\n')

                # Call out to get the interface descriptions currently configured and report them to user
                print('Current interface descriptions...\n')
                showinterfaces(net_connect)

                # Run the show lldp neighbor command
                command = 'show lldp nei'
                output = net_connect.send_command(command)
                show_lldp = parse_output(platform="cisco_ios", command="show lldp neighbors", data=output)
                #print(show_lldp)

                # Parse the output of show lldp and identify local interface, neighbor description, and neigbhbor interface and then write this to a file for a config
                for lldpnei in show_lldp:
                    savefile.write(f'\ninterface {lldpnei["local_interface"]}\n desc Connection to {lldpnei["neighbor"]} - {lldpnei["neighbor_interface"]}\n')

                savefile.close()

                # Set the  config file so that we can push it
                configfile = hostname[1] + '-lldp.cfg'

                successcount += 1

                # Push the config to the device
                print(f'Pushing configuration to {hostconnect}\n')
                output = net_connect.send_config_from_file(configfile)

                # Save the configuration to the device
                print(f'Saving configuration on {hostconnect}\n')
                output = net_connect.send_command('write mem')

                # Check to make sure the save was successful
                if 'OK' in output:
                    print('Config saved successfully\n')
                else:
                    print(f'You may need to manually save config on {hostconenct}.\n')

                # Display the updated interface descriptions
                print('Updated interface descriptions...\n')
                showinterfaces(net_connect)
                print('\n')

        # Error handling error for timeout, auth, etc issues.
        except NetMikoTimeoutException as err:
            errorentry = (f'Connettion timeout {err}')
            errorlog.write(errorentry)
            errorlog.write('-' * len(header_string) + '\n')
            print(errorentry)
            errorcount += 1
        # This is for auth failure and will cause the program to exit so to not lock out the users account.
        except NetMikoAuthenticationException as err:
            errorentry = (f'Authentication failed - {hostconnect} - {err}')
            errorlog.write(errorentry)
            errorlog.write('-' * len(header_string) + '\n')
            print(errorentry)
            autherror += 1
            if autherror >= 2:
                print('We have had two authentication errors.\n')
                print('\nPlease re-run and enter check password.\nPlease check log for any other errors.\n...exiting.')
                sys.exit()
            else:
                print('...first authentication error, continuing...\n')
        except ConnectionRefusedError as err:
            errorentry = (f"Connection Refused: {err}\n")
            print(errorentry)
            errorlog.write(errorentry)
            errorlog.write('-' * len(header_string) + '\n')
            errorcount += 1
        except TimeoutError as err:
            errorentry = (f"Connection TimedOut: {err}\n")
            print(errorentry)
            errorlog.write(errorentry)
            errorlog.write('-' * len(header_string) + '\n')
            errorcount += 1
        except Exception as err:
            errorentry = (f"Connection Error: {err}\n")
            print(errorentry)
            errorlog.write(errorentry)
            errorlog.write('-' * len(header_string) + '\n')
            errorcount += 1
            if 'Authentication to device failed' in err:
                print('Invalid password - exiting.')
                sys.exit()

    if errorcount >= 1:
        print(f'We had {errorcount} errors - please check error log\n')
    else:
        print(f'\n\nNo errors encountered.  Looks like a clean run!')
        errorlog.write(f'\n\nNo errors encountered.\n\nLooks like a clean run.\n')
        for item in devicelist:
            print('\t' + item)

    errorlog.close()

# Since we are using this a few times, set aside in its own function area
def showinterfaces(net_connect):
    command = 'show interfaces'
    output = net_connect.send_command(command)
    show_int = parse_output(platform="cisco_ios", command="show interfaces", data=output)
    # print(show_int)
    # Parse the output and display the interface and description
    for datapoint in show_int:
        # If the interface is Loopback0, skip it
        if datapoint['interface'] == 'Loopback0':
            pass

        # If the interface has no description ( lenght of 0 ) set the description to No description
        elif len(datapoint['description']) == 0:
            datapoint['description'] = "No description"
            print(f'\tInterface {datapoint["interface"]} has a description of {datapoint["description"]}')

        # Print the current description on the interface
        else:
            print(f'\tInterface {datapoint["interface"]} has a description of {datapoint["description"]}')

    print('\n')


if __name__ == '__main__':
    signal(SIGINT, handler)
    errorcount = 0
    successcount = 0
    enablelogging()
    timeinfo()
    welcome()
    getarg()
    userdata()
    interfaceupdate(datafile, getuser, getpwd1, errorcount, successcount)

