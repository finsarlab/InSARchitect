from ...models import ProjectConfig
import boto3

def download_orbits(config: ProjectConfig):
    print(config)
