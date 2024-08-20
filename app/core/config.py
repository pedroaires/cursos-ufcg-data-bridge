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


def parse_config(path=None, tag='!ENV'):
    """
    Load a YAML configuration file and resolve any environment variables.
    
    The environment variables must have !ENV before them and be in the format:
    ${VAR_NAME}. For example:
    
    database:
        host: !ENV ${HOST}
        port: !ENV ${PORT}
    
    :param str path: Path to the YAML file.
    :param str tag: The tag to identify environment variables.
    :return: The parsed configuration as a dictionary.
    :rtype: dict
    """
    
    pattern = re.compile(r'\${(\w+)}')  
    loader = yaml.SafeLoader
    loader.add_implicit_resolver(tag, pattern, None)

    def env_constructor(loader, node):
        """Custom constructor to replace environment variables in YAML."""
        value = loader.construct_scalar(node)
        matches = pattern.findall(value)
        for var in matches:
            value = value.replace(f'${{{var}}}', os.getenv(var, var))
        return value

    loader.add_constructor(tag, env_constructor)
    
    if path:
        with open(path) as file:
            return yaml.load(file, Loader=loader)
    else:
        raise ValueError('You must provide either a path or YAML data.')
    

def load_config(env: str) -> Settings:
    config = parse_config("config/config.yaml")
    return Settings(**config[env])

ENV = os.getenv("ENVIRONMENT", "development")
settings = load_config(ENV)