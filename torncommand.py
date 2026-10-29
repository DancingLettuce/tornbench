"""This filename is torncommand.py"""

# /home/@@/tb/bin/python3 /home/@@/tornbench/torncommand.py test


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
    DATABASE_DRIVER = ""
    TORN_API_KEY = ""
    """ 
SCRIPT_DIR = Path(__file__).resolve().parent 
#DEFAULT_CONFIG_PATH = SCRIPT_DIR / "secrets.toml" # for a local secrets or config file
DEFAULT_CONFIG_PATH = SCRIPT_DIR.parent / "secrets" / "secrets.toml"
DEFAULT_LOG_PATH = SCRIPT_DIR / "log.txt"
ALLOWED_COMMANDS={
    'test':"--a test--", 
    'factionsearch':"search for all factions", 
    'factionmembers':"get all faction members",
    }
  
ARGS, ARBITRARY_ARGS = init_argparse()
try:
    import tb_lib_helper_lib as helperlib 
    imports_lib_helper_lib = True
except Exception as e:
    print(f"CRITICAL ERROR: Can not import tb_lib_helper_lib {e}")
    imports_lib_helper_lib = False  
    sys.exit()

try:
    import tb_lib_sqlhandler 
    from sqlalchemy.orm import Session
    import tb_lib_sqlhandler_models 
    from sqlalchemy import text  
    from sqlalchemy import select
    import_lib_sqlhandler = True
except Exception as e:
    import_lib_sqlhandler = False
    print(f"WARNING: Can not import lib_sqlhandler {e}")

CONFIG = helperlib.init_secrets(toml_string=TOML_STRING,filename=ARGS.configfile) 
 
from datetime import datetime as dt_datetime, timedelta  , timezone as dt_timezone 
import subprocess
import json 
import os  
import getpass
from dataclasses import dataclass, field
import requests #sudo apt-get install python3-requests # pip install requests
from requests.exceptions import ConnectionError, RequestException
from datetime import datetime, timezone as timezone_datetime, timedelta
from requests.packages.urllib3.exceptions import InsecureRequestWarning



def _get_response_from_requests(apiendpoint=None, headers=None, timeout=5):
    # return json, response object
    try:
        response = requests.get(apiendpoint, headers = headers, timeout=5)
        if response.status_code != 200:
            # eventlog=appendEventLog(feature='api', event='get',verbosity='error' , 
            # value_text= f"Calling api  {apiendpoint} " + 
            # f"Response code is {response} responsetext={response.text}" )
            raise TornAPIError(f"TORN API error response status_code={response.status_code}", reason=f"{response.status_code}",json=None)
        try:
            meme = response.json()
            if meme.get('error', None) is not None:
                m = meme.get('error',meme)
                raise TornAPIError(f"TORN API error {m}", reason=m.get('error',m),json=meme)
            return meme, response
        except Exception as e1:
            raise e1
    except Exception as e:
        raise e
    return meme, None # never get here

def get_api(section='', request=None, selections='', cat='', ts_to='', 
        ts_from='', id='', slug='', urlbreadcrumb='', version=2,
        apikey='', user=None, limit='',offset='', raw='', sleepiferror=False,
        debuglog=None, no_progress=False, client_id=None):
    #print(f"get_api called with section={section}, request={request}, selections={selections}, cat={cat}, ts_to={ts_to}, ts_from={ts_from}, id={id}, slug={slug}, urlbreadcrumb={urlbreadcrumb}, version={version}, apikey={apikey}, user={user}, limit={limit}, offset={offset}, raw={raw}, sleepiferror={sleepiferror}")
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning) 
    headers = None
 
    if version == 1:
        apiurl_v1 = 'https://api.torn.com/'
        apiendpoint = (apiurl_v1 + section + 
            (('/' + slug  ) if slug else '') + 
            '/?' + 
            (('&selections=' + selections ) if selections else '') + 
            ('&key=' + apikey )  
            )
        headers = None
    else:
        if raw:
            apiendpoint=raw
        else:
            apiendpoint = ('https://api.torn.com/v2/' + section + 
                (('/' + slug  ) if slug else '') + 
                (('/' + urlbreadcrumb  ) if urlbreadcrumb else '') + 
                '?' + 
                ((('&selections=' + selections ) if selections else '') + 
                (('&cat=' + cat ) if cat else '') + 
                (('&to=' + ts_to ) if ts_to else '')  + 
                (('&from=' + ts_from ) if ts_from else '')  +
                (('&id=' + id ) if id else '')  +
                (('&limit=' + limit ) if limit else '')   +
                (('&offset=' + offset ) if offset else '') )
                )
        headers = {'Authorization':'ApiKey '+ apikey}    
    
    responsejson = None
    ###  get the response and catch error, repeat
    trycount = 0
    error_timeout =0
    error_tornapi = 0
    while responsejson is None:
        try:
            # if debuglog:
            #     debuglog.debug(message=f"apiendpoint={apiendpoint}")
            # print_log_file(log_text=f"api2apiendpoint={apiendpoint}")
            trycount +=1
            responsejson, response = _get_response_from_requests(apiendpoint=apiendpoint, headers=headers, timeout=5)  # returns json or raises error
            # if debuglog:
            #     debuglog.debug(message=f"responsejson={responsejson}  response={response}")
            #print_log_file(log_text=f"responsejson={responsejson}  response={response}")
            #print_log_file(log_text=f"api2response={response}")
        except requests.exceptions.ReadTimeout as e:
            error_timeout +=1
            if sleepiferror:
                print(f"ReadTimeoutTIMEOUT ERROR_1 {e} for {apiendpoint}. Sleeping x1 for 3 mins error_timeout={error_timeout} error_tornapi={error_tornapi}")
                helperlib.sleep_with_progress_bar(seconds=180,no_progress=no_progress, client_id=client_id)
                responsejson = None
            else:
                print(f"REQUESTS ERROR_2 {e} for {apiendpoint}. sleepiferror is False  error_timeout={error_timeout} error_tornapi={error_tornapi}")
                raise e
        except requests.exceptions.Timeout as e:
            error_timeout +=1
            if sleepiferror:
                print(f"TIMEOUT ERROR_3 {e} for {apiendpoint}. Sleeping x1 for 3 mins error_timeout={error_timeout} error_tornapi={error_tornapi}")
                helperlib.sleep_with_progress_bar(seconds=180,no_progress=no_progress)
                responsejson = None
            else:
                print(f"REQUESTS ERROR_4 {e} for {apiendpoint}. sleepiferror is False  error_timeout={error_timeout} error_tornapi={error_tornapi}")
                raise e
        except TornAPIError as e:
            error_tornapi += 1
            if "Too many requests" in e.reason or "504" in e.reason or "429" in e.reason:
                if sleepiferror:
                    if error_tornapi == 1:
                        print(f"API ERROR01 too many requests for {apiendpoint} e={e} Sleeping x1 45 seconds  error_timeout={error_timeout} error_tornapi={error_tornapi} reaon={e.reason}",) 
                        helperlib.sleep_with_progress_bar(seconds=45,no_progress=no_progress, client_id=client_id)
                    else:
                        print(f"API ERROR02 too many requests for {apiendpoint} e={e} Sleeping x 60 seconds  error_timeout={error_timeout} error_tornapi={error_tornapi} reaon={e.reason}",) 
                        helperlib.sleep_with_progress_bar(seconds=60,no_progress=no_progress, client_id=client_id)
                    responsejson = None
                else:
                    print(f"REQUESTS ERROR03 too many requests  e={e} for {apiendpoint} . sleepiferror is False  error_timeout={error_timeout} error_tornapi={error_tornapi} reaon={e.reason}")
                    raise e
            else:
                #lib#TornAPIErrorGetAPI1/REQUESTS ERROR ThirdPartyAPIError: 504 for https://api.torn.com/user/3635821/?&key=b9k8R3I5J4b4K63Z without Too many requests ThirdPartyAPIError: 504 reason=504  error_timeout=0 error_tornapi=1
                print(f"TornAPIErrorGetAPI1/REQUESTS ERROR e={e} for {apiendpoint} without Too many requests {e} reason={e.reason}  error_timeout={error_timeout} error_tornapi={error_tornapi}",)
                raise e
        except Exception as e:
            print(f"REQUESTS ERROR04 e={e} for {apiendpoint}  error_timeout={error_timeout} error_tornapi={error_tornapi}",)
            raise e
        if responsejson is None and trycount>10:
            break
    
    if responsejson is None:
        print(f"liberror CRITICAL ERROR responsejson is None ",)
        raise Exception(f"CRITICAL ERROR responsejson is None ")
        

    # eventlog=appendEventLog(request=request, feature='api', event='get',verbosity='verbose' , 
    #     eventfield=apiendpoint, 
    #     model=section, model_name= (slug + ' ' + id).strip(),
    #     value_text= f"Calling api v{version} {apiendpoint} " +
    #     (f"ts_from={timestamptodate(ts_from)}" if ts_from else '') +
    #     (f"ts_to={timestamptodate(ts_to)}" if ts_to else '') + ' ' + 
    #     f"Response code is {response} data={responsejson}" )
    return responsejson
     
def factionsearch():
    print(f"Running factionsearch command with param1: {ARGS.param1} and param2: {ARGS.param2}")
    print(f"searching factions. Creates the faction if it does not exist, creates the leader if not exists. Does not update leader details.")
    sqlh = tb_lib_sqlhandler.SqlAService(
                database_name =CONFIG.get('DATABASE_NAME',''), 
                database_host = CONFIG.get('DATABASE_HOST',''),
                database_user = CONFIG.get('DATABASE_USER',''),
                database_password = CONFIG.get('DATABASE_PASSWORD',''),
            )
    with Session(sqlh.engine) as session:
        #instance = session.get(tb_lib_sqlhandler_models.FactionBasic, faction_id=19) 
        #instance = session.scalars(select(tb_lib_sqlhandler_models.FactionBasic).filter_by(faction_id=19)).first()
        #instance.name="39th Street Killers"
        #instance.name="39sk"
        #session.commit()

        #print(f"Fetched faction with id 19: {instance.name if instance else 'Not Found'}")  
        #sys.exit(0)  # Exit after opening the session for testing purposes
        fs= FactionSearch(apikey=CONFIG.get('TORN_API_KEY', ''))
        print(f"Searching factions with API key: {CONFIG.get('TORN_API_KEY', '')}" )
        next = fs.search()
        pagecount=0
        factioncount=0
        batch_time = dt_datetime.now(dt_timezone.utc)
        current_time = dt_datetime.now(dt_timezone.utc)
        while next:
            pagecount +=1
            for i in fs.factionlist:
                factioncount +=1
                # fid = i.pop('id')
                # i['update_on_viafactionsearchapi']= current_time
                # leader, leadercreated = models.PlayerProfile.objects.get_or_create(
                #     player_id=i['leader_id'], defaults={
                #         'update_source':'factionsearch',
                #         'update_on_viafactionsearchapi': current_time,
                #         'name':i['leader_name']}
                #     )
                # i.pop('leader_name')
                # i['faction_leader'] = leader 
                defaults = {'name': i.get('name'), 'tag': i.get('tag'), 'leader_id': i.get('leader_id'),
                            'co_leader_id': i.get('co_leader_id'), 'co_leader_name': i.get('co_leader_name'), 
                            'is_destroyed': i.get('is_destroyed'),
                            'update_on_viafactionsearchapi': current_time,
                            'updated_on': current_time,
                            }
                factionbasic, factioncreated =tb_lib_sqlhandler.update_or_create(session, 
                        tb_lib_sqlhandler_models.FactionBasic, 
                        faction_id=i.get('id'), 
                        defaults=defaults)
                #print(f"Processed faction {factionbasic.name} {factionbasic.faction_id}. Updated: {factioncreated}")
                #print(f"Defaults used for get_or_create: {defaults}")
                #session.commit()  # Commit after each get_or_create to ensure changes are saved
                #sys.exit(0)  # Exit after processing the first faction for testing purposes

                # models.FactionBasic.objects.update_or_create(
                #     faction_id=fid, defaults=i )
                # m=''
                if factioncreated:
                    m = f"Faction {factionbasic.name} {factionbasic.faction_id} was created "
                else:
                    m=(f"faction {factionbasic.name} {factionbasic.faction_id} "
                    f"updated. Running for {(current_time - batch_time).total_seconds() // 60 } mins")
    
                # if leadercreated:
                #     leader.factionbasic = factionbasic
                #     leader.save()
                #     m= m + f"Leader {leader.name} {leader.player_id} {fid} was created"
                print(f"{pagecount}-{factioncount} {next} {m}")
            fs= FactionSearch(apikey=CONFIG.get('TORN_API_KEY', ''), raw=next) 
            next = fs.search() 
            current_time = dt_datetime.now(dt_timezone.utc)
            session.commit()
        session.commit()

def factionmembers():
    print(f"Running factionmembers command with param1: {ARGS.param1} and param2: {ARGS.param2}")
    print(f"searching faction members. Creates the faction if it does not exist, creates the leader if not exists. Does not update leader details.")
    sqlh = tb_lib_sqlhandler.SqlAService(
                database_name =CONFIG.get('DATABASE_NAME',''), 
                database_host = CONFIG.get('DATABASE_HOST',''),
                database_user = CONFIG.get('DATABASE_USER',''),
                database_password = CONFIG.get('DATABASE_PASSWORD',''),
            )
    results = 
    with Session(sqlh.engine) as session:
        # Example of fetching and printing faction members
        results = session.execute(text("""SELECT tf.faction_id, tf.name 
            FROM torn.torn_factionbasic AS tf
            where tf.is_destroyed = 0
            ORDER BY tf.faction_id; """)).fetchall()
        for row in results:
            print(f"ID: {row.id} | Name: {row.name} | Leader ID: {row.leader_id}")  

def test_db_connection():
    print(f"Testing database connection with config: {CONFIG}")
    sqlh = tb_lib_sqlhandler.SqlAService(
                database_name =CONFIG.get('DATABASE_NAME',''), 
                database_host = CONFIG.get('DATABASE_HOST',''),
                database_user = CONFIG.get('DATABASE_USER',''),
                database_password = CONFIG.get('DATABASE_PASSWORD',''),
                database_driver = CONFIG.get('DATABASE_DRIVER',''),
            )
    try:
        with sqlh.engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"Database connection successful. Result: {result.scalar()}")
    except Exception as e:
        print(f"Database connection failed: {e}")

def main():
    tdiff = helperlib.TimeDiff()
    scriptlog = helperlib.ScriptLog()   
    scriptlog.print_summary()  
    
    args_command = ARGS.command 
    args_param1 = ARGS.param1
    args_param2 = ARGS.param2
    
    if args_command and (args_command.startswith('*') or args_command.endswith('*')):
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
        test_db_connection() 
        # Add your test command logic here  
        helperlib.print_troubleshooting_info(scriptlog=scriptlog)
    elif (args_command == 'factionsearch' ) :
        factionsearch() 
    elif (args_command == 'factionmembers' ) :
        print(f"Running factionmembers command with param1: {args_param1} and param2: {args_param2}")
        # Add your factionmembers command logic here
        factionmembers()  # Call the function to handle faction members


        

    else:  
        print(f"No command passed {args_command}.") 

    
    scriptlog.print_summary()  
    

    print(f"Started:{tdiff.start_time_str} Total Duration: {tdiff.convert_timediff()}")
    
class TornAPIError(Exception):
    def __init__(self, message="An unknown error occurred with the API.", reason=None, json=json):
        super().__init__(message)
        self.reason = reason # Store the specific reason if available
        self.json = json
    def __str__(self):
        if self.reason:
            return f"ThirdPartyAPIError10: superstr={super().__str__()}  reason={self.reason}  "
        return super().__str__()


@dataclass 
class FactionSearch:
    # https://api.torn.com/v2/faction/search?limit=20&offset=0
    """
        {
        "search": [
        {
        "id": 19,
        "name": "39th Street Killers",
        "respect": 15396034,
        "members": 100,
        "leader": {
            "id": 2151656,
            "name": "Kasto"
        },
        "co_leader": {
            "id": 1326199,
            "name": "Shoop"
        },
        "image": "https://factionimages.torn.com/08ed9796-7b7a-43d8-a25a-d21683f24f9b-19.gif",
        "tag_image": "https://factiontags.torn.com/19-91655.png",
        "tag": "39th",
        "is_destroyed": false,
        "is_recruiting": false
        },
        {
        "id": 33,
        "name": "Honour and Pride",
        "respect": 127302,
        "members": 3,
        ...
        ],
        "_metadata": {
            "links": {
            "prev": null,
            "next": "https://api.torn.com/v2/faction/search?&offset=20"
            }
        """
    apikey: str = None
    raw:str = None
    api_response = None
    response_search = None
    meta_next = None
    factionlist = []
    limit = 20
    offset = 0
    request = None
    next = None
    batch_time = None
    sleepiferror=True
    no_progress=False
    client_id=None
    # def __init__(self,**kwargs):
    #     # # call the super by using super().__init__(**kwargs)
    #     # for k,v in kwargs.items():
    #     #     setattr(self,k,v) 
    #     if self.batch_time is None:
    #         self.batch_time = dt_datetime.now(dt_timezone.utc)
    def search(self, sleepiferror=None):
        print(f"Searching factions with API key: {self.apikey} and raw: {self.raw}")

        if sleepiferror is not None:
            self.sleepiferror=sleepiferror 
        if self.raw:
            self.api_response = get_api(raw=self.raw,  apikey=self.apikey, sleepiferror=self.sleepiferror ,
            no_progress=self.no_progress, client_id=self.client_id)
        else:   
            if self.offset is None:
                self.offset = 0
            self.api_response = get_api(section='faction', apikey=self.apikey, 
                slug='search', request=self.request, sleepiferror=sleepiferror ,
                limit=str(self.limit), offset=str(self.offset),no_progress=self.no_progress, client_id=self.client_id )
        self.factionlist = []
        for i in self.api_response['search']:
            self.factionlist.append(helperlib.flatten_json(i,delimiter='_'))
        self.next = self.api_response['_metadata']['links']['next']
        return self.next 
   
if __name__ == "__main__":
    main()  