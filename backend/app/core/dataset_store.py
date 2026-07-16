import os
import json
import uuid
import pandas as pd
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()

DEFAULT_STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))
STORAGE_DIR = os.path.abspath(os.getenv("SAAR_STORAGE_DIR", DEFAULT_STORAGE_DIR))
REGISTRY_PATH = os.path.join(STORAGE_DIR, "registry.json")

# Ensure storage directory exists
os.makedirs(STORAGE_DIR, exist_ok=True)

class DatasetStore:
    """
    Manages the physical files and metadata registry for uploaded datasets.
    Stores metadata in a simple registry.json file.
    """

    @staticmethod
    def _load_registry() -> Dict[str, Any]:
        if not os.path.exists(REGISTRY_PATH):
            return {}
        try:
            with open(REGISTRY_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error("failed_to_load_registry", error=str(e))
            return {}

    @staticmethod
    def _save_registry(registry: Dict[str, Any]):
        try:
            with open(REGISTRY_PATH, "w") as f:
                json.dump(registry, f, indent=2)
        except Exception as e:
            logger.error("failed_to_save_registry", error=str(e))

    @classmethod
    def register_dataset(cls, filename: str, file_path: str) -> str:
        """
        Generates a unique dataset_id, copies/moves the file to storage,
        and creates a registry entry.
        """
        dataset_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1].lower()
        new_path = os.path.join(STORAGE_DIR, f"{dataset_id}{ext}")
        
        # Copy file to storage location
        import shutil
        shutil.copy2(file_path, new_path)
        
        registry = cls._load_registry()
        registry[dataset_id] = {
            "id": dataset_id,
            "filename": filename,
            "file_path": new_path,
            "format": ext.replace(".", ""),
            "status": "upload_completed",
            "metadata": {},
            "schema": {},
            "eda": {},
            "cleaning_history": [],
            "ml_recommendations": {},
            "ai_insights": {}
        }
        cls._save_registry(registry)
        logger.info("dataset_registered", dataset_id=dataset_id, filename=filename)
        return dataset_id

    @classmethod
    def update_dataset(cls, dataset_id: str, update_dict: Dict[str, Any]):
        """
        Updates metadata or analysis results in the registry.
        """
        registry = cls._load_registry()
        if dataset_id not in registry:
            raise KeyError(f"Dataset {dataset_id} not found in registry.")
        
        for key, val in update_dict.items():
            registry[dataset_id][key] = val
            
        cls._save_registry(registry)
        logger.debug("dataset_updated", dataset_id=dataset_id, keys=list(update_dict.keys()))

    @classmethod
    def get_dataset(cls, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves registry entry for a dataset.
        """
        registry = cls._load_registry()
        return registry.get(dataset_id)

    @classmethod
    def get_all_datasets(cls) -> List[Dict[str, Any]]:
        """
        Retrieves all registered datasets.
        """
        registry = cls._load_registry()
        return list(registry.values())

    @classmethod
    def get_dataframe(cls, dataset_id: str) -> pd.DataFrame:
        """
        Reads the dataset file into a Pandas DataFrame.
        """
        meta = cls.get_dataset(dataset_id)
        if not meta:
            raise KeyError(f"Dataset {dataset_id} not found.")
        
        file_path = meta["file_path"]
        fmt = meta["format"]
        
        if fmt == "csv":
            return pd.read_csv(file_path)
        elif fmt in ["xlsx", "xls"]:
            engine = 'openpyxl' if fmt == 'xlsx' else 'xlrd'
            return pd.read_excel(file_path, engine=engine)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    @classmethod
    def save_dataframe(cls, dataset_id: str, df: pd.DataFrame):
        """
        Saves a modified Pandas DataFrame back to disk.
        """
        meta = cls.get_dataset(dataset_id)
        if not meta:
            raise KeyError(f"Dataset {dataset_id} not found.")
        
        file_path = meta["file_path"]
        fmt = meta["format"]
        
        if fmt == "csv":
            df.to_csv(file_path, index=False)
        elif fmt in ["xlsx", "xls"]:
            engine = 'openpyxl' if fmt == 'xlsx' else None
            df.to_excel(file_path, index=False, engine=engine)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
        
        logger.info("dataframe_saved", dataset_id=dataset_id)
