import aws_cdk as cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_sns as sns,
    aws_dynamodb as dynamodb,
)
from constructs import Construct

class StorageStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # S3 Bucket (TestBucket)
        self.bucket = s3.Bucket(
            self, "TestBucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # DynamoDB Table: S3-object-size-history
        # Partition key: bucket_name 
        # Sort key: timestamp 
        self.table = dynamodb.Table(
            self, "S3ObjectSizeHistory",
            partition_key=dynamodb.Attribute(
                name="bucket_name",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # GSI: to query max size across all buckets
        # Partition key: a constant value to allow querying all items
        # Sort key: total_size for efficient max size lookup
        self.table.add_global_secondary_index(
            index_name="AllBucketsSizeIndex",
            partition_key=dynamodb.Attribute(
                name="record_type",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="total_size",
                type=dynamodb.AttributeType.NUMBER,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # SNS topic for S3 events (avoids cross-stack cycle with LambdaStack)
        self.size_tracking_topic = sns.Topic(self, "SizeTrackingTopic")

        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.SnsDestination(self.size_tracking_topic),
        )
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED,
            s3n.SnsDestination(self.size_tracking_topic),
        )

        # Outputs
        cdk.CfnOutput(self, "BucketName", value=self.bucket.bucket_name)
        cdk.CfnOutput(self, "TableName", value=self.table.table_name)