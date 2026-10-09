from io import StringIO
from unittest.mock import patch

from botocore.exceptions import ClientError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings


MINIO_SETTINGS = {
    "AWS_ACCESS_KEY_ID": "lumenary",
    "AWS_SECRET_ACCESS_KEY": "secret",
    "AWS_STORAGE_BUCKET_NAME": "lumenary-media",
    "AWS_S3_ENDPOINT_URL": "http://minio:9000",
    "AWS_S3_REGION_NAME": "us-east-1",
    "AWS_S3_SIGNATURE_VERSION": "s3v4",
    "AWS_S3_ADDRESSING_STYLE": "path",
}


class EnsureMinioBucketCommandTests(SimpleTestCase):
    @override_settings(**MINIO_SETTINGS)
    @patch("cms.management.commands.ensure_minio_bucket.boto3.client")
    def test_creates_missing_bucket_and_applies_public_read_policy(self, client_factory):
        client = client_factory.return_value
        client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )

        call_command("ensure_minio_bucket", stdout=StringIO())

        client.create_bucket.assert_called_once_with(Bucket="lumenary-media")
        client.put_bucket_policy.assert_called_once()

    @override_settings(
        **{
            **MINIO_SETTINGS,
            "AWS_S3_ENDPOINT_URL": "https://s3.example.com",
        }
    )
    def test_rejects_external_s3_endpoint(self):
        with self.assertRaisesMessage(CommandError, "restricted to the bundled MinIO"):
            call_command("ensure_minio_bucket")
