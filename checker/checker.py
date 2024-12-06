import json
import os
from dataclasses import asdict, dataclass
from glob import iglob
from typing import (TYPE_CHECKING, Any, Dict, Generator, List, Tuple, Type,
                    TypeVar, Sequence, overload)
from string import ascii_letters, digits
import secrets


JSON_FILES_DIR: str = "./json_files"

def generateConfig(config: str, dns_list = ["8.8.8.8"]) -> str: # type: ignore
    ...

if not TYPE_CHECKING:
    from v2json import generateConfig



folder_pathes: Tuple[str, ...] = (
    "./proxies/v2ray",
    "./proxies/tvc"
)


def generate_random_string(length: int = 8) -> str:
    """
    Generates a cryptographically secure random string.

    :param length: The desired length of the random string.
    :type length: int
    :return: A random string of specified length.
    :rtype: str
    """
    alphabet = ascii_letters + digits  # a-z, A-Z, 0-9
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def save_json(url: str, port: int) -> str:
    """
    Generates a JSON configuration from the given URL and port, saves it to a file, 
    and returns the absolute path to the saved file.

    :param url: The URL to generate the configuration.
    :type url: str
    :param port: The port number to be assigned to the configuration.
    :type port: int
    :return: The absolute file path of the saved JSON file.
    :rtype: str
    """
    # Generate the raw JSON configuration and set the port
    raw_json = json.loads(generateConfig(url))
    # raw_json["inbounds"][0]["port"] = port

    # Generate a random file name and save the JSON file
    file_path: str = os.path.join(JSON_FILES_DIR, f"{generate_random_string(8)}.json")
    with open(file_path, "w") as fp:
        json.dump(raw_json, fp, indent=4)

    # Return the absolute path of the saved file
    return os.path.abspath(file_path)



T = TypeVar('T')
T_P = TypeVar("T_P", bound='Payload')

@dataclass
class Payload:
    """
    Base class for data structures that can be serialized to JSON.
    """

    def to_json(self) -> str:
        """
        Converts the dataclass instance to a JSON string.

        :return: The JSON string representation of the instance.
        :rtype: str
        """
        return json.dumps(asdict(self), indent=4)

    @classmethod
    def from_json(cls: Type[T_P], json_data: str) -> T_P:
        """
        Creates an instance of the dataclass from a JSON string.

        :param json_data: JSON string representing the dataclass.
        :type json_data: str
        :return: An instance of the dataclass.
        :rtype: T_P
        """
        data = json.loads(json_data)
        return cls(**data)

@dataclass
class InputPayload(Payload):
    """
    Represents the input payload with configurations and metadata.

    :param rootFilePath: Path to the root file.
    :type rootFilePath: str
    :param configs: List of configuration dictionaries.
    :type configs: List[Dict]
    """
    rootFilePath: str
    configs: List[str]

@dataclass
class ConfigPayload(Payload):
    """
    Represents the configuration payload for a specific proxy configuration.

    This class holds information about a specific proxy configuration, including
    the URL, the path to the associated JSON file, the configuration index, and the port number.

    :param url: The URL associated with the configuration.
    :type url: str
    :param jsonFilePath: The file path to the JSON configuration file.
    :type jsonFilePath: str
    :param index: The index of the configuration in the list of configurations.
    :type index: int
    :param port: The port number assigned to the configuration.
    :type port: int
    """
    url: str
    jsonFilePath: str
    index: int
    port: int


def yield_txt_files(folder_path: str) -> Generator[str, None, None]:
    """
    Yields .txt files from the given folder.

    :param folder_path: Path to the folder to search for .txt files.
    :type folder_path: str
    :yield: Path to each .txt file in the folder.
    :rtype: str
    """
    pattern = os.path.join(folder_path, "*.txt")
    for file_path in iglob(pattern):
        yield file_path

def chunker(data: Sequence[T], chunk_size: int) -> Generator[Sequence[T], None, None]:
    """
    Splits the input sequence into chunks of the given size.

    :param data: The input sequence to be split into chunks.
    :type data: Sequence[T]
    :param chunk_size: The size of each chunk.
    :type chunk_size: int
    :yield: A chunk of the input Sequence.
    :rtype: Generator[Sequence[T], None, None]
    """
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

failed = all = 0
def process_txt_files() -> None:
    global failed, all
    port = 1000  # Initialize the base port number

    # Iterate over the predefined folder paths containing proxy configuration files
    for folder_path in folder_pathes:
        
        # Iterate over each .txt file found in the folder
        for txt_file in yield_txt_files(folder_path):
            
            # Create an initial InputPayload to hold the root file and its configurations
            input_payload: InputPayload = InputPayload(
                rootFilePath=txt_file,
                configs=list(),
            )

            # Open and read the lines from the current text file
            with open(txt_file, "r") as fp:
                lines = fp.readlines()

            # Iterate over each line in the text file and generate a ConfigPayload
            for index, line in enumerate(lines):
                
                port += 1  # Increment the port for each new configuration
                
                # Generate the JSON file path for the current configuration line
                all+=1
                try:
                    json_file_path = save_json(line, port)
                except Exception as err:
                    failed+=1
                    print("Failed to sex for config:", line, "\nerr:", err)
                    print("file:", txt_file)
                
                # Create a ConfigPayload instance for the current configuration
                payload = ConfigPayload(
                    index=index,
                    jsonFilePath=json_file_path,
                    port=port,
                    url=line
                )

                # Append the generated ConfigPayload as a JSON string to the input_payload's configs
                input_payload.configs.append(
                    payload.to_json()
                )

            # TODO: Continue the process for storing or handling the input_payload


if __name__ == "__main__":

    if not os.path.exists(JSON_FILES_DIR): 
        os.makedirs(JSON_FILES_DIR)
    process_txt_files()
    print(failed, all)