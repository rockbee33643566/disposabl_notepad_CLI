import os
import shutil

def init_file_system(
    config_file_name: str | None = None,
    config_example_file_name: str | None = None, 
    data_dir_name: str | None = None
) -> None:
    if config_file_name is None:
        config_file_name = "config.json"
    if config_example_file_name is None:
        config_example_file_name = "config.example.json"
    if data_dir_name is None:
        data_dir_name = "data"
    
    if not os.path.isdir(data_dir_name):
        os.mkdir(data_dir_name)

    if not os.path.isfile(config_file_name):
        shutil.copy(config_example_file_name, config_file_name)