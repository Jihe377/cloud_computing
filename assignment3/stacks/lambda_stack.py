import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
    aws_apigateway as apigw,
)
from constructs import Construct
from stacks.storage_stack import StorageStack

class LambdaStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, storage_stack: StorageStack, **kwargs):
        super().__init__(scope, id, **kwargs)

        bucket = storage_stack.bucket
        table = storage_stack.table

        # Size-Tracking Lambda 
        size_tracking_fn = _lambda.Function(
            self, "SizeTrackingLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/size_tracking"),
            timeout=cdk.Duration.seconds(30),
            environment={
                "TABLE_NAME": table.table_name,
                "BUCKET_NAME": bucket.bucket_name,
            },
        )

        # Permissions for size-tracking lambda
        bucket.grant_read(size_tracking_fn)
        table.grant_write_data(size_tracking_fn)

        # Subscribe to SNS topic (avoids writing back into StorageStack's bucket resource)
        size_tracking_fn.add_event_source(
            lambda_event_sources.SnsEventSource(storage_stack.size_tracking_topic)
        )

        # Plotting Lambda
        plotting_fn = _lambda.Function(
            self, "PlottingLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/plotting"),
            timeout=cdk.Duration.seconds(60),
            memory_size=512,        # matplotlib needs more memory
            layers=[
                _lambda.LayerVersion.from_layer_version_arn(
                    self, "MatplotlibLayer",
                    "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p310-matplotlib:13" 
                )
            ],
            environment={
                "TABLE_NAME": table.table_name,
                "BUCKET_NAME": bucket.bucket_name,
                "GSI_NAME": "AllBucketsSizeIndex",
            },
        )

        # Permissions for plotting lambda
        table.grant_read_data(plotting_fn)
        bucket.grant_put(plotting_fn)

        # REST API for plotting lambda
        api = apigw.LambdaRestApi(
            self, "PlottingApi",
            handler=plotting_fn,
            rest_api_name="PlottingApi",
        )

        # Driver Lambda
        driver_fn = _lambda.Function(
            self, "DriverLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/driver"),
            timeout=cdk.Duration.seconds(120),
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "PLOTTING_API_URL": api.url,   
            },
        )

        # Permissions for driver lambda
        bucket.grant_read_write(driver_fn)

        # Outputs
        cdk.CfnOutput(self, "PlottingApiUrl", value=api.url)