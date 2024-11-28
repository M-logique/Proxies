import ctypes
import json
import os
from threading import Thread
from os import makedirs, path as _path
from logging import Logger, INFO, Formatter, StreamHandler
from re import findall

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
            result.append(item)
            seen.add(item)
    return result


logger = CustomLogger("PPP")
root_dir = os.path.dirname(os.path.abspath(__file__))
updater = ctypes.CDLL(f'{root_dir}/updater.so')


def fetch_resources_and_dump():
    updater.FetchResources.restype = ctypes.c_char_p
    result = updater.FetchResources()


    json_data = result.decode('utf-8')

    try:
        parsed_data = json.loads(json_data)
        
        for data in parsed_data:
            name = data.get("name")
            raw_results = data.get("rawResults").splitlines()
            joined_results = "\n".join(remove_duplicates(raw_results))
            filepath = "."+data.get("filepath")

            dump(filepath=filepath, text=joined_results)

            logger.info("Dump success for %s", name)



    except json.JSONDecodeError as e:
        logger.error("Error decoding JSON:", e)

def fetch_tg_channels():
    with open(f"{root_dir}/../data/tgchannels.json") as fp:
        channels = json.load(fp)
    
    encoded_json = str(json.dumps(channels)).encode("utf-8")
    char_p_json = ctypes.c_char_p(encoded_json)

    updater.FetchTGChannels.argtypes = (ctypes.c_char_p, )
    updater.FetchTGChannels.restype = ctypes.c_char_p

    data = updater.FetchTGChannels(char_p_json)

    parsed_data = json.loads(data)
    pattern = r'(?:vless|vmess|ss|trojan)://[^\s#]+(?:#[^\s]*)?'

    for item in parsed_data:

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
            logger.warning("Unsuccessfull dump for %s due to empty result in scrapping", name)



def dump(filepath: str, text: str):
    """
    Writes text data to a file at the specified path.
    """
    makedirs(_path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as fp:
        logger.debug("Writing to file: %s", filepath)
        fp.write(str(text))
        

if __name__ == "__main__":

    fetch_tg_channels()

    # thread = Thread(target=fetch_resources_and_dump)
    # thread.start()


    # thread.join()
