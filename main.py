from disposabi_notepad_client import init_db, init_file_system, get_config, Client, API, CLI

def main():
    init_db()
    conf = get_config()

    api = API(conf.host)
    client = Client(api)
    cli = CLI(client, conf)
    cli.main()

if __name__ == "__main__": 
    main()