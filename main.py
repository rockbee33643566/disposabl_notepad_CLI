from disposabi_notepad_client import (
    config, 
    utl,
    encryption,
    Database,
    UserRepo,
    init_db,
    ClientApi,
    Client, 
    CLI
)

def main():
    utl.init_file_system()
    conf = config.get_config()

    if conf.first_launch: 
        first_launch()

    db = Database()
    init_db(db=db)
    user_repo = UserRepo(db)

    api = ClientApi(conf.host)
    client = Client(api, db, user_repo)
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