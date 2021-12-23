import gzip
import pickle
from io import BytesIO
from pathlib import Path
from typing import Dict

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class DataLoader:
    def __init__(self, credential: DefaultAzureCredential):
        self.credential = credential
        self.cache: Dict = {}
        if Path("cache.gz").is_file():
            with gzip.open("cache.gz", "rb") as file:
                self.cache = pickle.load(file)  # type: ignore

    def get(
        self, account_url: str, container: str, filename: str, use_cache: bool = True
    ) -> BytesIO:
        client = BlobServiceClient(
            account_url=account_url,
            credential=self.credential,
        )
        blobClient = client.get_container_client(container).get_blob_client(filename)
        if use_cache:
            data_key = f"{account_url}_{container}_{filename}"
            properties = blobClient.get_blob_properties()
            if data_key in self.cache:
                cached_last_modified = self.cache[data_key]["properties"][
                    "last_modified"
                ]
                last_modified = properties["last_modified"]
                if last_modified <= cached_last_modified:
                    print(f"Loading file {filename} from cache")
                    return BytesIO(self.cache[data_key]["data"])
            print(f"Loading file {filename} from datastore and caching")
            self.cache[data_key] = {
                "data": blobClient.download_blob().readall(),
                "properties": properties,
            }
            with gzip.open("cache.gz", "wb") as file:
                pickle.dump(self.cache, file)  # type: ignore
            return BytesIO(self.cache[data_key]["data"])
        print(f"Loading file {filename} from datastore")
        return BytesIO(blobClient.download_blob().readall())
