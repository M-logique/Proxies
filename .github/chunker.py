from pathlib import Path
from typing import List, TypeVar
from glob import iglob

T = TypeVar('T')

def load_proxies() -> List[str]:
    configs = []

    for f in iglob("proxies/**/*.txt"):
        with open(f) as fp:
            configs.extend(fp.read().splitlines())

    return configs    


def chunk_evenly(data: List[T], parts: int) -> List[List[T]]:
    n = len(data)
    k, m = divmod(n, parts)
    return [data[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(parts)]

def main():

    chunks_path = Path("chunks")
    chunks_path.mkdir(exist_ok=True)

    proxies = load_proxies()

    chunks = chunk_evenly(proxies, 20)

    for i, chunk in enumerate(chunks):
        
        with open(chunks_path / f"chunk-{i+1}.txt", "w") as fp:
            fp.write("\n".join(chunk))





if __name__ == "__main__":
    main()