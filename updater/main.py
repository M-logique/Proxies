from argparse import ArgumentParser, Namespace
from asyncio import TimeoutError, gather, run
from base64 import b64decode
from json import loads
from logging import INFO, Formatter, Logger, StreamHandler
from os import makedirs
from os import path as _path
from os import remove, walk
from re import findall
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple

from aiohttp import ClientError, ClientSession, ClientTimeout
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# a global timeout requests. in seconds.
GLOBAL_TIMEOUT = 5
GLOBAL_FOLDER_PATH = "./proxies"




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

def parse_text(prefix: str, pattern: str, text: str) -> List[str]:
    """
    Extracts proxies from text based on a regex pattern, adds prefix to each proxy,
    and removes duplicates.
    """
    proxies = findall(pattern, text)
    proxies_with_prefix = list(set([f"{prefix}{proxy}" for proxy in proxies]))
    return proxies_with_prefix

def clean_up(folder_path: str):
    """
    Deletes all files in the specified folder. Used to clean up proxy data.
    """
    for root, _, files in walk(folder_path):
        for file in files:
            file_path = _path.join(root, file)
            try:
                remove(file_path)
                logger.debug(f"Removed file: {file_path}")
            except Exception as e:
                logger.error(f"Error removing file {file_path}: {e}")

def parse_arguments() -> Namespace:
    """
    Parses command-line arguments for logging level, timeout, and cleanup options.
    """
    parser = ArgumentParser(description="A script for scraping proxies from multiple sources.")
    
    parser.add_argument(
        '--logLevel', 
        '-l',
        type=str, 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
        default='INFO',
        help='Set the logging level (default: INFO)'
    )

    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=5,
        help="Set the global timeout, in seconds. (default: 20)"
    )
    
    parser.add_argument(
        "--cleanup",
        "-cl",
        type=lambda x: str(x).lower().strip() == "true" or str(x).lower().strip() == "1",
        default="true",
        help="Cleans the proxies folder up. (default: true)"
    )

    return parser.parse_args()


class RegularResources:
    """
    Holds different proxy resources with associated protocols and URL sources.
    Each dictionary (e.g., http, socks4, socks5) includes a regex for extracting
    proxies, a prefix, and a list of URLs to scrape data from.
    """
    

    filepath: str = GLOBAL_FOLDER_PATH+"/regular/{}.txt"

    http: Dict[str, Any] = {
        "regex": r"\b\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}\b",
        "prefix": "http://",
        "resources": (
            # List of HTTP proxy resources
            "https://api.proxyscrape.com/?request=displayproxies&proxytype=http",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://www.proxyscan.io/download?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://api.openproxylist.xyz/http.txt",
            "https://raw.githubusercontent.com/shiftytr/proxy-list/master/proxy.txt",
            "http://alexa.lr2b.com/proxylist.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
            "https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt",
            "https://proxy-spider.com/api/proxies.example.txt",
            "https://multiproxy.org/txt_all/proxy.txt",
            "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
            "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/http.txt",
            "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/https.txt",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
            "https://openproxylist.xyz/http.txt",
            "https://proxyspace.pro/http.txt",
            "https://proxyspace.pro/https.txt",
            "https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",
            "https://raw.githubusercontent.com/aslisk/proxyhttps/main/https.txt",
            "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/HTTP.txt",
            "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
            "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
            "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
            "https://raw.githubusercontent.com/RX4096/proxy-list/main/online/http.txt",
            "https://raw.githubusercontent.com/RX4096/proxy-list/main/online/https.txt",
            "https://raw.githubusercontent.com/saisuiu/uiu/main/free.txt",
            "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://rootjazz.com/proxies/proxies.txt",
            "https://sheesh.rip/http.txt",
            "https://www.proxy-list.download/api/v1/get?type=https",
        )
    }

    socks4: Dict[str, Any] = {
        "regex": r"\b\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}\b",
        "prefix": "socks4://",
        "resources": (
            # List of SOCKS4 proxy resources
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4",
            "https://openproxylist.xyz/socks4.txt",
            "https://proxyspace.pro/socks4.txt",
            "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS4.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
            "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
            "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks4.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
            "https://www.proxy-list.download/api/v1/get?type=socks4",
            "https://www.proxyscan.io/download?type=socks4",
            "https://api.proxyscrape.com/?request=displayproxies&proxytype=socks4&country=all",
            "https://api.openproxylist.xyz/socks4.txt",
        )
    }

    socks5: Dict[str, Any] = {
        "regex": r"\b\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}\b",
        "prefix": "socks5://",
        "resources": (
            # List of SOCKS5 proxy resources
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all&simplified=true",
            "https://www.proxy-list.download/api/v1/get?type=socks5",
            "https://www.proxyscan.io/download?type=socks5",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
            "https://api.openproxylist.xyz/socks5.txt",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
            "https://openproxylist.xyz/socks5.txt",
            "https://proxyspace.pro/socks5.txt",
            "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
            "https://raw.githubusercontent.com/manuGMG/proxy-365/main/SOCKS5.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
            "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
            "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
        )
    }

    
class SpecialResources:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    async def barry_far(self):
        """
        Fetches proxy configuration files from Barry Far's GitHub, parses them,
        and stores them in the local directory.
        """

        filepath: str = self.filepath + "/v2ray/mixed.txt"
        urls: Tuple[str, ...] = (
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub3.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub4.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub5.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub5.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub6.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub7.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub8.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub9.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub10.txt"
        )

        # Fetch content from all URLs concurrently
        raw_results = await gather(
            *(fetch_and_read(url) for url in urls)
        )

        # Filter out empty results
        raw_results = (i for i in raw_results if i is not None)

        # Parse proxies from results
        parsed_results = parse_text(
            "",
            pattern=r'(?:vless|vmess|ss|trojan)://[^\s#]+(?:#[^\s]*)?',
            text='\n'.join(raw_results),
        )

        dump(filepath=filepath, text='\n'.join(parsed_results))
        logger.info("Barry Far resources dump successful")

    async def mahsa_normal(self):
        # Encryption key and IV for decrypting the received file
        key = "ca815ecfdb1f153a"
        iv = "lvcas56410c97lpb"
        
        # URL of the encrypted file and the path to store the final file
        url = "https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/app/sub.txt"
        filepath: str = self.filepath + "/v2ray/mahsa-normal.txt"

        # Create an HTTP session with a specified timeout
        async with ClientSession(timeout=ClientTimeout(total=GLOBAL_TIMEOUT)) as session:
            # Fetch data from the URL
            async with session.get(url) as resp:
                # Check the response status
                if resp.status != 200:
                    return logger.error("Failed to fetch mahsa configs")
                
                logger.debug("Mahsa fetch was successful")

                # Read the encrypted text
                encrypted_text = await resp.text()
                encrypted_bytes = b64decode(encrypted_text)
                key_bytes = key.encode('utf-8')
                iv_bytes = iv.encode('utf-8')

                # Decrypt the text using AES-CBC mode
                cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
                decrypted = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
                decrypted_text = decrypted.decode('utf-8')
                json_data = loads(decrypted_text)

                # Extract URLs from the JSON data
                urls = [
                    item.get('config', "Error: 'config' key not found in the decrypted JSON.") 
                    for item in json_data['mtn']+json_data["mci"]
                ]

                logger.debug("Mahsa's decryption successful, %d URLs loaded", len(urls))

                # Parse URLs using the specified regex pattern
                parsed_results = parse_text(
                    "",
                    pattern=r'(?:vless|vmess|ss|trojan)://[^\s#]+(?:#[^\s]*)?',
                    text='\n'.join(urls),
                )

                # Save parsed URLs to file
                dump(filepath=filepath, text='\n'.join(parsed_results))
                logger.info("Mahsa resources dump successful")

    async def mci_mtn(self):
        # Start an HTTP session with a specified timeout
        async with ClientSession(timeout=ClientTimeout(total=GLOBAL_TIMEOUT)) as session:
            mci, mtn, mkh, miner, warp = [], [], [], [], []

            # Loop to fetch MTN data files
            for num in range(4):
                url = f"https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/mtn/sub_{num + 1}.txt"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.text()
                        mtn += b64decode(data).decode('utf-8').splitlines()

            # Loop to fetch MCI data files
            for num in range(4):
                url = f"https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/mci/sub_{num + 1}.txt"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.text()
                        mci += b64decode(data).decode('utf-8').splitlines()

            # Fetch additional Warp data
            async with session.get("https://raw.githubusercontent.com/proSSHvpn/proSSHvpn/main/ProSSH-ALL") as response:
                if response.status == 200:
                    warp += (await response.text()).splitlines()
            
            # Combine all fetched data into single strings
            mci_data = "\n".join(mci)
            mtn_data = "\n".join(mtn)

            warp_data = "\n".join(warp)

            logger.info("V2ray data fetched and combined successfully.")
            
            # Save each data type to respective files
            dump(self.filepath+"/v2ray/mci.txt", mci_data)
            dump(self.filepath+"/v2ray/mtn.txt", mtn_data)
            dump(self.filepath+"/v2ray/warp.txt", warp_data)


async def fetch_and_read(url: str) -> Optional[str]:
    """
    Fetches and reads the content of a URL with a specified timeout.
    """
    async with ClientSession() as session:
        try:
            async with session.get(url, timeout=ClientTimeout(total=GLOBAL_TIMEOUT)) as resp:
                text = await resp.text()
                logger.debug(
                    "Fetched text with the length of %d from the url %s",
                    len(text.splitlines()),
                    url
                )
                return text
        except (ClientError, TimeoutError) as err:
            logger.error(f"Failed to fetch URL {url}: {err}")
            return None

async def fetch_all(urls: Sequence[Any]):
    """
    Iterates over URLs, fetches each one, and yields content if available.
    """
    for url in urls:
        resp = await fetch_and_read(url)
        logger.debug(f"Fetching URL: {url}")
        if resp:
            yield resp

def dump(filepath: str, text: str):
    """
    Writes text data to a file at the specified path.
    """
    makedirs(_path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as fp:
        logger.debug("Writing to file: %s", filepath)
        fp.write(str(text))
        

async def write_in_file(name: str, t: Dict[str, Any], filepath: str) -> None:
    """
    Fetches and writes proxies to a file, based on the specified protocol configuration.
    """
    if not isinstance(t, dict): return
    
    urls: Tuple[str, ...] = t.get("resources", tuple())
    results = [i async for i in fetch_all(urls)]
    joined_results = "\n".join(results)
    parsed_results_lst = parse_text(
        t.get("prefix", ""), 
        t.get("regex", r""), 
        joined_results
    )

    parsed_results = "\n".join(parsed_results_lst)
    path = filepath.format(name)
    dump(path, parsed_results)
    logger.info("Wrote %d lines of %s proxies in %s", len(parsed_results.splitlines()), name, path)

        

def iterate_class_vars(obj: Any) -> Generator[Any, Any, None]: #type:ignore
    """
    Iterates over all non-callable (variable) attributes of a class instance, excluding special attributes (those starting with '__').
    Yields each variable name and its corresponding value as a tuple.
    """
    for i in dir(obj):
        # Check if the attribute is not callable and does not start with '__'
        if not callable(getattr(obj, i)) and not i.startswith("__"):
            yield i, getattr(obj, i)  # Yield the attribute name and its value

def iterate_class_methods(obj: Any) -> Generator[Any, Any, None]: #type:ignore
    """
    Iterates over all callable (method) attributes of a class instance, excluding special attributes (those starting with '__').
    Yields each method name and the method itself as a tuple.
    """
    for i in dir(obj):
        # Check if the attribute is callable and does not start with '__'
        if callable(getattr(obj, i)) and not i.startswith("__"):
            yield i, getattr(obj, i)  # Yield the method name and the method itself


async def main():
    """
    Main function for initializing logging, parsing arguments, cleaning up files,
    and fetching proxy data.
    """
    args = parse_arguments()
    level = getattr(__import__("logging"), args.logLevel)

    logger.setLevel(level)

    # Set global timeout from arguments
    global GLOBAL_TIMEOUT
    GLOBAL_TIMEOUT = args.timeout

    # Cleanup option if specified
    if args.cleanup:
        logger.info("Cleaning up")
        clean_up(GLOBAL_FOLDER_PATH)

    logger.info("Started the job")

    # Regular protocols
    rrobj = RegularResources()
    logger.info("fetching regular protocols")
    await gather(
        *(
            write_in_file(
                name=name,
                t=t,
                filepath=rrobj.filepath
            ) #type:ignore
            for name, t in iterate_class_vars(rrobj)
        )
    )


    # Special protocols
    srobj = SpecialResources(GLOBAL_FOLDER_PATH)
    await gather(
        *(method() for _, method in iterate_class_methods(srobj))
    )

    logger.info("Job done")

if __name__ == "__main__":
    try:
        run(main())
    except KeyboardInterrupt:
        logger.info("Closing the program")
