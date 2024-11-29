# Standard library imports
import asyncio
import json
import os
import sys
import importlib.util
from re import findall
from sysconfig import get_config_var
from typing import List, Dict, Optional

# Logging imports
from logging import Logger, INFO, Formatter, StreamHandler, FileHandler, DEBUG
from logging.handlers import RotatingFileHandler


# Setup directory paths
root_dir = os.path.dirname(os.path.abspath(__file__))
workflow_dir = sys.argv[1]

# Dynamically load the 'resources' module built with pybind11
module_name = 'resources'
system_soabi = get_config_var('SOABI')
module_path = f'{root_dir}/{module_name}.{system_soabi}.so'

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
		"""Log a message to the console."""
		self.setLevel(level)
		for handler in self.handlers:
			if isinstance(handler, StreamHandler):
				handler.setLevel(level)
	
	def log_to_file(self, level: int = INFO) -> None:
		"""Log a message to the file."""
		self.setLevel(level)
		for handler in self.handlers:
			if isinstance(handler, FileHandler) or isinstance(handler, RotatingFileHandler):
				handler.setLevel(level)


# Initialize a custom logger named "PPP" with default logging level INFO
# This logger will output logs with a specified format to the console
logger = CustomLogger("PPP", level = DEBUG, log_to_file = True, log_file_path = "logs/app.log")


def remove_duplicates(items: List[str]) -> List[str]:
	"""Remove duplicate entries while preserving order."""
	seen_items = set(); return [item for item in items if not (item in seen_items or seen_items.add(item))]


def dump(filepath: str, text: str) -> None:
	"""Write text data to a specified file synchronously."""
	# Make the directory if it doesn't exist
	os.makedirs(os.path.dirname(filepath), exist_ok = True)
	
	with open(filepath, "w") as fp:
		logger.debug("Writing to file: %s", filepath)
		fp.write(str(text))


async def fetch_resources_and_dump() -> None:
	"""Fetch resources, parse JSON, and dump results to file."""
	try:
		json_data = resources.fetch_resources()
		parsed_data = json.loads(json_data)
		
		# Iterate over the parsed resources and write to file
		for data in parsed_data:
			name = data.get("name")
			raw_results = data.get("rawResults").splitlines()
			joined_results = "\n".join(remove_duplicates(raw_results))
			filepath = "." + data.get("filepath")
			dump(filepath, joined_results)
			logger.info("Dump success for %s", name)
	
	except json.JSONDecodeError as error:
		logger.error("Error decoding JSON: %s", error)


def read_channels_data(filepath: str) -> List[Dict]:
	"""Read and parse the JSON data from the given file."""
	try:
		with open(filepath) as fp:
			return json.load(fp)
	except Exception as error:
		logger.error("Error reading channels data: %s", error)
		return []


def extract_urls(raw_content: str) -> str:
	"""Extract and return the URLs from raw content based on a pattern."""
	pattern = r'(?:vless|vmess|ss|trojan)://[^\s#]+(?:#[^\s]*)?'
	urls = findall(pattern, raw_content)[::-1]  # Reverse the order of the URLs
	return '\n'.join(urls)


def process_item(item: Dict, filepath: str) -> None:
	"""Process a single item by extracting URLs and dumping the data."""
	raw_content = item.get("rawResults", "")
	urls = extract_urls(raw_content)
	
	if urls.strip():
		dump(filepath, urls)
		logger.info("Dump successful for %s", item.get("name"))
	else:
		logger.warning("Unsuccessful dump for %s due to empty result", item.get("name"))


async def fetch_tg_channels() -> None:
	"""Fetch Telegram channels and dump relevant URLs."""
	tg_channels_file = f"{workflow_dir}/data/tgchannels.json"
	
	# Read the channels data from the file
	channels = await read_channels_data(tg_channels_file)
	
	if not channels:
		logger.warning("No channels data found.")
		return None
	
	json_data = json.dumps(channels)
	data = resources.fetch_tg_channels(json_data)
	parsed_data = json.loads(data)
	
	# Process each parsed item
	for item in parsed_data:
		filepath = "." + item.get("filepath")
		await process_item(item, filepath)


async def main() -> None:
	"""Main async entry point for fetching and dumping resources."""
	# Directly await both fetch tasks concurrently
	try:
		await asyncio.gather(
			fetch_tg_channels(),  # Fetch Telegram channels
			fetch_resources_and_dump(),  # Fetch resources and dump
			return_exceptions = True
		)
	except Exception as error:
		logger.error("An error occurred during execution: %s", error)


if __name__ == "__main__":
	# Use ProactorEventLoop (normally for Windows, but can be used on Linux as well)
	# asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
	
	# The default event loop on Linux is SelectorEventLoop, which is suitable for most applications
	# and works efficiently with Linux's native event-handling mechanisms like epoll
	asyncio.run(main())
