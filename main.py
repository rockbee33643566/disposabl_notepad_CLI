from disposabi_notepad_client import (
    config, 
    utl,
    encryption,
    database, 
    API,
    Client, 
    CLI
)

def main():
    utl.init_file_system()
    conf = config.get_config()

    if conf.first_launch: 
        first_launch()

    database.init_db()

    api = API(conf.host)
    client = Client(api)
    cli = CLI(client=client, config=conf)

    try:
        cli.main()
    except KeyboardInterrupt:
        print("Программа завершилась")
    finally:
        conf.first_launch = False
        config.edit_config(conf)

def first_launch(): 
    encryption.generate_db_key()

if __name__ == "__main__": 
    main()