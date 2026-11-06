import asyncio

from disposabi_notepad_client import (
    config,
    utl,
    encryption,
    Database,
    UserRepo,
    init_db,
    ClientApi,
    Client,
)
from disposabi_notepad_client import run


async def main():
    utl.init_file_system()
    conf = config.get_config()

    if conf.first_launch:
        first_launch()
        conf.first_launch = False
        config.edit_config(conf)

    db = Database()
    await init_db(db=db)
    user_repo = UserRepo(db)

    api = ClientApi(conf.host)
    client = Client(api, db, user_repo)

    try:
        await run(client)
    finally:
        await db.close()
        await api.http.close()


def first_launch():
    encryption.generate_db_key()


if __name__ == "__main__":
    asyncio.run(main())