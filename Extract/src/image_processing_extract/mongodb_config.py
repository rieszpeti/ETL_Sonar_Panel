from dataclasses import dataclass, field


@dataclass
class MongoDBConfig:
    connection_string: str = field(metadata={'required': True})
    db_name: str = field(metadata={'required': True})
    collection_name: str = field(metadata={'required': True})

    def __post_init__(self):
        if not self.connection_string:
            raise ValueError("The connection string must not be empty.")
        if not self.db_name:
            raise ValueError("The database name must not be empty.")
        if not self.collection_name:
            raise ValueError("The collection name must not be empty.")