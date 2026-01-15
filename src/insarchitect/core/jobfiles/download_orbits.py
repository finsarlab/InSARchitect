from ...models import ProjectConfig
import boto3

def download_orbits(config: ProjectConfig):
    s3 = boto3.resource('s3')
    for bucket in s3.buckets.all():
        print(bucket.name)
