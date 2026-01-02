from __future__ import annotations
from helpers import *
from exaroton import Exaroton

# basic check to see if API connection was successful
def check_successful_API_login(exa):
    try:
        exa.get_account()
        return True
    except:
        return False
    
# check if server exists by server ID
def check_server_exists(servers, id):
    for s in servers:
        if s.id == id:
            return True
    return False

# terminate script
def terminate(exit_msg=""):
    print(exit_msg)
    print('-- script terminating --')
    exit()


# list play time of each player on server (in ticks - independent from server tick rate)
def list_playtime(exa, id):
    server = exa.get_server(id)
    print(f"Checking playtime for server \"{server.name}\"")
    print(f"  IP: {server.address}")
    print(f"  ID: {id}")

    usercache = fetch_json_file(exa, id, "usercache.json")
    players_by_uuid = list_to_dict(usercache)
    print(players_by_uuid)

    player_stats = fetch_stats_files(exa, config.API_KEY, id)
    for uuid, player in player_stats.items():
        print(f"Player: {players_by_uuid[uuid]}")
        print(f"   uuid: {uuid}")
        print(f"   total server playtime (ticks): {player['stats']['minecraft:custom']['minecraft:total_world_time']}")
    pass




if __name__ == '__main__':
    config = load_config()
    print("Config loaded successfully")

    exa = Exaroton(config.API_KEY)
    if not check_successful_API_login(exa):
        terminate('Error in Accessing Exaroton API - Check if API key is valid')
    
    account = exa.get_account()
    servers = exa.get_servers()

    print(f'Accessing Exaroton API through account: {account.name} - {account.email}')

    # no servers in exaroton account
    if len(servers) == 0:
        terminate("There seem to be no servers associated to this exaroton account")
    # exactly one server in exaroton account, proceed for this server
    elif len(servers) == 1:
        print('Found exactly 1 server in exaroton account - ignoring config server ID and proceeding')
        list_playtime(exa, exa.get_servers()[0].id)
    # 2 or more servers in exaroton account
    else:
        # no server ID specified: prompt user to input server ID in config
        if config.SERVER_ID == "" or not config.SERVER_ID:
            print("\nMultiple servers associated to this exaroton account, please paste the server ID of the server you wish to check into the config file (config.json)")
            print("--------------------------")
            print("     List of Servers      ")
            print("--------------------------")
            for i, s in enumerate(servers):
                print(f"Server {i+1}")
                print(f"  name: {s.name}")
                print(f"  IP: {s.address}")
                print(f"  ID: {s.id}")
            terminate("\nRe-run script after inputting server ID")
        # server ID specified in config
        else:
            if check_server_exists(servers, config.SERVER_ID):
                list_playtime(exa, config.SERVER_ID)
            else:
                terminate(f"Could not find server with server ID \"{config.SERVER_ID}\"")

