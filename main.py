import asyncio

from disposabi_notepad_client import (
    config,
    utl,
    logger,
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
    log = logger.get_logger()
    await log.info(f"Запуск приложения, хост={conf.host}")

    if conf.first_launch:
        first_launch()
        conf.first_launch = False
        config.edit_config(conf)
        await log.info("Первый запуск: сгенерирован ключ базы данных")

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
        await log.info("Приложение завершено")
        await logger.get_logger().shutdown()


def first_launch():
    encryption.generate_db_key()


if __name__ == "__main__":
    asyncio.run(main())