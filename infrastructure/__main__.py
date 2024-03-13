# Copyright 2022 Inductor, Inc.

"""Entrypoint for Inductor Infrastructure."""

import pulumi_aws as aws
import pulumi_awsx as awsx


import config
from util import ecs_ec2, lb, rds
# sa
# Network
availability_zone_names = aws.get_availability_zones(
    state="available"
).names[:config.NUMBER_OF_AVAILABILITY_ZONES]
vpc = awsx.ec2.Vpc(
    config.RESOURCE_NAME_PREFIX + "-vpc",
    availability_zone_names=availability_zone_names,
    nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(strategy="None")
)
# load_balancer = lb.LoadBalancer(
#     config.RESOURCE_NAME_PREFIX,
#     vpc_id=vpc.vpc_id,
#     subnet_ids=vpc.public_subnet_ids,
# )
# load_balancer.add_dns_record(config.lb.domain_name)
# target_group = load_balancer.add_target_group(config.lb.health_check_path)
# listener = load_balancer.add_listener(config.lb.domain_name, target_group)


# # ECR
# repository = awsx.ecr.Repository(
#     config.RESOURCE_NAME_PREFIX + "-repository")
# image = awsx.ecr.Image(
#     config.RESOURCE_NAME_PREFIX + "-image",
#     repository_url=repository.url,
#     path=config.DOCKER_BUILD_SOURCE)


# # ECS
# cluster = ecs_ec2.Cluster(
#     config.RESOURCE_NAME_PREFIX,
#     vpc_id=vpc.vpc_id,
#     cluster_name=config.ecs.cluster_name,
#     ec2_config=config.ecs_ec2,
#     max_instance_count=config.ecs.max_instance_count,
#     min_instance_count=config.ecs.min_instance_count,
#     subnet_ids=vpc.public_subnet_ids,
# )
# task = ecs_ec2.Task(
#     config.RESOURCE_NAME_PREFIX,
#     family_name=config.ecs.task_family_name,
#     container_name=config.ecs.container_name,
#     container_image=image.image_uri,
# )
# service = ecs_ec2.Service(
#     config.RESOURCE_NAME_PREFIX,
#     cluster_arn=cluster.cluster.arn,
#     task_definition_arn=task.task_definition.arn,
#     target_group_arn=target_group.arn,
#     security_group_ids=[cluster.security_group.id],
#     container_name=config.ecs.container_name,
#     subnet_ids=vpc.public_subnet_ids,
#     desired_task_count=config.ecs.desired_task_count,
# )


# RDS
# database = rds.RDS(
#     config.RESOURCE_NAME_PREFIX,
#     rds_config=config.rds,
#     vpc_id=vpc.vpc_id,
#     subnet_ids=vpc.private_subnet_ids,
#     access_security_groups=[cluster.security_group.id],
# )
