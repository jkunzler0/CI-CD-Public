"""Configuration for Inductor Infrastructure.

Converts Pulumi configuration into Python variables and dataclasses.
Contains information about the configurable parameters.
Sets default values for parameters that are expected to be the same for
most stacks (dev, staging, prod).
"""

import dataclasses
import os
from typing import Optional

import pulumi


pulumi_config = pulumi.Config()


# AWS Region for all infrastructure to use.
AWS_REGION = pulumi_config.get("aws_region", default="us-east-1")


# This value is a prefix for all Pulumi resource names.
# See https://www.pulumi.com/docs/concepts/resources/names/ for more
# information about Pulumi resource names.
# We are setting an explicit prefix to make it easier to identify resources
# created by this script. Some AWS resources will derive their name in AWS
# from this prefix.
# NOTE: Having a lengthy prefix can cause some AWS resources to throw an
# error when creating them. This is because these resources have a maximum
# name length. If you encounter this error, you can try reducing the length
# of this prefix.
# NOTE: Do not change this value after creating any Pulumi resources.
# Doing so will cause Pulumi to create new resources instead of updating
# existing resources.
RESOURCE_NAME_PREFIX = pulumi_config.get("resource_name_prefix", default="ind")


NUMBER_OF_AVAILABILITY_ZONES = pulumi_config.get(
    "number_of_availability_zones", default=2)


# Path to a directory to use for the Docker build context for ECS deployment.
# It is assumed that this directory contains a Dockerfile, but more parameters
# can be added to specify a different Dockerfile.
# See https://www.pulumi.com/registry/packages/awsx/api-docs/ecr/image/
# for more information.
DOCKER_BUILD_SOURCE = os.path.abspath(
    pulumi_config.get("docker_build_source", default="../backend"))


@dataclasses.dataclass
class ECSConfig:
    """ECS configuration.
    
    Attributes:
        desired_task_count: Number of tasks to run.
        max_instance_count: Maximum number of instances to run.
        min_instance_count: Minimum number of instances to run.
        container_name: Name of the container.
        cluster_name: Name of the ECS cluster.
        task_family_name: Name of the ECS task family.
    """
    desired_task_count: Optional[int] = 1
    max_instance_count: Optional[int] = 1
    min_instance_count: Optional[int] = 0
    container_name: Optional[str] = "container-main"
    cluster_name: Optional[str] = "cluster-main"
    task_family_name: Optional[str] = "task-main"
ecs = ECSConfig(**pulumi_config.get_object("ecs", default={}))


@dataclasses.dataclass
class LBConfig:
    """Load balancer configuration.

    Required manual setup:
    1. Acquire a domain name. (This can be done through AWS Route53.)
    2. Create a public hosted zone for the domain name. (This will be done
        automatically if the domain name is acquired through AWS Route53.)
    3. Using AWS Certificate Manager (ACM), request a certificate for the
        domain name and all subdomains. (i.e. example.com and *.example.com)
    4. Create a CNAME record in the hosted zone for this certificate. (This
        can be done from the ACM console.)
    
    Attributes:
        domain_name: Domain name to use for the load balancer.
        health_check_path: Path to use for the load balancer health check.
    """
    domain_name: str
    health_check_path: Optional[str] = "/"
lb = LBConfig(**pulumi_config.get_object("lb", default={}))


@dataclasses.dataclass
class EC2Config:
    """EC2 configuration.

    Optional manual setup:
    1. Create the EC2 key pair to use for debugging.
    
    Attributes:
        ami: AMI ID to use.
        instance_type: EC2 instance type to use.
        template_name: Name of the EC2 launch template to use.
        key_name: Optional name of the SSH key to use for debugging.
    """
    # Amazon ECS-Optimized Amazon Linux 2 (AL2) arm64 AMI
    ami_id: Optional[str] = "ami-0bae8df33460eefaa"
    # If changing the ami, verify the instance type is supported.
    instance_type: Optional[str] = "t4g.small"
    template_name: Optional[str] = "template-main"
    key_name: Optional[str] = None
ecs_ec2 = EC2Config(**pulumi_config.get_object("ecs_ec2", default={}))


@dataclasses.dataclass
class RDSConfig:
    """RDS configuration.

    The master_username and master_password are not secrets as the RDS instance
    is not publicly accessible.

    See https://www.pulumi.com/registry/packages/aws/api-docs/rds/cluster/ for
    more information on the RDS cluster resource and its attributes.

    Attributes:
        engine_version: Database engine version to use.
        max_capacity: Maximum capacity for the database.
        min_capacity: Minimum capacity for the database.
        cluster_identifier: Name of the RDS cluster to create.
        database_name: Name of the database to create.
        engine: Database engine to use.
        engine_type: Database engine type to use.
        engine_mode: Database engine mode to use.
        master_username: Username for the master user.
        master_password: Password for the master user.
        instance_class: Instance class to use for the database.
        port: Port to use for the database.
    """
    # Latest engine version as of 2022-05-03
    engine_version: Optional[str] = "8.0.mysql_aurora.3.03.1"
    max_capacity: Optional[int] = 1
    min_capacity: Optional[int] = 0.5
    cluster_identifier: Optional[str] = "inductor-cloud"
    database_name: Optional[str] = "inductor"
    engine: Optional[str] = "aurora-mysql"
    engine_type: Optional[str] = "mysql"
    engine_mode: Optional[str] = "provisioned"
    master_username: Optional[str] = "inductor"
    master_password: Optional[str] = "inductor"
    instance_class: Optional[str] = "db.serverless"
    port: Optional[int] = 3306
rds=RDSConfig(**pulumi_config.get_object("rds", default={}))
