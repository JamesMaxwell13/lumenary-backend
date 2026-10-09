import json
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the bundled MinIO media bucket and apply its public read policy."

    def handle(self, *args, **options):
        endpoint = settings.AWS_S3_ENDPOINT_URL
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        if not endpoint or not bucket:
            raise CommandError("AWS_S3_ENDPOINT_URL and AWS_STORAGE_BUCKET_NAME are required.")

        hostname = urlparse(endpoint).hostname
        if hostname not in {"minio", "localhost", "127.0.0.1"}:
            raise CommandError("This command is restricted to the bundled MinIO service.")

        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(
                signature_version=settings.AWS_S3_SIGNATURE_VERSION,
                s3={"addressing_style": settings.AWS_S3_ADDRESSING_STYLE},
            ),
        )

        try:
            client.head_bucket(Bucket=bucket)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code not in {"404", "NoSuchBucket", "NotFound"}:
                raise CommandError(f"Unable to inspect MinIO bucket: {code}") from exc
            client.create_bucket(Bucket=bucket)
            self.stdout.write(f"Created MinIO bucket: {bucket}")

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/*"],
                }
            ],
        }
        client.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
        self.stdout.write(self.style.SUCCESS(f"MinIO bucket is ready: {bucket}"))
