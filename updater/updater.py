import ctypes
import json
import os
from threading import Thread
from os import makedirs, path as _path
from logging import Logger, INFO, Formatter, StreamHandler

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


logger = CustomLogger("PPP")

def remove_duplicates(lst):
    seen = set()  
    result = []   
    for item in lst:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


root_dir = os.path.dirname(os.path.abspath(__file__))


def fetch_resources_and_dump():
    updater = ctypes.CDLL(f'{root_dir}/updater.so')
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
    ...

# async def main():
#     thread = Thread(target=fetch_resources_and_dump)
#     thread.start()

#     obj = SpecialResources(".")

#     await gather(obj.mci_mtn(), obj.mahsa_normal())
#     thread.join()

def dump(filepath: str, text: str):
    """
    Writes text data to a file at the specified path.
    """
    makedirs(_path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as fp:
        logger.debug("Writing to file: %s", filepath)
        fp.write(str(text))
        

if __name__ == "__main__":

    thread = Thread(target=fetch_resources_and_dump)
    thread.start()


    thread.join()
