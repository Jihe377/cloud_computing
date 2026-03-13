import aws_cdk as cdk
from stacks.storage_stack import StorageStack
from stacks.lambda_stack import LambdaStack

app = cdk.App()

storage_stack = StorageStack(app, "StorageStack")
LambdaStack(app, "LambdaStack", storage_stack=storage_stack)

app.synth()