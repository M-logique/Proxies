
import importlib.util
import json
import os
import sys
from logging import INFO, Formatter, Logger, StreamHandler
from os import makedirs
from os import path as _path
from re import findall
from sysconfig import get_config_var
from asyncio import gather, create_task, run


root_dir = os.path.dirname(os.path.abspath(__file__))
workflow_dir = sys.argv[1]

# Importing resources module that built using pybind11
module_name = 'resources'
system_soabi = get_config_var('SOABI')
module_path = f'{root_dir}/{module_name}.{system_soabi}.so'

spec = importlib.util.spec_from_file_location(module_name, module_path)
resources = importlib.util.module_from_spec(spec)
sys.modules[module_name] = resources
spec.loader.exec_module(resources)


class CustomLogger(Logger):
    """Custom logger with a console handler and specific formatting."""
    def __init__(self, name: str, level: int = INFO):
        super().__init__(name, level)

        # Define log format
        formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Create and set console handler
        console_handler = StreamHandler()
        console_handler.setFormatter(formatter)

        # Prevent multiple handlers if one already exists
        if not self.hasHandlers():
            self.addHandler(console_handler)



def remove_duplicates(lst):
    seen = set()  
    result = []

    for item in lst:
        if item not in seen:
            result.append(result)
            seen.add(item)

    return result


logger = CustomLogger("PPP")


async def fetch_resources_and_dump():
    json_data = resources.fetch_resources()


    try:
        parsed_data = json.loads(json_data)
        def dump_data(data):
            name = data.get("name")
            raw_results = data.get("rawResults").splitlines()
            joined_results = "\n".join(remove_duplicates(raw_results))
            filepath = "."+data.get("filepath")

            dump(filepath=filepath, text=joined_results)

            logger.info("Dump success for %s", name)

        
        list(
            map(
                dump_data,
                parsed_data
            )
        )



    except json.JSONDecodeError as e:
        logger.error("Error decoding JSON:", e)

async def fetch_tg_channels():
    with open(f"{workflow_dir}/data/tgchannels.json") as fp:
        channels = json.load(fp)
    
    json_data = str(json.dumps(channels))
    data = resources.fetch_tg_channels(json_data)

    parsed_data = json.loads(data)
    pattern = r'(?:vless|vmess|ss|trojan)://[^\s#]+(?:#[^\s]*)?'

    def dump_item(item):

        raw_content = item.get("rawResults")
        filepath = "."+item.get("filepath")
        name = item.get("name")


        urls = findall(pattern, raw_content)[::-1]
        joined_urls = '\n'.join(urls)
        
        if joined_urls.strip() != "":
            dump(
                filepath=filepath,
                text=joined_urls
            )
            logger.info("Dump successfull for %s", name)
        else:
            logger.warning("Unsuccessfull dump for %s due to empty result in scraping", name)

    list(
        map(
            dump_item,
            parsed_data
        )
    )



def dump(filepath: str, text: str):
    """
    Writes text data to a file at the specified path.
    """
    makedirs(_path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as fp:
        logger.debug("Writing to file: %s", filepath)
        fp.write(str(text))

async def main():
    jobs = (
        fetch_tg_channels,
        fetch_resources_and_dump
    )

    await gather(
        *map(
            create_task, 
            jobs
        )
    )


if __name__ == "__main__":

    run(main())