from aws_cdk import (
    Stack,
    aws_ecr_assets as ecr_assets,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_logs as logs,
    aws_servicediscovery as servicediscovery,
    aws_elasticloadbalancingv2 as elbv2,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from pathlib import Path
import json


class RagAwsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        version = kwargs.pop("version", "default-version")
        super().__init__(scope, construct_id, **kwargs)

        account = self.account
        region = self.region
        

        # VPC
        vpc = ec2.Vpc(self, "RagVpc", max_azs=2)

        # Security Group
        sg = ec2.SecurityGroup(
            self, "RagSecurityGroup",
            vpc=vpc,
            description="Allow traffic on ports 8000, 8080, and 50051",
            allow_all_outbound=True
        )
        for port in [8000, 8080, 50051]:
            sg.add_ingress_rule(peer=sg, connection=ec2.Port.tcp(port))
        sg.add_ingress_rule(peer=ec2.Peer.any_ipv4(), connection=ec2.Port.tcp(8000))

        # ECS Cluster
        cluster = ecs.Cluster(self, "RagCluster", cluster_name = f"rag-ecs-cluster-{version}",  vpc=vpc)

        # ECR Registry
        ecr_repo = ecr.Repository(
            self, "RagRegistry",
            repository_name= f"rag-registry-{version}"
        )

        # IAM Role

        task_role = iam.Role(
            self, "RagTaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Task execution role for ECS"

        )
        task_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            resources=["*"]
            )
        )
        task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"))


        # Build and upload images
        image_asset = ecr_assets.DockerImageAsset(
            self,
            "RagDockerImage",
            directory=str(Path(__file__).resolve().parents[3])  
        )



        # Task definitions
        ## rag-task

        # Logs
        rag_log_group = logs.LogGroup(
            self, 
            "RagLogGroup", 
            log_group_name=f"/ecs/rag-task-{version}",
            removal_policy= RemovalPolicy.DESTROY
        )

        # Create Fargate task definition
        rag_task_def = ecs.FargateTaskDefinition(
            self, f"rag-task",
            family=f"rag-task",
            cpu=512,
            memory_limit_mib=1024,
            execution_role=task_role,
            task_role=task_role
        )

        # Add container
        rag_container = rag_task_def.add_container(
            "RagAwsContainer",
            container_name="rag-aws-container",

            image=ecs.ContainerImage.from_docker_image_asset(image_asset),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="ecs",
                log_group=rag_log_group
                ),
            essential=True,
            environment={
                "WEAVIATE_HTTP_HOST": "weaviate.myapp.local",
                "WEAVIATE_HTTP_PORT": "8080",
                "WEAVIATE_GRPC_HOST": "weaviate.myapp.local",
                "WEAVIATE_GRPC_PORT": "50051",
                "IN_DOCKER": "1"
                }
                )

        rag_container.add_port_mappings(
            ecs.PortMapping(container_port=8000, protocol=ecs.Protocol.TCP)
            )

        ## weaviate-task
        # Logs
        weaviate_log_group = logs.LogGroup(
            self, 
            "WeaviateLogGroup", 
            log_group_name=f"/ecs/weaviate-{version}",
            removal_policy= RemovalPolicy.DESTROY
        )

        # Task definition
        weaviate_task_def = ecs.FargateTaskDefinition(
            self, f"weaviate-task",
            family=f"weaviate-task",
            cpu=512,
            memory_limit_mib=1024,
            task_role=task_role,
            execution_role=task_role
        )

        # Container definition
        weaviate_container = weaviate_task_def.add_container(
            "WeaviateContainer",
            container_name = "weaviate",
            image=ecs.ContainerImage.from_registry("semitechnologies/weaviate:latest"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="ecs",
                log_group=weaviate_log_group
            ),
            essential=True,
            environment={
                "QUERY_DEFAULTS_LIMIT": "100",
                "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED": "true",
                "PERSISTENCE_DATA_PATH": "./weaviate_data",
                "DEFAULT_VECTORIZER_MODULE": "none",
                "ENABLE_MODULES": "text2vec-openai",
                "GRPC_ENABLED": "true"
            }
        )
        # Service Discovery / Cloud Map
        namespace = servicediscovery.PrivateDnsNamespace(
            self,
            "ServiceDiscoveryNamespace",
            name="myapp.local",
            vpc=vpc,
            description="Private DNS namespace for service discovery"
        )



        # Port mappings
        weaviate_container.add_port_mappings(
            ecs.PortMapping(container_port=8080, protocol=ecs.Protocol.TCP),
            ecs.PortMapping(container_port=50051, protocol=ecs.Protocol.TCP)
        )

        # Services
        rag_service = ecs.FargateService(
            self, "RagService",
            service_name = "rag-service",
            cluster=cluster,
            task_definition=rag_task_def,
            desired_count=1,
            assign_public_ip=True,
            security_groups=[sg],
            vpc_subnets={"subnet_type": ec2.SubnetType.PUBLIC},
        )

        weaviate_service=  ecs.FargateService(
            self, "WeaviateService",
            service_name = "weaviate-service",
            cluster=cluster,
            task_definition=weaviate_task_def,
            desired_count=1,
            assign_public_ip=True,
            security_groups=[sg],
            vpc_subnets={"subnet_type": ec2.SubnetType.PUBLIC},
            cloud_map_options=ecs.CloudMapOptions(
                name="weaviate",
                cloud_map_namespace=namespace
                )
        )


        alb_sg = ec2.SecurityGroup(
            self,
            "AlbSecurityGroup",
            vpc=vpc,
            description="Allow HTTP traffic for ALB",
            allow_all_outbound=True
        )

        # Allow HTTP from anywhere (IPv4)
        alb_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP access from anywhere"
        )

        # Optional: Allow HTTP from anywhere (IPv6)
        alb_sg.add_ingress_rule(
            ec2.Peer.any_ipv6(),
            ec2.Port.tcp(80),
            "Allow HTTP access from anywhere (IPv6)"
        )

        # Allow ALB to communicate with ECS tasks (on port 8000)
        sg.add_ingress_rule(peer=alb_sg, connection=ec2.Port.tcp(8000), description="Allow traffic from ALB")


        # Create the ALB
        lb = elbv2.ApplicationLoadBalancer(
            self, "RagALB",
            vpc=vpc,
            internet_facing=True,
            idle_timeout=Duration.seconds(120),
            security_group=alb_sg
        )




        listener = lb.add_listener("Listener", port=80)


        # Add service as target
        listener.add_targets(
            "ECS",
            port=8000,
            targets=[rag_service],
            health_check=elbv2.HealthCheck(
                path="/docs",
                port="8000"
            )
        )
