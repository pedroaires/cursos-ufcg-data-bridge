import yaml
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
import re

load_dotenv()

class Settings(BaseSettings):
    auth_url: str
    base_url: str
    username: str
    password: str
    database_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


def resolve_env_variables(value, pattern):
    """Resolve environment variables in a string."""
    matches = pattern.findall(value)
    for var in matches:
        value = value.replace(f'${{{var}}}', os.getenv(var, var))
    return value

def setup_yaml_loader(tag='!ENV'):
    """Set up a YAML loader that resolves environment variables."""
    pattern = re.compile(r'\${(\w+)}')
    loader = yaml.SafeLoader
    loader.add_implicit_resolver(tag, pattern, None)

    def env_constructor(loader, node):
        """Custom constructor to replace environment variables in YAML."""
        value = loader.construct_scalar(node)
        return resolve_env_variables(value, pattern)

    loader.add_constructor(tag, env_constructor)
    return loader

def load_yaml_file(path, loader):
    """Load a YAML file from the given path using the specified loader."""
    if not path:
        raise ValueError('You must provide a path to the YAML file.')
    
    with open(path, 'r') as file:
        return yaml.load(file, Loader=loader)

def load_config(env: str) -> Settings:
    """Load the configuration settings for the specified environment."""
    loader = setup_yaml_loader()
    config = load_yaml_file('config/config.yaml', loader)
    return Settings(**config[env])

def load_column_mappings() -> dict:
    """Load column mappings from a YAML file"""
    loader = setup_yaml_loader()
    mappings = load_yaml_file("config/cols_mapping.yaml", loader)
    return mappings

ENV = os.getenv("ENVIRONMENT", "development")
settings = load_config(ENV)