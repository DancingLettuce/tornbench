"""This filename is torncommand.py"""

# /home/@@/tb/bin/python3 /home/@@/tornbench/torncommand.py test
#rsync -a -v -P --exclude '*.db' --exclude '*.pyc' --exclude '__pycache__/*' --exclude '*wsgi*' --exclude '.git/*'  /home/u/*** ***@***:/home/***/;echo '***'
# ctrl-k 0 fold

import argparse   
from pathlib import Path
import sys  
import csv
import io

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
    BAZAAR_API_URL = "" 
    REMOTE_ROBOT_URL = ""
    REMOTE_ROBOT_CLIENT_ID = ""
    """ 
SCRIPT_DIR = Path(__file__).resolve().parent 
#DEFAULT_CONFIG_PATH = SCRIPT_DIR / "secrets.toml" # for a local secrets or config file
DEFAULT_CONFIG_PATH = SCRIPT_DIR.parent / "secrets" / "secrets.toml"
DEFAULT_LOG_PATH = SCRIPT_DIR / "log.txt"
ALLOWED_COMMANDS={
    'test':"--a test--", 
    'factionsearch':"search for all factions", 
    'factionmembers':"get all faction members",
    'snapshot':"Get active users",
    'playerprofile_snapshot':"Get profile for all snapshot players",
    'playerprofile': 'playerid/name/factionid/name pfm[p=player/f=faction only/m=all members of faction/0=no datecheck]',
    'getitems': 'get items from torn api',
    'seleniumbazaar': 'get bazaar data using Selenium',
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
    from sqlalchemy import select, or_, func, insert    
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

def _get_csvresponse_from_requests(apiendpoint=None, headers=None, timeout=5):
    # return csv, response object
    try:
        response = requests.get(apiendpoint, headers = headers, timeout=5)
        if response.status_code != 200:
            # eventlog=appendEventLog(feature='api', event='get',verbosity='error' , 
            # value_text= f"Calling api  {apiendpoint} " + 
            # f"Response code is {response} responsetext={response.text}" )
            raise TornAPIError(f"TORN API error response status_code={response.status_code}", reason=f"{response.status_code}",json=None)
        return response.text, response 
    except Exception as e:
        raise e


def get_api(section='', request=None, selections='', cat='', ts_to='', 
        ts_from='', id='', slug='', urlbreadcrumb='', version=2,
        apikey='', user=None, limit='',offset='', raw='', sleepiferror=True,
        debuglog=None, no_progress=False, client_id=None, format='json'):
    """
    version 1 
    https://api.torn.com/user/3558395?selections=&key=YdLcNsoN9XKZWcPy
    https://api.torn.com/faction/48835?selections=&key=YdLcNsoN9XKZWcPy
    version 2
    https://api.torn.com/v2/user/basic
    https://api.torn.com/v2/user/3558395/profile
    https://api.torn.com/v2/user/3558395/personalstats?cat=all
    https://api.torn.com/v2/faction/search
    https://api.torn.com/v2/faction/48835/members
    """
    print(f"get_api called with section={section}, request={request}, selections={selections}, cat={cat}, ts_to={ts_to}, ts_from={ts_from}, id={id}, slug={slug}, urlbreadcrumb={urlbreadcrumb}, version={version}, apikey={apikey}, user={user}, limit={limit}, offset={offset}, raw={raw}, sleepiferror={sleepiferror}")
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
    #print(f"Calling API endpoint: {apiendpoint} with headers: {headers}")
      
    responsejson = None
    ###  get the response and catch error, repeat 
    trycount = 0
    error_timeout =0
    error_tornapi = 0
    if format == 'csv':
        responsecsv, response = _get_csvresponse_from_requests(apiendpoint=apiendpoint, headers=headers, timeout=5)  # returns json or raises error
        return responsecsv
    
    while responsejson is None:
        try:
            # if debuglog:
            #     debuglog.debug(message=f"apiendpoint={apiendpoint}")
            # print_log_file(log_text=f"api2apiendpoint={apiendpoint}")
            #print(f"Calling API endpoint: {apiendpoint} (Attempt {trycount + 1})")
            trycount +=1  
            responsejson, response = _get_response_from_requests(apiendpoint=apiendpoint, headers=headers, timeout=5)  # returns json or raises error
            #print(f"API call successful. Response JSON: {responsejson}")
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
     

def get_factionmembers_viamembersapi(faction_id:int=None, apikey:str=None):
        #https://api.torn.com/v2/faction/5431/members
            try:
                api_response = get_api(section='faction', apikey=apikey, 
                    slug=str(faction_id), urlbreadcrumb='members' ,sleepiferror=True, 
                    no_progress=False )
            except Exception as e:
                raise e
            factionmembers = []
            for i in api_response['members']:
                factionmembers.append(helperlib.flatten_json(i,delimiter='_')) 
            return factionmembers 

def get_snapshot():    
    sqlh = tb_lib_sqlhandler.SqlAService(
                database_name =CONFIG.get('DATABASE_NAME',''), 
                database_host = CONFIG.get('DATABASE_HOST',''),
                database_user = CONFIG.get('DATABASE_USER',''),
                database_password = CONFIG.get('DATABASE_PASSWORD',''),
            )
    sqlh.truncate_table(tablename='tb_player_snapshot_staging')  
    count=0
    with Session(sqlh.engine) as session:
        # Add your snapshot logic here
        # For example, you might want to fetch some data from an API and store it in the database
        # This is a placeholder for the actual implementation
        
        # GET https://api.torn.com/v2/user/snapshot
        try:
            api_response = get_api(section='user', apikey=CONFIG.get('TORN_API_KEY', ''),
                slug=None, urlbreadcrumb='snapshot' ,sleepiferror=True, 
                no_progress=False, format='csv')
        except Exception as e:
            raise e
        clean_text = api_response.strip()
        # Total rows is the number of newlines + 1, then subtract 1 for the header
        total_data_rows = clean_text.count('\n')
        csv_file_like = io.StringIO(api_response)  # Create a file-like object from the CSV string
        reader = csv.DictReader(csv_file_like)
        """
        snapshot CSV format:
        id,name,gender,signed_up,level,rank,donator,faction,company,job,spouse,display_case,bazaar,fed,fed_reason,time_played,awards
        1,Chedburn,Male,1100521336,15,Outstanding,1,40992,79286,,2103253,1,1,0,,48596767,1411
        5,Tebbs,Male,1100521055,95,Elite,1,46166,114356,,253773,1,0,0,,4381288,394
        12,SandyClaws,Male,1100522080,36,Outstanding,1,9745,77427,,97534,1,1,0,,2056518,344"""
        #for row in reader:
        for chunk in helperlib.batched(reader, 1000):
            batch_dicts = []
            for row in chunk:
                count += 1
                utc_dt = dt_datetime.fromtimestamp(int(row.get('signed_up', 0)) if row.get('signed_up') else None, 
                    tz=dt_timezone.utc)
                # Safely extract values using the header names as keys:
                batch_dicts.append({
                    'player_id': int(row['id']),
                    'name': row.get('name'),
                    'gender': row.get('gender'),
                    'signed_up': utc_dt, 
                    'level': row.get('level',None), #None if row.get('level','')=='' else row.get('level') ,
                    'player_rank': row.get('player_rank',''), #None if row.get('player_rank','')=='' else row.get('player_rank') ,
                    'donator': row.get('donator',''), #None if row.get('donator','')=='' else row.get('donator') ,
                    'faction': None if row.get('faction','')=='' else row.get('faction') ,
                    'company': None if row.get('company','')=='' else row.get('company') ,
                    'job': row.get('job'),
                    'spouse': None if row.get('spouse','')=='' else row.get('spouse') ,
                    'display_case': row.get('display_case',''), #None if row.get('display_case','')=='' else row.get('display_case') ,
                    'bazaar': row.get('bazaar',''), #None if row.get('bazaar','')=='' else row.get('bazaar') ,
                    'fed': row.get('fed',''), #None if row.get('fed','')=='' else row.get('fed') ,
                    'fed_reason': row.get('fed_reason'),
                    'time_played': None if row.get('time_played','')=='' else row.get('time_played') ,
                    'awards': None if row.get('awards','')=='' else row.get('awards') ,
                    'update_on_viasnapshotapi': dt_datetime.now(dt_timezone.utc),
                    'updated_on': dt_datetime.now(dt_timezone.utc), 
                } ) 
            """'level': row.get('level') if row.get('level') else None,
                    'player_rank': row.get('rank') if row.get('rank') else None,
                    'donator': row.get('donator') if row.get('donator') else None,
                    'faction': row.get('faction') if row.get('faction') else None,
                    'company': row.get('company') if row.get('company') else None,
                    'job': row.get('job'),
                    'spouse': row.get('spouse',None) if row.get('spouse') else None, 
                    'display_case': row.get('display_case') if row.get('display_case') else None,
                    'bazaar': row.get('bazaar') if row.get('bazaar') else None,
                    'fed': row.get('fed') if row.get('fed') else None,
                    'fed_reason': row.get('fed_reason'),
                    'time_played': row.get('time_played') if row.get('time_played') else None,
                    'awards': row.get('awards') if row.get('awards') else None,
                    'update_on_viasnapshotapi': dt_datetime.now(dt_timezone.utc),
                    'updated_on': dt_datetime.now(dt_timezone.utc), """
            session.execute(insert(tb_lib_sqlhandler_models.PlayerSnapshotStaging), batch_dicts)
            #tb_lib_sqlhandler.update_or_create(session=session, model=tb_lib_sqlhandler_models.PlayerProfile, defaults=defaults, player_id=player_id)
            #if count % 100 == 0 or count == total_data_rows:
            print(f"{count}/{total_data_rows} Processed snapshot for player {row.get('name')} (ID: {row['id']})")   
            
            session.commit()  # Commit after processing all rows
        session.commit()  # Final commit after processing all rows

    sql="""INSERT INTO torn.torn_playerprofile (
            player_id,
            name,
            signup_truedate,
            `level`,
            `rank`,
            faction_id,
            job_company_id,
            spouse_id,
            bazaar_snapshot,
            update_on_viasnapshotapi
        )
        SELECT 
            CAST(s.player_id AS UNSIGNED),
            s.name,
            -- Safely convert string Unix timestamp to MySQL DATETIME
            FROM_UNIXTIME(CAST(NULLIF(s.signed_up, '') AS UNSIGNED)),
            CAST(NULLIF(s.`level`, '') AS UNSIGNED),
            s.player_rank,
            -- NULLIF turns empty CSV strings ('') into NULL before casting to int
            CAST(NULLIF(s.faction, '') AS UNSIGNED),
            CAST(NULLIF(s.company, '') AS UNSIGNED),
            CAST(NULLIF(s.spouse, '') AS UNSIGNED),
            CAST(NULLIF(s.bazaar, '') AS UNSIGNED),
            COALESCE(s.update_on_viasnapshotapi, NOW())
        FROM torn.tb_player_snapshot_staging AS s
        ##WHERE s.player_id REGEXP '^[0-9]+$' -- Protects against corrupt non-numeric rows
        ON DUPLICATE KEY UPDATE
            name                     = VALUES(name),
            signed_up                = VALUES(signed_up),
            `level`                  = VALUES(`level`),
            `rank`                   = VALUES(`rank`),
            faction_id               = VALUES(faction_id),
            job_company_id           = VALUES(job_company_id),
            spouse_id                = VALUES(spouse_id),
            bazaar_snapshot          = VALUES(bazaar_snapshot),
            update_on_viasnapshotapi = VALUES(update_on_viasnapshotapi),
            updated_on               = NOW();"""
    
    sql="""INSERT INTO torn.torn_playerprofile (
            player_id,
            name,
            signup_truedate,
            `level`, 
            faction_id,
            job_company_id,
            spouse_id,
            bazaar_snapshot,
            update_on_viasnapshotapi
        )
        SELECT 
            player_id,
            name,
            signed_up,
            `level`,
            faction,
            company,
            spouse,
            bazaar,
            update_on_viasnapshotapi
        FROM tb_player_snapshot_staging s 
        where not exists (SELECT 1 FROM torn_playerprofile pp WHERE pp.player_id = s.player_id );"""
    print(f"Inserting new records")
    sqlh.execute_sql(sql)
    sql="""
        UPDATE torn_playerprofile AS pp
        INNER JOIN tb_player_snapshot_staging AS s
            ON pp.player_id = s.player_id
        SET pp.name = s.name,
        pp.signup_truedate=s.signed_up,
        pp.`level`=s.level,
        pp.faction_id=s.faction,
        pp.job_company_id=s.company,
        pp.spouse_id=s.spouse,
        pp.bazaar_snapshot=s.bazaar,
        pp.update_on_viasnapshotapi=s.update_on_viasnapshotapi;"""
    print(f"Updating existing records")  
    sqlh.execute_sql(sql)

def donotuse__get_player_profile_viaprofileapi(player_id:int, apikey:str=None, sleepiferror = True, version=1):
        #https://api.torn.com/v2/user?id=3287528
        
      
        try:
            if version == 1:
                api = get_api(section='user', apikey=apikey, slug=str(player_id),
                sleepiferror=sleepiferror,version=version)
            else: 
                api = get_api(section='user', apikey=apikey, id=str(player_id), 
                sleepiferror=sleepiferror, version=version)
        except Exception as e:
            raise e
        
        if api.get('error'):     
            raise Exception(f"error in response {api}")
        elif version == 2 and api.get('profile', None) is None:
            raise Exception(f"error in PROFILE {api}")
        else:
            if version == 2:
                api = api['profile']
            api_json = flatten_json(api,delimiter='_')
            if version == 1:
                api_json['update_on_viauserapi_v1'] = dt_datetime.now(dt_timezone.utc)
                api_json['update_source'] = 'playeruserapi_v'+str(version)
            else:
                api_json['update_on_viaplayerprofileapi'] = dt_datetime.now(dt_timezone.utc)
                api_json['update_source'] = 'playerprofileapi_v'+str(version)
            if api_json.get('signup',None):
                api_json['signup_truedate'] = dt_datetime.strptime(api_json['signup'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if api_json.get('signed_up',None):
                api_json['signup_truedate'] = dt_datetime.strptime(api_json['signed_up'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if api_json['last_action_timestamp']:
                api_json['last_action_truedate'] = dt_datetime.fromtimestamp(float(api_json['last_action_timestamp']), tz=timezone.utc)
                timediff = dt_datetime.now(dt_timezone.utc) - api_json['last_action_truedate'] 
                api_json['last_action_datediff_truedate_days'] = timediff.days
            company_id = api_json.get('job_company_id',None)
            
            # icons must be deleted if they do not exist
            iconslist = ['basicicons_icon3','basicicons_icon27','basicicons_icon6',
                'basicicons_icon87','basicicons_icon4','basicicons_icon8',
                'basicicons_icon26','basicicons_icon9','basicicons_icon35','basicicons_icon71',
                'basicicons_icon15','basicicons_icon22']
            for i in iconslist:
                if i not in api_json.keys():
                    api_json[i] = ''
            faction_id = api_json.get('faction_faction_id', None)
            if faction_id:
                self.factionbasic, self.factionbasic_created = models.FactionBasic.objects.update_or_create(
                    faction_id=faction_id, 
                    defaults={'name':api_json.get('faction_faction_name', 'name-not-found')})
                api_json['factionbasic'] = self.factionbasic
                if self.factionbasic_created:
                    appendEventLog(request=self.request, contentobject=self.factionbasic,
                    feature='script', event='create', model='FactionBasic', model_name=api_json.get('faction_faction_name', 'name-not-found'), 
                    value_text=f"Created on import of {self.player_id} {self.player_name}") 
            if company_id:
                company, created = models.Company.objects.get_or_create(
                    company_id=company_id,
                    defaults={'name':api_json.get('job_company_name','name-not-found')})
                if created:
                    appendEventLog(request=self.request, contentobject=company,
                    feature='script', event='create', model='Company', model_name=api_json.get('job_company_name','name-not-found'), 
                    value_text=f"Created on import of {self.player_id} {self.player_name}") 
                api_json['companytb'] = company

            ## check the status and set the previous status
            if not self.previous_model or not self.previous_model.status_description_previous:
                api_json['status_description_previous'] = api_json['status_description']
                api_json['status_details_previous'] =  api_json['status_details']
                api_json['status_state_previous'] =  api_json['status_state']
                api_json['status_previous_update_on'] = self.batch_time
            else:
                if self.previous_model.status_description != api_json['status_description']:
                    # description has changed
                    api_json['status_description_previous'] = self.previous_model.status_description
                    api_json['status_details_previous'] =  self.previous_model.status_details
                if self.previous_model.status_state != api_json['status_state']:
                    api_json['status_state_previous'] =  self.previous_model.status_state
                    api_json['status_previous_update_on'] = self.previous_model.updated_on
            ####
            self.player_profile, created = models.PlayerProfile.objects.update_or_create(
                player_id=self.player_id,
                defaults = api_json)
            ####
            if created:
                appendEventLog(request=self.request, contentobject=self.player_profile,
                feature='script', event='create', model='PlayerProfile', model_name=self.player_profile.name)
            else:
                appendEventLog(request=self.request, contentobject=self.player_profile,
                feature='script', event='updated', model='PlayerProfile', model_name=self.player_profile.name)
        return self.player_profile

def updateplayerprofile(api_dictlist=None):
    """Running playerprofile command with param1: 3974694 and param2: None
        API response: {'rank': 'Outstanding Bonds Agent', 'level': 35, 
        'honor': 500, 'gender': 'Male', 'property': 'Private Island', 
        'signup': '2025-10-14 05:53:31', 
        'awards': 260, 'friends': 4, 'enemies': 1, 'forum_posts': 7, 
        'karma': 2, 'age': 383, 'role': 'Civilian', 'donator': 1, 
        'player_id': 3974694, 'name': 'TonTin', 'property_id': 5719345, 
        'revivable': 0, 'profile_image': 'https://profileimages.torn.com/05550ab6-9c28-4646-9719-75f254a7afae-3974694.png', 
        'life': {'current': 1625, 'maximum': 1625}, 'status': {'description': 'Okay', 
        'details': '', 'state': 'Okay', 'color': 'green', 'until': 0}, 
        'job': {'job': 'Employee', 'position': 'Confectionist', 'company_id': 115809, 
        'company_name': 'Reaper&#039;s Sweet Shoppe', 'company_type': 14}, 
        'faction': {'position': 'Enforcer', 'faction_id': 48835, 
        'days_in_faction': 382, 'faction_name': 'Valiance', 'faction_tag': 'VLNC', 
        'faction_tag_image': '48835-34313.png'}, 'married': {'spouse_id': 3971658, 
        'spouse_name': 'Lawzz', 'duration': 378}, 'basicicons': {'icon6': 'Male', 
        'icon4': 'Subscriber', 'icon8': 'Married - To Lawzz', 'icon27': 
        'Company - Confectionist of Reaper&#039;s Sweet Shoppe (Sweet Shop)', 
        'icon9': 'Faction - Enforcer of Valiance'}, 'states': {'hospital_timestamp': 0, 'jail_timestamp': 0}, 
        'last_action': {'status': 'Offline', 'timestamp': 1793543921, 'relative': '8 hours ago'}, 
        'competition': {'name': 'Rock, Paper, Scissors', 'status': 'rock', 'current_hp': 255, 'max_hp': 256}} for query: 3974694

        Running playerprofile command with param1: 3974694 and param2: None
        API response: {'rank': 'Outstanding Bonds Agent', 'level': 35, 'honor': 500, 
        'gender': 'Male', 'property': 'Private Island', 'signup': '2025-10-14 05:53:31', 
        'awards': 260, 'friends': 4, 'enemies': 1, 'forum_posts': 7, 'karma': 2, 'age': 383, 
        'role': 'Civilian', 'donator': 1, 'player_id': 3974694, 'name': 'TonTin', 'property_id': 5719345, 
        'revivable': 0, 'profile_image': 'https://profileimages.torn.com/05550ab6-9c28-4646-9719-75f254a7afae-3974694.png', 
        'life_current': 1625, 'life_maximum': 1625, 'status_description': 'Okay', 'status_details': '', 'status_state': 'Okay', 
        'status_color': 'green', 'status_until': 0, 'job_job': 'Employee', 'job_position': 'Confectionist', 'job_company_id': 115809, 
        'job_company_name': 'Reaper&#039;s Sweet Shoppe', 'job_company_type': 14, 'faction_position': 'Enforcer', 
        'faction_faction_id': 48835, 'faction_days_in_faction': 382, 'faction_faction_name': 'Valiance', 'faction_faction_tag': 'VLNC', 
        'faction_faction_tag_image': '48835-34313.png', 'married_spouse_id': 3971658, 'married_spouse_name': 'Lawzz', 
        'married_duration': 378, 'basicicons_icon6': 'Male', 'basicicons_icon4': 'Subscriber', 'basicicons_icon8': 'Married - To Lawzz', 
        'basicicons_icon27': 'Company - Confectionist of Reaper&#039;s Sweet Shoppe (Sweet Shop)', 
        'basicicons_icon9': 'Faction - Enforcer of Valiance', 'states_hospital_timestamp': 0, 'states_jail_timestamp': 0, 
        'last_action_status': 'Offline', 'last_action_timestamp': 1793543921, 'last_action_relative': '8 hours ago', 
        'competition_name': 'Rock, Paper, Scissors', 'competition_status': 'rock', 'competition_current_hp': 255, 'competition_max_hp': 256} for query: 3974694
        """
    sqlh = tb_lib_sqlhandler.SqlAService(
                    database_name =CONFIG.get('DATABASE_NAME',''), 
                    database_host = CONFIG.get('DATABASE_HOST',''),
                    database_user = CONFIG.get('DATABASE_USER',''),
                    database_password = CONFIG.get('DATABASE_PASSWORD',''),
                )
    if isinstance(api_dictlist, dict):
        api_dictlist=[api_dictlist,]
    elif isinstance(api_dictlist, list):
        pass
    else:
        raise "ERROR dictlist"
    with Session(sqlh.engine) as session:
        for api_dict in api_dictlist:
            player_id = api_dict['player_id']
            defaults={'level': api_dict.get('level',None),
                      'age': api_dict.get('age',None),
                      'name': api_dict.get('name',None),
                      'life_current': api_dict.get('life_current',None),
                      'life_maximum': api_dict.get('life_maximum',None),
                      'status_description': api_dict.get('status_description',None),
                      'status_details': api_dict.get('status_details',None),
                      'status_state': api_dict.get('status_state',None),
                      'status_color': api_dict.get('status_color',None),
                      'faction_id': api_dict.get('faction_faction_id',None),
                      'married_spouse_id': api_dict.get('married_spouse_id',None),
                      'job_company_id': api_dict.get('job_company_id',None),
                      'job_company_type': api_dict.get('job_company_type',None),
                      'basicicons_icon27': api_dict.get('basicicons_icon27',None),
                      'last_action_status': api_dict.get('last_action_status',None),
                      'last_action_timestamp': api_dict.get('last_action_timestamp',None),
                      'last_action_relative': api_dict.get('last_action_relative',None),
                      'basicicons_icon4': api_dict.get('basicicons_icon4',None), 
                      'signup': api_dict.get('signup',None), 
                      'updated_on': dt_datetime.now(dt_timezone.utc),
                      }
            if api_dict.get('signed_up',None):
                defaults['signup_truedate'] = dt_datetime.strptime(api_dict['signed_up'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt_timezone.utc)
            if api_dict['last_action_timestamp']:
                defaults['last_action_truedate'] = dt_datetime.fromtimestamp(float(api_dict['last_action_timestamp']), tz=dt_timezone.utc)
                timediff = dt_datetime.now(dt_timezone.utc) - defaults['last_action_truedate']  
                defaults['last_action_datediff_truedate_days'] = timediff.days
            if api_dict.get('update_on_via'):
                defaults[api_dict['update_on_via']] = dt_datetime.now(dt_timezone.utc)

            #print(f"Updating or creating player profile for player_id: {player_id} with defaults: {defaults}")
            
            tb_lib_sqlhandler.update_or_create(session, tb_lib_sqlhandler_models.PlayerProfile,defaults=defaults, player_id=player_id)
        session.commit()  # Commit after processing all player profiles
    

def playerprofile(query:str='',apikey:str=None,version=1):
    #print(f"Running playerprofile command with param1: {ARGS.param1} and param2: {ARGS.param2}")
    if helperlib.is_int(query):
        api = get_api(section='user', apikey=apikey, slug=str(query),
                        sleepiferror=True,version=version)
        if version==1:
            api['update_on_via']='update_on_viauserapi_v1'
        api=helperlib.flatten_json(api,delimiter='_')
    else:
        api=None
    
    #print(f"API response: {api} for query: {query}")
    return api





def playerprofile_snapshot():
    sqlh = tb_lib_sqlhandler.SqlAService(
                database_name =CONFIG.get('DATABASE_NAME',''), 
                database_host = CONFIG.get('DATABASE_HOST',''),
                database_user = CONFIG.get('DATABASE_USER',''),
                database_password = CONFIG.get('DATABASE_PASSWORD',''),
            )
    BATCH_SIZE = 100
    # Define your threshold (e.g., must not have been processed in the last 24 hours)
    batchstart_time = dt_datetime.now(dt_timezone.utc)
    threshold_time = dt_datetime.now(dt_timezone.utc) - timedelta(days=7)
    playerprofile_threshold_time = dt_datetime.now(dt_timezone.utc) - timedelta(days=7) 
    model = tb_lib_sqlhandler_models.PlayerProfile
    totalfaction_processed = 0
    totalmembers_processed = 0
    tdiff = helperlib.TimeDiff()
    with Session(sqlh.engine) as session:
        count_stmt = (
            select(func.count())
            .select_from(model)
            .where(model.level.is_(None))
            .where(
                or_(  
                    model.update_on_viaplayerprofileapi > playerprofile_threshold_time,
                    model.update_on_viaplayerprofileapi.is_(None)
                )  
            )
        )
        # 3. Execute the statement and fetch the raw integer scalar value [source: 1, 2]
        # (Assuming 'session' is your active SQLAlchemy Session object)
        #total_count = session.execute(count_stmt).scalar()
        
        
        stmt = (
            select(model.player_id, model.name)
            .where(model.level.is_(None))
            .where(
                or_(  
                    model.update_on_viaplayerprofileapi > playerprofile_threshold_time,
                    model.update_on_viaplayerprofileapi.is_(None)
                )  
            )
        )
        total_count=tb_lib_sqlhandler.get_statement_count(session=session, stmt=stmt)
        print(f"Total NULL level players: {total_count}")
 
        # 3. Execute the statement and fetch the results
        # (Assuming 'session' is your active SQLAlchemy Session object)
        results = session.execute(stmt).all()

#        # 4. Accessing the results
        count = 0
        for row in results:
            print(f"ID: {row.player_id}, Name: {row.name}")
            api=playerprofile(query=row.player_id, apikey=CONFIG.get('TORN_API_KEY', ''),version=1)
            updateplayerprofile(api_dictlist=api)
        session.commit()  # Commit after processing all player profiles

        stmt = (
            select(model.player_id, model.name)
            .where(model.update_on_viasnapshotapi > dt_datetime.now(dt_timezone.utc) - timedelta(hours=24))
            .where(or_(  
                    model.update_on_viauserapi_v1 < playerprofile_threshold_time,
                    model.update_on_viauserapi_v1.is_(None)
                )  
            ) )
              
        total_records = total_count=tb_lib_sqlhandler.get_statement_count(session=session, stmt=stmt)
        print(f"Total snapshot players: {total_records}")
        results = session.execute(stmt).all()
        for row in results:
            count += 1
            print(f"{count}/{total_records}: Fetching player profile for player_id: {row.player_id}, name: {row.name}  ..{tdiff.convert_timediff()} ")
            
            api=playerprofile(query=row.player_id, apikey=CONFIG.get('TORN_API_KEY', ''),version=1)
            updateplayerprofile(api_dictlist=api)


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

def factionmembers(cooldown_hours: int = 4): 
    print(f"Running factionmembers command with param1: {ARGS.param1} and param2: {ARGS.param2}")
    print(f"searching faction members. Creates the faction if it does not exist, creates the leader if not exists. Does not update leader details.")
    sqlh = tb_lib_sqlhandler.SqlAService(
                database_name =CONFIG.get('DATABASE_NAME',''), 
                database_host = CONFIG.get('DATABASE_HOST',''),
                database_user = CONFIG.get('DATABASE_USER',''),
                database_password = CONFIG.get('DATABASE_PASSWORD',''),
            )
    BATCH_SIZE = 100
    # Define your threshold (e.g., must not have been processed in the last 24 hours)
    batchstart_time = dt_datetime.now(dt_timezone.utc)
    threshold_time = dt_datetime.now(dt_timezone.utc) - timedelta(hours=cooldown_hours)
    factionmodel = tb_lib_sqlhandler_models.FactionBasic
    totalfaction_processed = 0
    totalmembers_processed = 0
    with Session(sqlh.engine) as session:
        count_query = (
                select(func.count())
                .select_from(factionmodel)
                .where(factionmodel.is_destroyed == 0)
                .where(
                    or_(
                        factionmodel.latest_factionmembersapi == None,
                        factionmodel.latest_factionmembersapi < batchstart_time
                    )
                )
                .where(
                    or_(
                        factionmodel.latest_factionmembersapi == None,
                        factionmodel.latest_factionmembersapi < threshold_time
                    )
                )
            )
        # 2. Execute and fetch a single scalar value (the integer count)
        total_records = session.scalar(count_query)
        print(f"Total unprocessed records: {total_records}")
        

    while True:
        with Session(sqlh.engine) as session:
            # Select rows that:
            # 1. Have NEVER been processed (IS NULL)
            # OR
            # 2. Were processed longer ago than our threshold_time
            # stmt = (
            #     select(factionmodel)
            #     .where(
            #         or_(
            #             factionmodel.latest_factionmembersapi == None,
            #             factionmodel.latest_factionmembersapi < threshold_time
            #         )
            #     )
            #     .order_by(factionmodel.id.asc())  # Keeps chunking deterministic
            #     .limit(BATCH_SIZE)
            # )
            #records = session.scalars(stmt).all()
            query = select(factionmodel)
            query = query.where(factionmodel.is_destroyed == 0)
            query = query.where(
                    or_(  
                        factionmodel.latest_factionmembersapi == None,
                        factionmodel.latest_factionmembersapi < batchstart_time
                    )
                )  
            query = query.where(
                or_(
                    factionmodel.latest_factionmembersapi == None,
                    factionmodel.latest_factionmembersapi < threshold_time
                )
            )
            query = query.order_by(factionmodel.id.asc()).limit(BATCH_SIZE)
            records = session.scalars(query).all()
            # If no records match, we are completely done for this run
            if not records:
                break
            for instance in records:
                try:
                    # 1. Call your rate-limited API
                    #print(f"Fetching faction members for faction {instance.name} (ID: {instance.faction_id})")  
                    factionmembers = get_factionmembers_viamembersapi(faction_id=instance.faction_id, apikey=CONFIG.get('TORN_API_KEY', ''))
                    totalfaction_processed += 1
                    totalmembers_processed += len(factionmembers)
                    print(f"{totalfaction_processed}/{total_records} ({totalmembers_processed} members)  Fetched {len(factionmembers)} members for faction {instance.name} (ID: {instance.faction_id})")
                    #print(f"First member details: {factionmembers[0] if factionmembers else 'No members found'}")
                    """Fetched 75 members for faction Valiance (ID: 48835) 
                    First member details: {'id': 2057823, 'name': 'Will', 'level': 100, 
                    'days_in_faction': 1093, 'last_action_status': 'Idle', 
                    'last_action_timestamp': 1793368479, 'last_action_relative': '19 minutes ago', 
                    'status_description': 'Traveling from Torn to Switzerland', 'status_details': None, 
                    'status_state': 'Traveling', 'status_color': 'blue', 'status_until': None, 
                    'status_plane_image_type': 'light_aircraft', 'revive_setting': 'Unknown', 'position': 'Leader', 
                    'is_revivable': False, 'is_on_wall': False, 'is_in_oc': True, 'has_early_discharge': False}
                    """
                    for faction_member in factionmembers:
                        utc_dt = dt_datetime.fromtimestamp(faction_member.get('last_action_timestamp'), tz=dt_timezone.utc)
                        defaults = {
                            'faction_id': instance.faction_id, 
                            'name': faction_member.get('name'),
                            'level': faction_member.get('level'),
                            'last_action_status': faction_member.get('last_action_status'),
                            'last_action_timestamp': faction_member.get('last_action_timestamp'),
                            'last_action_truedate': utc_dt,
                            'status_description': faction_member.get('status_description'),
                            'status_details': faction_member.get('status_details'),
                            'status_state': faction_member.get('status_state'),
                            'status_color': faction_member.get('status_color'),
                            'status_until': faction_member.get('status_until'),
                            'status_plane_image_type': faction_member.get('status_plane_image_type'),
                            'update_on_viafactionmemberapi': dt_datetime.now(dt_timezone.utc),
                            'updated_on': dt_datetime.now(dt_timezone.utc),
                        }
                        tb_lib_sqlhandler.update_or_create(session=session, model=tb_lib_sqlhandler_models.PlayerProfile, defaults=defaults, player_id=faction_member.get('id'))    
                        # 2. Update your business data
                        #instance.value = api_result["new_value"]

                        # 3. Mark the exact moment it was successfully completed
                        # Using func.now() ensures database-level time consistency
                        ##instance.last_processed_at = func.now()
    
                        # Commit immediately so a crash doesn't lose this progress
                    instance.latest_factionmembersapi = dt_datetime.now(dt_timezone.utc)
                    session.commit()
                    #sys.exit(0)  # Exit after processing the first faction for testing purposes


                # except RateLimitException:
                #     session.rollback()
                #     # Backoff and sleep. The instance remains eligible
                #     # for processing because last_processed_at was not updated.
                #     time.sleep(45)

                except Exception as e:
                    print(f"Error processing faction {instance.name} (ID: {instance.faction_id}): {e}"   )
                    raise e 
                    session.rollback()
                    # Optional: Still update the timestamp on structural errors
                    # so a corrupted record doesn't block the queue forever
                    instance.last_processed_at = func.now()
                    session.commit()


    # with Session(sqlh.engine) as session:
    #     # Example of fetching and printing faction members
    #     results = session.execute(text("""SELECT tf.faction_id, tf.name 
    #         FROM torn.torn_factionbasic AS tf
    #         where tf.is_destroyed = 0
    #         ORDER BY tf.faction_id; """)).fetchall()
    #     for row in results:
    #         print(f"ID: {row.id} | Name: {row.name} | Leader ID: {row.leader_id}")  

def get_items():
    print(f"Running getitems command with param1: {ARGS.param1} and param2: {ARGS.param2}")
    """Calling API endpoint: https://api.torn.com/v2/torn/items? (Attempt 1)
    API response: {'id': 2, 'name': 'Baseball Bat', 
    'description': 'A long, solid wooden bat. As a weapon, it can land quite a blow on your enemy.', 
    'effect': None, 'requirement': None, 'image': 'https://www.torn.com/images/items/2/large.png', 
    'type': 'Weapon', 'sub_type': 'Clubbing', 'is_masked': False, 'is_tradable': True, 'is_found_in_city': True, 
    'value': {'vendor': {'country': 'Torn', 'name': "Big Al's Gun Shop"}, 'shops': [{'country': 'Torn', 
    'shop': "Big Al's Gun Shop", 'buy_price': 200, 'sell_price': 130}], 'buy_price': 200, 'sell_price': 130, 
    'market_price': 144}, 'circulation': 767399, 'details': {'category': 'Melee', 'stealth_level': 6.6, 
    'base_stats': {'damage': 16, 'accuracy': 57, 'armor': 0}, 'ammo': None, 'mods': []}}"""

    sqlh = tb_lib_sqlhandler.SqlAService(
                database_name =CONFIG.get('DATABASE_NAME',''), 
                database_host = CONFIG.get('DATABASE_HOST',''),
                database_user = CONFIG.get('DATABASE_USER',''),
                database_password = CONFIG.get('DATABASE_PASSWORD',''),
            )
    with Session(sqlh.engine) as session:
        # https://api.torn.com/v2/torn/items
        # https://api.torn.com/v2/torn/items
        try:
            api_response = get_api(section='torn', apikey=CONFIG.get('TORN_API_KEY', ''),
                slug=None, urlbreadcrumb='items' ,sleepiferror=True, 
                no_progress=False, format='json', version=2)
        except Exception as e: 
            raise e
         
        """Defaults for item ID 1: {'name': 'Hammer', 
        'description': 'A small, lightweight tool used in the building industry. Can also be used as a weapon.', 
        'effect': None, 'requirement': None, 'image': 'https ://www.torn.com/images/items/1/large.png', 'type': 'Weapon', 
        'sub_type': 'Clubbing', 'is_masked': False, 'is_tradable': True, 'is_found_in_city': True, 'buy_price': None, 'sell_price': None, 
        'value_bu y_price': None, 'value_sell_price': None, 'value_market_price': None, 'circulation': 3301462, 'details_category': None, 
        'details_stealth_level': None, 'details_base_stats_damage': None, 'details_base_ stats_accuracy': None, 'details_base_stats_armor': None}
        """
        for item_data in api_response['items']:
            item_data = helperlib.flatten_json(item_data, delimiter='_')
            print(f"Processing item ID: {item_data.get('id')} - Name: {item_data.get('name')}")
            
            defaults = {
                'name': item_data.get('name'),
                'description': item_data.get('description'),
                'effect': item_data.get('effect'),
                'requirement': item_data.get('requirement'),
                'image': item_data.get('image'),    
                'type': item_data.get('type'),
                'sub_type': item_data.get('sub_type'),
                'is_masked': item_data.get('is_masked'),
                'is_tradable': item_data.get('is_tradable'), 
                'is_found_in_city': item_data.get('is_found_in_city'), 
                'value_buy_price': item_data.get('value_buy_price'),
                'value_sell_price': item_data.get('value_sell_price'), 
                'value_market_price': item_data.get('value_market_price'),
                'circulation': item_data.get('circulation'),
            } 
            tb_lib_sqlhandler.update_or_create(session=session, model=tb_lib_sqlhandler_models.Item, defaults=defaults, item_id=int(item_data.get('id')))
        session.commit()  # Final commit after processing all rows
        

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
            if args_command.replace('*', '').lower() in key.lower())
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
        cooldown_hours = 4  # Default cooldown
        if args_param1 and args_param1.isdigit():
            cooldown_hours = int(args_param1)   
        factionmembers(cooldown_hours=cooldown_hours)  # Call the function to handle faction members
    elif (args_command == 'snapshot' ) :
        print(f"Running snapshot command with param1: {args_param1} and param2: {args_param2}")
        # Add your snapshot command logic here
        get_snapshot()  # Call the function to handle snapshot
    elif (args_command == 'playerprofile_snapshot' ) :
        print(f"Running playerprofile_snapshot command with param1: {args_param1} and param2: {args_param2}")
        # Add your playerprofile_snapshot command logic here
        playerprofile_snapshot()  # Call the function to handle player profile snapshot
    elif (args_command == 'playerprofile' ):
        if not args_param2 or 'p' in args_param2:
            # update using update_on_viauserapi_v1
            api=playerprofile(query=args_param1, apikey=CONFIG.get('TORN_API_KEY', ''),version=1)
            updateplayerprofile(api_dictlist=api)
        elif 'f' in args_param2:
            model = tb_lib_sqlhandler_models.PlayerProfile
            threshold_time = dt_datetime.now(dt_timezone.utc) - timedelta(minutes=5)
            with Session(tb_lib_sqlhandler.SqlAService(
                database_name =CONFIG.get('DATABASE_NAME',''), 
                database_host = CONFIG.get('DATABASE_HOST',''),
                database_user = CONFIG.get('DATABASE_USER',''),
                database_password = CONFIG.get('DATABASE_PASSWORD',''),
                ).engine) as session:
                stmt = (
                select(model.player_id, model.name)
                    .where(model.faction_id==args_param1)
                )
                if args_param2 and '0' not in args_param2:
                    stmt = stmt.where(
                            or_(  
                                model.update_on_viauserapi_v1 < threshold_time,
                                model.update_on_viauserapi_v1.is_(None)
                            )  
                        )
                stmt =stmt.order_by(model.player_id.asc())
                total_records = total_count=tb_lib_sqlhandler.get_statement_count(session=session, stmt=stmt) 
                print(f"Total faction members for {args_param1}: {total_records} ..{tdiff.convert_timediff()} minutes")
                results = session.execute(stmt).all()
                for row in results: 
                    print(f"Fetching player profile for player_id: {row.player_id}, name: {row.name} ..{tdiff.convert_timediff()} minutes")
                    api=playerprofile(query=row.player_id, apikey=CONFIG.get('TORN_API_KEY', ''),version=1)
                    updateplayerprofile(api_dictlist=api)
    elif (args_command == 'getitems' ):
        get_items()
    elif (args_command == 'seleniumbazaar' ):
        import tb_lib_selenium
        tb_lib_selenium.REMOTE_ROBOT_URL = CONFIG.get('REMOTE_ROBOT_URL', '')
        tb_lib_selenium.BAZAAR_API_URL = CONFIG.get('BAZAAR_API_URL', '')
        tb_lib_selenium.REMOTE_ROBOT_CLIENT_ID = CONFIG.get('REMOTE_ROBOT_CLIENT_ID', '')
        if args_param1 and args_param1.lower() == 'getremotecontrolstate':
            if args_param2:
                client_id=args_param2
            else:
                client_id=tb_lib_selenium.REMOTE_ROBOT_CLIENT_ID
            response = tb_lib_selenium.getremotecontrolstate(client_id=client_id)
            print(f"Remote control state for client_id {client_id}: {response} {response.json() if hasattr(response, 'json') else ''}")
             
        else: 
            tb_lib_selenium.getbazaar(bazaar_api_url=CONFIG.get('BAZAAR_API_URL',''),) 
  
        




        

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