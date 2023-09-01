# Copyright 2022 Inductor, Inc.

"""ECS EC2 Component Resources"""

import base64
import json
import textwrap
from typing import List

import pulumi
import pulumi_aws as aws

import config


class Cluster(pulumi.ComponentResource):
    """ECS Cluster Component Resource"""

    def __init__(self,
        resource_name_prefix: str,
        vpc_id: str,
        cluster_name: str,
        ec2_config: config.EC2Config,
        max_instance_count: int,
        min_instance_count: int,
        subnet_ids: List[str],
        opts=None):
        """Create an ECS Cluster and associated resources.

        Resources created:
        - Security Group
        - IAM Role and Profile
        - Launch Template
        - Auto Scaling Group
        - ECS Cluster
        - Capacity Provider
        - Cluster Capacity Provider
        
        Args:
            resource_name_prefix: Prefix to use for all resources
                created by this component.
            vpc_id: VPC to create the cluster in.
            cluster_name: Name of the cluster.
            ec2_config: Configuration for the EC2 instances.
            max_instance_count: Maximum number of instances to run.
            min_instance_count: Minimum number of instances to run.
            subnet_ids: Subnets to use for the EC2 instances.
            opts: Optional pulumi resource options.
        """
        self.resource_name_prefix = resource_name_prefix + "-ecs-cluster"
        super().__init__(
            "ind:ecs:Cluster",
            self.resource_name_prefix,
            {},
            opts)

        # Security Group
        # - EC2 instance can only be accessed via the load balancer.
        self.security_group = aws.ec2.SecurityGroup(
            self.resource_name_prefix + "-sg",
            vpc_id=vpc_id,
            description="Inbound: HTTP from LB. Outbound: Any.",
            opts=pulumi.ResourceOptions(parent=self)
        )
        aws.ec2.SecurityGroupRule(
            self.resource_name_prefix + "-sg-ingress",
            type="ingress",
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
            ipv6_cidr_blocks=["::/0"],
            security_group_id=self.security_group.id,
            opts=pulumi.ResourceOptions(parent=self)
        )
        aws.ec2.SecurityGroupRule(
            self.resource_name_prefix + "-sg-engress",
            type="egress",
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
            ipv6_cidr_blocks=["::/0"],
            security_group_id=self.security_group.id,
            opts=pulumi.ResourceOptions(parent=self)
        )

        # IAM Role and Profile
        # - Permissions for the EC2 instances to connect to the ECS cluster.
        self.ecs_instance_role = aws.iam.Role(
            self.resource_name_prefix + "ecs-instance-role",
            assume_role_policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement":
                    [
                        {
                            "Sid": "",
                            "Effect": "Allow",
                            "Principal": {"Service": "ec2.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ],
                }
            ),
            opts=pulumi.ResourceOptions(parent=self)
        )
        self.ecs_instance_role_policy_attach = aws.iam.RolePolicyAttachment(
            self.resource_name_prefix + "ecs-instance-policy-attach",
            role=self.ecs_instance_role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role",
            opts=pulumi.ResourceOptions(parent=self)
        )
        self.ecs_instance_profile = aws.iam.InstanceProfile(
            self.resource_name_prefix + "ecs-iam-instance-profile",
            role=self.ecs_instance_role.name,
            opts=pulumi.ResourceOptions(parent=self))

        # User Data
        # - Connects the EC2 instances to the ECS cluster.
        ec2_user_data = textwrap.dedent(f"""
            #!/bin/bash
            echo ECS_CLUSTER={cluster_name} >> /etc/ecs/ecs.config
        """)
        ec2_user_data = pulumi.Output.all(ec2_user_data).apply(
            lambda args: base64.b64encode(args[0].encode()).decode())

        self.launch_template = aws.ec2.LaunchTemplate(
            self.resource_name_prefix + "launch-template",
            iam_instance_profile=aws.ec2.LaunchTemplateIamInstanceProfileArgs(
                arn=self.ecs_instance_profile.arn,
            ),
            network_interfaces=[
                aws.ec2.LaunchTemplateNetworkInterfaceArgs(
                    associate_public_ip_address=True,
                    security_groups=[self.security_group.id],
                ),
            ],
            image_id=ec2_config.ami_id,
            instance_type=ec2_config.instance_type,
            key_name=ec2_config.key_name,
            name=ec2_config.template_name,
            user_data=ec2_user_data,
            opts=pulumi.ResourceOptions(parent=self)
        )
        self.autoscaling_group = aws.autoscaling.Group(
            self.resource_name_prefix + "autoscaling_group",
            desired_capacity=0,  # Scaling is handled by the Capacity Provider
            min_size=min_instance_count,
            max_size=max_instance_count,
            vpc_zone_identifiers=subnet_ids,
            launch_template=aws.autoscaling.GroupLaunchTemplateArgs(
                id=self.launch_template.id,
                version="$Latest",
            ),
            protect_from_scale_in=True,
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.cluster = aws.ecs.Cluster(
            self.resource_name_prefix + "cluster",
            name=cluster_name,
            opts=pulumi.ResourceOptions(parent=self)
        )
        self.capacity_provider = aws.ecs.CapacityProvider(
            self.resource_name_prefix + "capacity-provider",
            auto_scaling_group_provider=aws.ecs.CapacityProviderAutoScalingGroupProviderArgs(
                auto_scaling_group_arn=self.autoscaling_group.arn,
                managed_termination_protection="ENABLED",
                managed_scaling=aws.ecs.CapacityProviderAutoScalingGroupProviderManagedScalingArgs(
                    maximum_scaling_step_size=1000,
                    minimum_scaling_step_size=1,
                    status="ENABLED",
                    target_capacity=10,
                ),
            ),
            opts=pulumi.ResourceOptions(parent=self)
        )
        self.cluster_capacity_providers = aws.ecs.ClusterCapacityProviders(
            self.resource_name_prefix + "cluster-capacity-provider",
            cluster_name=self.cluster.name,
            capacity_providers=[self.capacity_provider.name],
            default_capacity_provider_strategies=[
                aws.ecs.ClusterCapacityProvidersDefaultCapacityProviderStrategyArgs(
                    base=1,
                    weight=100,
                    capacity_provider=self.capacity_provider.name)],
            opts=pulumi.ResourceOptions(parent=self)
        )


class Service(pulumi.ComponentResource):
    """ECS Service Component Resource"""

    def __init__(self,
        resource_name_prefix: str,
        cluster_arn: str,
        task_definition_arn: str,
        target_group_arn: str,
        security_group_ids: List[str],
        container_name: str,
        subnet_ids: List[str],
        desired_task_count: int,
        opts=None):
        """Create an ECS Service.
        
        Args:
            resource_name_prefix: Prefix to use for all resources
                created by this component.
            cluster_arn: ARN of the ECS cluster.
            task_definition_arn: ARN of the ECS task definition.
            target_group_arn: ARN of the load balancer target group.
            security_group_ids: Security groups to use for the ECS service.
            container_name: Name of the container.
            subnet_ids: Subnets to use for the ECS service.
            desired_task_count: Number of tasks to run.
            opts: Optional pulumi resource options.
        """
        self.resource_name_prefix = resource_name_prefix + "-ecs-service"
        super().__init__(
            "ind:ecs:Service",
            self.resource_name_prefix,
            {},
            opts)

        self.service = aws.ecs.Service(
            self.resource_name_prefix + "-service",
            cluster=cluster_arn,
            launch_type="EC2",
            desired_count=desired_task_count,
            task_definition=task_definition_arn,
            network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                assign_public_ip=False,
                subnets=subnet_ids,
                security_groups=security_group_ids,
            ),
            load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
                target_group_arn=target_group_arn,
                container_name=container_name,
                container_port=80,
            )],
            opts=pulumi.ResourceOptions(parent=self)
        )


class Task(pulumi.ComponentResource):
    """ECS Task Component Resource"""

    def __init__(self,
        resource_name_prefix: str,
        family_name: str,
        container_name: str,
        container_image: str,
        opts=None):
        """Create an ECS Task and associated resources.

        Resources created:
        - IAM Role
        - Task Definition
        
        Args:
            resource_name_prefix: Prefix to use for all resources
                created by this component.
            family_name: Unique name for your task definition.
            container_name: Name of a container.
            container_image: Image used to start a container.
            opts: Optional pulumi resource options.
        """
        self.resource_name_prefix = resource_name_prefix + "-ecs-task"
        super().__init__(
            "ind:ecs:Task",
            self.resource_name_prefix,
            {},
            opts)

        # IAM role:
        # - To allow the Task Definition to launch tasks on the cluster.
        self.task_execution_role = aws.iam.Role(
            self.resource_name_prefix + "task-execution-role",
            assume_role_policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement":
                    [
                        {
                            "Sid": "",
                            "Effect": "Allow",
                            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ],
                }
            ),
            opts=pulumi.ResourceOptions(parent=self)
        )
        self.task_execution_role_policy_attach = aws.iam.RolePolicyAttachment(
            self.resource_name_prefix + "task-excution-policy-attach",
            role=self.task_execution_role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
            opts=pulumi.ResourceOptions(parent=self)
        )

        self.task_definition = aws.ecs.TaskDefinition(
            self.resource_name_prefix + "-task-definition",
            family=family_name,
            cpu="256",
            memory="512",
            network_mode="awsvpc",
            requires_compatibilities=["EC2"],
            execution_role_arn=self.task_execution_role.arn,
            container_definitions=pulumi.Output.json_dumps([{
                "name": container_name,
                "image": container_image,
                "portMappings": [{
                    "containerPort": 80,
                    "hostPort": 80,
                    "protocol": "tcp"
                }]
            }]),
            opts=pulumi.ResourceOptions(parent=self)
        )
