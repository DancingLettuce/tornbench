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
    SSH_CERTIFICATE_FILE=""
    MEDIA_SOURCE=""
    SCP_DESTINATION_PATH=""
    TRANSCRIBER_PROJECT_ID=""
    SERVICE_ACCOUNT_FILE=""
    SEMANTIC_DATABASE=""
    SEMANTIC_USER=""
    SEMANTIC_PASSWORD=""
    SEMANTIC_IP=""
    ADMIN_EMAIL = ""
    VAULT_MATTER_ID = ""
    BASE_DOWNLOAD_DIR="" 
    DRIVE_PARENT_FOLDER_ID=""
    DRIVE_OWNER_EMAIL=""
    DJANGO_ROOT=""
    DJANGO_SETTINGS_MODULE=""
    GOOGLE_GROUP_HIGHLIGHT=[] 
    GOOGLEUSER_ACCOUNT_PASSWORD_DEFAULT = ""
    GOOGLEUSER_DEFAULT_HOLD_OU = ""
    TRANSCRIBE_PROMPT_ADDITIONAL_1 = ""
    TRANSCRIBE_OWNER_EMAIL = ""
    TRANSCRIBE_FOLDER_ID = ""
    TRANSCRIBE_LECTURE_FOLDER_ID = ""
    CLOUD_CMDB_DATABASE_NAME = ""
    CLOUD_CMDB_DATABASE_HOST = ""
    CLOUD_CMDB_DATABASE_USER = ""
    CLOUD_CMDB_DATABASE_PASSWORD = ""
    CLOUD_CMDB_DATABASE_DRIVER = ""
    EMAIL_HOST = ''
    EMAIL_USE_TLS = ""
    EMAIL_PORT = ""
    EMAIL_HOST_USER=''
    EMAIL_HOST_PASSWORD=''
    EMAIL_USER_LIST={} m
    EMAIL_USER_TEST = ""
    """ 
SCRIPT_DIR = Path(__file__).resolve().parent 
#DEFAULT_CONFIG_PATH = SCRIPT_DIR / "secrets.toml" # for a local secrets or config file
DEFAULT_CONFIG_PATH = SCRIPT_DIR.parent / "secrets" / "secrets.toml"
DEFAULT_LOG_PATH = SCRIPT_DIR / "log.txt"
ALLOWED_COMMANDS={
    'menu':"", 'questionary':"",'upload':"param1=folder location (default=.MP3)",'transcribe':"",
    'vault':"",'test':"",'approve_deviceuser':"",
    'delete_device':"",'list_delegates':"",'get_users':"",
    'list_user_groups':"",'delegate_sheet':"",
    'unsuspendmoveouresetpassword':"",'transcribe_lecture':"param1=folderid",
    'search_object':"",'moveou':"", "upload_file":"to gdrive param1=folderid",
    "deprovision_user":"", "unsuspend_user":"", "suspend_user":"",
    "delegate_account":"param1=mailbox param2=userwithaccess",
    "listallprojects":"all | quick","listallorganisations":"","listallfolders":"",
    "listallinstances":"param1=project_id","listallloadbalancers":"param1=project_id",
    "listapis":"project_id",
    "ingesttenable": "file_path",
    "ingestdnszone": "file_path",
    "csvexplode":r"filepath col(default=4)",
    "securityreset":"Delete passkey, Force PW change, Reset backup codes, Delete oAuth",
    "accountreset": "userlist,options (p=reset pw, o=move ou, a=delete oauth," +
    "b=reset backup codes,u=unsuspend/unarchive," + 
    "r=reset sign in,u=unsuspend,s=suspend " +
    "g=delete groups) eg poabusg",
    "syncalldirectoryusers":"",
    "logoutstaleusers":"",
    "deleteoauthstaleusers":"options s=suspended only"
    }
  
ARGS, ARBITRARY_ARGS = init_argparse()
import lib_helper_lib as helperlib 
CONFIG = helperlib.init_secrets(toml_string=TOML_STRING,filename=ARGS.configfile) 
 
from datetime import datetime as dt_datetime, timedelta  , timezone as dt_timezone 
import subprocess
import json 
import os  
import getpass
