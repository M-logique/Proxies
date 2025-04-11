# Standard library imports
import asyncio
import json
import logging
import os
import sys
import importlib.util
from re import findall
from typing import List, Dict, Optional

# Logging imports
from logging import Logger, INFO, Formatter, StreamHandler, FileHandler, DEBUG
from logging.handlers import RotatingFileHandler


# Setup directory paths
# Get the root directory of the current script
root_dir = os.path.dirname(os.path.abspath(__file__))

# Attempt to get the workflow directory from the command-line arguments, defaulting to "." if not provided
workflow_dir = next((arg for i, arg in enumerate(sys.argv) if i == 1), ".")

# Convert to an absolute path for consistency
workflow_dir = os.path.abspath(workflow_dir)

# Check if the specified workflow directory exists
if not os.path.exists(workflow_dir):
    logging.log(logging.ERROR, f"Error: Specified workflow directory does not exist: {workflow_dir}")
    sys.exit(1)

# Dynamically load the 'resources' module built with pybind11
module_name = 'resources'

# Construct the module path dynamically based on root directory and module name
module_path = f'{root_dir}/{module_name}.so'

# Import 'resources' module into the system
spec = importlib.util.spec_from_file_location(module_name, module_path)
resources = importlib.util.module_from_spec(spec)
sys.modules[module_name] = resources
spec.loader.exec_module(resources)


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
logger = CustomLogger("PPP", level = DEBUG, log_to_file = True, log_file_path = "logs/updater.log")


def remove_duplicates(items: List[str]) -> List[str]:
	"""Removes duplicate entries while preserving order."""
	seen_items = set()
	return [item for item in items if not (item in seen_items or seen_items.add(item))]


def dump(filepath: str, text: str) -> None:
	"""Writes text data to a specified file synchronously."""
	# Make the directory if it doesn't exist
	os.makedirs(os.path.dirname(filepath), exist_ok = True)
	
	# Open the specified file in write mode ('w')
	with open(filepath, "w") as fp:
		# Log a debug message indicating the file is being written to
		logger.debug("Writing to file: %s", filepath)
		
		# Convert the 'text' to a string (if it's not already) and write it to the file
		fp.write(str(text))


async def fetch_resources_and_dump() -> None:
	"""Fetches resources, parse JSON, and dump results to file."""
	try:
		# Fetch raw JSON data from an external resource function
		json_data = resources.fetch_resources()
		
		# Parse the fetched JSON data into a Python data structure (list of dictionaries)
		parsed_data = json.loads(json_data)
		
		# Iterate over each resource entry in the parsed data
		for data in parsed_data:
			# Extract the 'name' field for logging purposes
			name = data.get("name")
			
			# Get the 'rawResults' field and split it into individual lines
			raw_results = data.get("rawResults").splitlines()
			
			# Remove duplicate entries from 'raw_results' and join them back into a single string
			joined_results = "\n".join(remove_duplicates(raw_results))
			
			# Construct the file path where the cleaned results will be saved
			filepath = "." + data.get("filepath")
			
			# Save the cleaned and processed results to the specified file
			dump(filepath, joined_results)
			
			# Log a success message indicating that data was successfully saved
			logger.info("Dump success for %s", name)
	
	# Handle JSON parsing errors, logging the issue for troubleshooting
	except json.JSONDecodeError as error:
		logger.error("Error decoding JSON: %s", error)


def read_channels_data(filepath: str) -> List[Dict]:
	"""Reads and parse the JSON data from the given file."""
	try:
		# Open the file at the specified path and read its content
		with open(filepath) as fp:
			# Parse the JSON content and return it as a Python list of dictionaries
			return json.load(fp)
	except Exception as error:
		# Log an error message if reading or parsing the file fails
		logger.error("Error reading channels data: %s", error)
		# Return an empty list to indicate failure and avoid breaking downstream logic
		return []


def extract_urls(raw_content: str) -> str:
	"""Extracts and return the URLs from raw content based on a pattern."""
	# Define a regular expression pattern to match various types of URLs (vless, vmess, ss, trojan)
	pattern = r'(?:vless|vmess|ss|trojan)://[^\s#]+(?:#[^\s]*)?'
	
	# Find all matches of the pattern in the 'raw_content' and reverse their order
	urls = findall(pattern, raw_content)[::-1]
	
	# Join the extracted URLs into a single string, each separated by a newline
	return '\n'.join(urls)


def process_item(item: Dict, filepath: str) -> None:
	"""Processes a single item by extracting URLs and dumping the data."""
	# Extract the "rawResults" field from the 'item' dictionary, defaulting to an empty string if it doesn't exist
	raw_content = item.get("rawResults", "")
	
	# Extract URLs from the 'raw_content' using a custom 'extract_urls' function
	urls = extract_urls(raw_content)
	
	# Check if the extracted 'urls' is not empty or contains non-whitespace characters
	if urls.strip():
		# Save the 'urls' content to a specified 'filepath' using the 'dump' function
		dump(filepath, urls)
		
		# Log an info message indicating a successful dump, including the item name for context
		logger.info("Dump successful for %s", item.get("name"))
	else:
		# Log a warning message if the 'urls' extraction result is empty, indicating failure
		logger.warning("Unsuccessful dump for %s due to empty result", item.get("name"))


async def fetch_tg_channels() -> None:
	"""Fetches Telegram channels and dump relevant URLs."""
	tg_channels_file = f"{workflow_dir}/data/tgchannels.json"
	
	# Read the channels data from the file
	channels = read_channels_data(tg_channels_file)
	
	# Check if the 'channels' variable is empty or None
	if not channels:
		# Log a warning message indicating that no channel data is available
		logger.warning("No channels data found.")
		# Exit the function early and return None, since there's no data to process
		return None
	
	# Convert the 'channels' data into a JSON-formatted string
	json_data = json.dumps(channels)
	
	# Fetch the Telegram channels data using a resource function, passing the JSON data
	data = resources.fetch_tg_channels(json_data)
	
	# Parse the JSON response received from the 'fetch_tg_channels' function into a Python dictionary
	parsed_data = json.loads(data)
	
	# Process each parsed item
	for item in parsed_data:
		filepath = "." + item.get("filepath")
		process_item(item, filepath)


async def main():
	"""
	Main asynchronous function that fetches data concurrently and handles errors robustly.
	"""
	try:
		# Gather tasks to run concurrently
		results = await asyncio.gather(
			fetch_tg_channels(),  # Task 1: Fetch Telegram channels
			fetch_resources_and_dump(),  # Task 2: Fetch resources and dump to file
			return_exceptions = True  # Continue execution even if some tasks raise exceptions
		)
		
		# Process the results to handle exceptions individually for each task
		for index, result in enumerate(results):
			if isinstance(result, Exception):
				logger.error("Task %d failed with error: %s", index + 1, result)
			else:
				logger.info("Task %d completed successfully.", index + 1)
	
		if os.path.exists("additional_configs.txt"):
			with open("additional_configs.txt", "r") as fp:
				configs = fp.readlines()

			with open("proxies/tvc/mixed.txt", "a") as fp:
				fp.write("\n".join(configs))
		
	except asyncio.CancelledError:
		# Handle cases where the tasks are cancelled
		logger.warning("Tasks were cancelled before completion.")
	
	except Exception as error:
		# Catch any unexpected errors during execution
		logger.error("An unexpected error occurred during execution: %s", error)


# Run the main asynchronous function
if __name__ == "__main__":
	# Use ProactorEventLoop (normally for Windows, but can be used on Linux as well)
	# asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
	
	# The default event loop on Linux is SelectorEventLoop, which is suitable for most applications
	# and works efficiently with Linux's native event-handling mechanisms like epoll
	asyncio.run(main())
