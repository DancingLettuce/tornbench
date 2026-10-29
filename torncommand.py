"""This filename is torncommand.py"""

import argparse   
from pathlib import Path
import sys  
import csv

def init_argparse():
    parser = argparse.ArgumentParser()
    epilog=""">>Torn Command Tool"""
    description = ('cli')
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(
            description=description,
            epilog=epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            prog="torncommand.py"  # Explicitly set the program name for help messages
            )
    parser.add_argument(
            'command',
            type=str,
            nargs='?',
            help="""The command to execute  
        """
        )
    parser.add_argument(
            'param1',
            type=str,
            nargs='?',
            help="The parameter for the command ."
        )
    parser.add_argument(
            'param2',
            type=str,
            nargs='?',
            help="The parameter for the command ."
        )
    parser.add_argument('--filename', help='filename to parse')
    parser.add_argument("--debug",  action="store_true",   help="Show the debug logs")
    parser.add_argument("--truncate",  action="store_true",   help="Truncate the target first")
    parser.add_argument("--testrun",  action="store_true",   help="This is a testrun")
    parser.add_argument("--interactive",  action="store_true",   help="Interactive to get input")
    parser.add_argument("--uselocallist",  action="store_true",   help="Use value of lib_localtest.locallist")
    parser.add_argument(
        "--configfile", 
        type=Path, # Argparse will automatically convert the string input to a Path object
        default=DEFAULT_CONFIG_PATH,
        help="Path to the TOML configuration file."
        )
    #ARGS = parser.parse_args()
    ARGS, unknown = parser.parse_known_args()
    # Convert the list of unknown args into a dictionary
    # This assumes the format is strictly --key value --key2 value2
    arbitrary_args = {}
    for i in range(0, len(unknown), 2):
        if unknown[i].startswith('--'):
            # Strip the '--' from the key
            key = unknown[i].lstrip('-')
            # Assign the next item as the value
            value = unknown[i+1] if (i + 1) < len(unknown) else True
            arbitrary_args[key] = value
    return ARGS,  arbitrary_args

TOML_STRING="""# Auto-generated default configuration
    DATABASE_NAME = ""
    DATABASE_HOST = ""
    DATABASE_USER = ""
    DATABASE_PASSWORD = ""
    """ 
SCRIPT_DIR = Path(__file__).resolve().parent 
#DEFAULT_CONFIG_PATH = SCRIPT_DIR / "secrets.toml" # for a local secrets or config file
DEFAULT_CONFIG_PATH = SCRIPT_DIR.parent / "secrets" / "secrets.toml"
DEFAULT_LOG_PATH = SCRIPT_DIR / "log.txt"
ALLOWED_COMMANDS={
    'test':"--a test--", 
    }
  
ARGS, ARBITRARY_ARGS = init_argparse()
try:
    import tb_lib_helper_lib as helperlib 
    imports_lib_helper_lib = True
except Exception as e:
    print(f"CRITICAL ERROR: Can not import tb_lib_helper_lib {e}")
    imports_lib_helper_lib = False  
    sys.exit()


CONFIG = helperlib.init_secrets(toml_string=TOML_STRING,filename=ARGS.configfile) 
 
from datetime import datetime as dt_datetime, timedelta  , timezone as dt_timezone 
import subprocess
import json 
import os  
import getpass



def main():
    tdiff = helperlib.TimeDiff()
    scriptlog = helperlib.ScriptLog()   
    scriptlog.print_summary()  
    
    args_command = ARGS.command 
    args_param1 = ARGS.param1
    args_param2 = ARGS.param2
    
    if args_command and args_command.startswith('*'):
        allowed_commands_str = '\n** '.join(
            f"{key} {value}" 
            for key, value in ALLOWED_COMMANDS.items()
            if args_command[1:].lower() in key.lower())
        print(f'Command filter on {args_command[1:]}')
        print(f"** {allowed_commands_str}")
    elif args_command not in ALLOWED_COMMANDS.keys(): 
        allowed_commands_str = '\n** '.join(f"{key} {value}" for key, value in ALLOWED_COMMANDS.items())
        print(f"Command {args_command} not found. The possible commands are: {allowed_commands_str}")
    elif (args_command == 'test' ) :
        print(f"Running test command with param1: {args_param1} and param2: {args_param2}")
        # Add your test command logic here  
        helperlib.print_troubleshooting_info(scriptlog=scriptlog)

        
        

    else:  
        print(f"No command passed {args_command}.") 

    
    scriptlog.print_summary()  
    

    print(f"Started:{tdiff.start_time_str} Total Duration: {tdiff.convert_timediff()}")
    
    
   
if __name__ == "__main__":
    main()  