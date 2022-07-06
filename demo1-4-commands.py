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
    print('***************************')
    print('*   demo1-3-commands.py   *')
    print(f'*   {dt_string}   *')
    print('***************************')
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
# Looking for the file that contains the commands that we want to run against the host devices
def getarg(argv=sys.argv[1:]):
    global datafile,commandfile
    # Checking to make sure the data file was passed
    if len(argv) != 2:
        print('Please enter a command line variable containing the devices you want to connect to.\n\n\tExample:\tdemo1-4-commands.py routers.txt commands.txt\n')
        sys.exit()
    else:
        # We will try to open the file passed, if its invalid - will raise and print error returned.
        try:
            with open(argv[0]) as f:
                datafile = f.readlines()
        except Exception as e:
            print(f'An error occurred.\n\n{e}\n')

        # This is trying to load the commands
        try:
            with open(argv[1]) as f:
                commandfile = f.readlines()
        except Exception as e:
            print(f'An error has occured.\n\n{e}\n')

    return datafile, commandfile


# Get username and password information
def userdata():
    # This is prompting for the username and password - we are pulling the current logged in user and sett
    # that for default, unless a username is entered
    global getuser, getpwd1, envuser
    envuser = getpass.getuser()
    getuser = (input(f'Enter your username, or press enter for {envuser}: ') or envuser)

    # We are getting the password here, twice - so that we can verify that it matches
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
def runcommands(datafile, commandfile, getuser, getpwd1, errorcount, successcount):

    # Create empty list that we can append the hostnames to and another for the commands
    devicelist = []
    commandlist = []

    # Adding the commands to a list, easier to iterate over, yet not really necessary when I think about it
    for item in commandfile:
        commandlist.append(item)

    # Read the input data file, assign it to connecthost
    # Strip off any carriage returns that may have ben read in as well
    for line in datafile:
        # Strip carriage return from line read fromfile
        hostconnect = line.strip()
        hostoutput = open('output/' + hostconnect + '.log', 'w')

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

        # Creating an error-log in case of problems
        errorlog = open('output\demo1-4-errors.log', 'w')
        header_string = (f'! Created on {dt_string} by {envuser} \n')
        errorlog.write(header_string)
        errorlog.write('-' * len(header_string) + '\n')
        hostoutput.write(header_string)
        hostoutput.write('-' * len(header_string) + '\n')

        # Iterating over commands and sending them to the device via the runcommand section
        for item in commandfile:
            try:
                with ConnectHandler(**cisco1) as net_connect:
                    runcommand(net_connect, item, hostoutput)

            except Exception as err:
                print(errorentry)
                errorlog.write(errorentry)
                errorlog.write('-' * len(header_string) + '\n')


# Since we are using this a few times, set aside in its own function area
# This will use the open connection to the device and send the command that is iterated over
def runcommand(net_connect, command, hostoutput):
    print(f'Running {command}\n')
    hostoutput.write('\n' + '-' * 20 + '\n')
    hostoutput.write(command)
    output = net_connect.send_command(command)
    hostoutput.write(output)

# Main section of script
if __name__ == '__main__':
    signal(SIGINT, handler)
    errorcount = 0
    successcount = 0
    #enablelogging()
    timeinfo()
    welcome()
    getarg()
    userdata()
    runcommands(datafile, commandfile, getuser, getpwd1, errorcount, successcount)

