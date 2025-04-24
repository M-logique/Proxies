import json
import os
import secrets
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from glob import iglob
# Logging imports
from logging import (DEBUG, INFO, FileHandler, Formatter, Logger,
                     StreamHandler)
from logging.handlers import RotatingFileHandler
from string import ascii_letters, digits
from typing import (Any, Dict, Generator, List, Optional, Sequence, Tuple,
                    Type, TypeVar)
import importlib.util
from sysconfig import get_config_var
from uuid import uuid4

# Setup directory paths
# Get the root directory of the current script
root_dir = os.path.dirname(os.path.abspath(__file__))

# Attempt to get the workflow directory from the command-line arguments, defaulting to "." if not provided
workflow_dir = next((arg for i, arg in enumerate(sys.argv) if i == 1), ".")


# The folder where the JSON files will be saved
JSON_FILES_DIR: str = f"{workflow_dir}/json_files"
XRAY_CORE_PATH: str = f"{root_dir}/xray"


# The folders containing the configuration files of V2ray.
folder_paths: Tuple[str, ...] = (
    "./proxies/v2ray",
    "./proxies/tvc"
)

# Dynamically load the 'resources' module built with pybind11
module_name: str = 'proxies'
system_soabi: str = get_config_var("SOABI")

# Construct the module path dynamically based on root directory and module name
module_path = f'{root_dir}/{module_name}.so'

# Import 'proxies' module into the system
spec = importlib.util.spec_from_file_location(module_name, module_path)
proxies = importlib.util.module_from_spec(spec) #type: ignore
sys.modules[module_name] = proxies
spec.loader.exec_module(proxies) #type: ignore

TP = TypeVar("TP", bound="Payload")
T = TypeVar("T")

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
    def from_json(cls: Type[TP], json_data: str) -> TP:
        """
        Creates an instance of the dataclass from a JSON string.

        :param json_data: JSON string representing the dataclass.
        :type json_data: str
        :return: An instance of the dataclass.
        :rtype: TP
        """
        data: Any = json.loads(json_data)
        return cls(**data) #type: ignore
    
    @classmethod
    def from_dict(cls: Type[TP], dict_data: dict) -> TP:
        """
        Creates an instance of the dataclass from a dict.

        :param dict_data: JSON string representing the dataclass.
        :type dict_data: dict
        :return: An instance of the dataclass.
        :rtype: TP
        """

        return cls(**dict_data) #type: ignore


@dataclass
class InputPayload(Payload):
    """
    Represents the input payload with configurations and metadata.

    :param configs: List of configuration dictionaries.
    :type configs: List[Dict]
    """
    configs: List[Dict[Any, Any]]


@dataclass
class Location(Payload):
    """
    Represents location details associated with a query.

    :param query: The query string that resulted in this location (e.g., IP or hostname).
    :type query: str
    :param country: The name of the country for this location.
    :type country: str
    :param countryCode: The ISO 3166-1 alpha-2 country code (e.g., "US" for the United States).
    :type countryCode: str
    :param region: The region or state within the country.
    :type region: str
    :param regionName: The human-readable name of the region (e.g., "California").
    :type regionName: str
    :param city: The name of the city.
    :type city: str
    :param status: The status of the location resolution (e.g., "success" or "fail").
    :type status: str
    """
    query: str
    country: str
    countryCode: str
    region: str
    regionName: str
    city: str
    status: str

@dataclass
class Output(Payload):
    """
    Represents an output entity containing a URL and its associated location data.

    :param url: The URL associated with this output.
    :type url: str
    :param location: A Location object providing geographic details for the URL.
    :type location: Location
    """
    url: str
    location: Location

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

generate_unique_port = lambda: int(uuid4().int & (1<<16) -1) + 1024 


# Initialize a custom logger named "PPP" with default logging level INFO
# This logger will output logs with a specified format to the console
logger = CustomLogger("PPP", level = DEBUG, log_to_file = True, log_file_path = "logs/checker.log")

def yield_txt_files(folder_path: str) -> Generator[str, None, None]:
    """Yields .txt files from the given folder.

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
    raw_json["inbounds"][0]["settings"] = {
            "timeout": 300
        }
    raw_json["inbounds"][0]["protocol"] = "http"
    del raw_json["inbounds"][0]["sniffing"]

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
    configs: List[Dict[Any, Any]] = []

    def process_line(line: str) -> Optional[Dict[Any, Any]]:
        port = generate_unique_port()
        try:
            json_file_path = save_json(line, port)
            logger.info("Generated JSON for URL: '%s', path: %s", line, json_file_path)
            payload = ConfigPayload(
                url=line,
                jsonFilePath=json_file_path,
                port=port
            )

            # print(payload.port)

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

def chunks(data: Sequence[T], chunk_size: int) -> Generator[Sequence[T], None, None]:
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

def main():
    """
    Main function to process proxies, collect outputs, and generate a final JSON result.
    """
    # Ensure the directory for storing JSON files exists
    if not os.path.exists(JSON_FILES_DIR): 
        os.makedirs(JSON_FILES_DIR)

    # Generate the input payload for processing
    input_payload: InputPayload = generate_input_payload()

    # List to store processed outputs
    outputs: List[Output] = []

    # Process the input payload in chunks of 300 configurations
    for chunk in chunks(input_payload.configs, 300):
        # Create a smaller InputPayload object for the current chunk
        liter_input_payload: InputPayload = InputPayload(
            configs=list(chunk)
        )
        
        # Process proxies using the given input and xray core file path
        result: str = proxies.process_proxies(
            json_input=liter_input_payload.to_json(),
            xray_core_file_path=XRAY_CORE_PATH
        )

        # Parse the JSON response from the proxy processor
        loaded_outputs: Any = json.loads(result)

        try:
            # Extract and store output data
            for obj in loaded_outputs["outputs"]:
                outputs.append(
                    Output(
                        url=obj.get("url"),
                        location=Location.from_dict(obj.get("location"))
                    )
                )
        except (json.JSONDecodeError, TypeError, Exception) as err:
            # Log an error if data parsing fails
            logger.error("Failed to parse data: %s, exception: %s", err, type(err).__name__)
        
        # Log the current count of collected outputs
        logger.info("Current outputs: %d", len(outputs))

    else:
        # Initialize sets to track unique country codes and names
        locations_by_cc: set = set()
        locations_by_names: set = set()

        # Final dictionary to store processed data
        final_dict: Dict[str, Any] = {
            "totalProfiles": len(outputs),   # Total number of profiles
            "locations": {
                "totalCountries": 0,         # Total number of unique countries
                "byNames": [],               # List of unique country names
                "byCountryCode": []          # List of unique country codes
            },
            "profilesByCountryCode": {},     # URLs grouped by country code
            "profilesByCountryName": {}
        }

        # Process each output to populate the final dictionary
        for output in outputs:
            # Add country code and name to their respective sets
            locations_by_cc.add(output.location.countryCode)
            locations_by_names.add(output.location.country)

            # Retrieve country code and URL for the current output
            cc: str = output.location.countryCode
            url: str = output.url
            country_name: str = output.location.country.replace("Türkiye", "Turkey") 
            # Türkiye will showup in json like this: T\u00fcrkiye
            # So we need to replace it with "Turkey"

            # Group URLs by country code
            final_dict["profilesByCountryCode"][cc] = (
                final_dict["profilesByCountryCode"].get(cc, []) + [url]
            )

            # Group URLs by country name
            final_dict["profilesByCountryName"][country_name] = (
                final_dict["profilesByCountryName"].get(country_name, []) + [url]
            )

        # Populate the final dictionary with unique counts and data
        final_dict["locations"]["totalCountries"] = len(locations_by_cc)
        final_dict["locations"]["byNames"] = list(name for name in locations_by_names if name != "Türkiye")
        final_dict["locations"]["byCountryCode"] = list(locations_by_cc)

        # Write the final dictionary to a JSON file
        with open(f"{workflow_dir}/proxies/byLocation.json", "w") as fp:
            json.dump(final_dict, fp, indent=4)

            



if __name__ == "__main__":
    
    # Check if the specified workflow directory exists
    if not os.path.exists(workflow_dir):
        logger.error(f"Error: Specified workflow directory does not exist: {workflow_dir}")
        sys.exit(1)

    main()
