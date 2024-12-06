import json
import os
from dataclasses import asdict, dataclass
from glob import iglob
from typing import (Generator, List, Tuple, Type,
                    TypeVar, Sequence, Optional, Dict, Any)
from string import ascii_letters, digits
import secrets
from concurrent.futures import ThreadPoolExecutor

# Logging imports
from logging import Logger, INFO, Formatter, StreamHandler, FileHandler, DEBUG
from logging.handlers import RotatingFileHandler

# The folder where the JSON files will be saved
JSON_FILES_DIR: str = "./json_files"


# The folders containing the configuration files of V2ray.
folder_paths: Tuple[str, ...] = (
    "./proxies/v2ray",
    "./proxies/tvc"
)

value: int = "sex"

T = TypeVar("T", bound='Payload')

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

        return json.dumps(self.to_dict(), indent=4)
    
    def to_dict(self) -> dict:
        """
        Converts the dataclass instance to a dict.

        :return: The dict representation of the instance.
        :rtype: dict
        """

        return asdict(self)

    @classmethod
    def from_json(cls: Type[T], json_data: str) -> T:
        """
        Creates an instance of the dataclass from a JSON string.

        :param json_data: JSON string representing the dataclass.
        :type json_data: str
        :return: An instance of the dataclass.
        :rtype: T
        """
        data = json.loads(json_data)
        return cls(**data)

@dataclass
class InputPayload(Payload):
    """
    Represents the input payload with configurations and metadata.

    :param configs: List of configuration dictionaries.
    :type configs: List[Dict]
    """
    configs: List[Dict[Any, Any]]

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
    :param port: The port number assigned to the configuration.
    :type port: int
    """
    url: str
    jsonFilePath: str
    port: int


class CustomLogger(Logger):
	"""Custom logger with console and file output, and formatted messages."""
	def __init__(self,
	             name: str,
	             level: int = INFO,
	             log_to_file: bool = False,
	             log_file_path: Optional[str] = None,
	             max_log_size: int = 10 * 1024 * 1024,  # Default: 10MB
	             backup_count: int = 5):  # Default: 5 backups
		"""
		Initializes a custom logger with configurable handlers.

		:param name: Name of the logger.
		:param level: Logging level (e.g., INFO, DEBUG, ERROR).
		:param log_to_file: Whether to log to a file (default: False).
		:param log_file_path: Path to the log file (if logging to a file).
		:param max_log_size: Maximum size of the log file before rotation (default: 10MB).
		:param backup_count: Number of backup log files to keep (default: 5).
		"""
  
		super().__init__(name, level)
		
		# Formatter for log messages
		formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
		
		# Console handler for standard output
		console_handler = StreamHandler()
		console_handler.setFormatter(formatter)
		
		# Add console handler if not already present
		if not self.hasHandlers():
			self.addHandler(console_handler)
		
		# File handler setup (if enabled)
		if log_to_file and log_file_path:
			# Ensure the directory exists
			os.makedirs(os.path.dirname(log_file_path), exist_ok = True)
			
			# Use RotatingFileHandler to limit file size and rotate logs
			file_handler = RotatingFileHandler(log_file_path,
			                                   maxBytes = max_log_size,
			                                   backupCount = backup_count)
			file_handler.setFormatter(formatter)
			
			self.addHandler(file_handler)
		
		# Set the default logging level (INFO, DEBUG, etc.)
		self.setLevel(level)
		
		# Avoid duplicate handlers (handled by `hasHandlers()` check above)
	
	def log_to_console(self, level: int = INFO) -> None:
		"""Logs a message to the console."""
		self.setLevel(level)
		for handler in self.handlers:
			if isinstance(handler, StreamHandler):
				handler.setLevel(level)
	
	def log_to_file(self, level: int = INFO) -> None:
		"""Logs a message to the file."""
		self.setLevel(level)
		for handler in self.handlers:
			if isinstance(handler, FileHandler) or isinstance(handler, RotatingFileHandler):
				handler.setLevel(level)


# Initialize a custom logger named "PPP" with default logging level INFO
# This logger will output logs with a specified format to the console
logger = CustomLogger("PPP", level = DEBUG, log_to_file = True, log_file_path = "logs/checker.log")

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
    raw_json = json.loads(__import__("v2json").generateConfig(url)) # type: ignore
    raw_json["inbounds"][0]["port"] = port

    # Generate a random file name and save the JSON file
    file_path: str = os.path.join(JSON_FILES_DIR, f"{generate_random_string(8)}.json")
    with open(file_path, "w") as fp:
        json.dump(raw_json, fp, indent=4)

    # Return the absolute path of the saved file
    return os.path.abspath(file_path)


def generate_json_files() -> List[Dict[Any, Any]]:
    """
    Generates JSON configuration files from proxy URLs and assigns unique ports to each.

    Iterates through all text files in predefined folder paths, processes each line to
    create a configuration, and saves it as a JSON file.

    :return: A list of JSON file paths.
    :rtype: List[str]
    """
    port: int = 1000  # Initialize the base port number
    configs: List[Dict[Any, Any]] = []

    def process_line(line: str) -> Optional[Dict[Any, Any]]:
        nonlocal port # Access the shared port variable
        port += 1
        try:
            json_file_path = save_json(line, port)
            payload = ConfigPayload(
                url=line,
                jsonFilePath=json_file_path,
                port=port
            )

            return payload.to_dict()
        except Exception as err:
            logger.error(f"Error generating JSON for URL '{line}': {err}")
            return None

    for folder_path in folder_paths:
        for txt_file in yield_txt_files(folder_path):
            with open(txt_file, "r") as fp:
                lines = [line.strip() for line in fp.readlines()]

            with ThreadPoolExecutor() as executor:
                results = list(executor.map(process_line, lines))

            configs.extend([result for result in results if result is not None])

    return configs

def generate_input_payload() -> InputPayload:
    """
    Generates an InputPayload object containing configurations for proxy servers.

    Uses `generate_json_files` to create configuration files and wraps the resulting
    JSON file paths into an InputPayload instance.

    :return: An InputPayload object with all configurations.
    :rtype: InputPayload
    """
    json_files = generate_json_files()
    return InputPayload(
        configs=json_files
    )

if __name__ == "__main__":


    # Creating JSON_FILES_DIR if not exists
    if not os.path.exists(JSON_FILES_DIR): 
        os.makedirs(JSON_FILES_DIR)

    
    input_payload = generate_input_payload()

    with open("result.json", "w") as fp:
        json.dump(input_payload.to_dict(), fp, indent=4)