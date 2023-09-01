# Copyright 2022 Inductor, Inc.

"""RDS Component Resources"""

from typing import List, Optional

import pulumi
import pulumi_aws as aws

import config


class RDS(pulumi.ComponentResource):
    """RDS Component Resource"""

    def __init__(self,
        resource_name_prefix: str,
        rds_config: config.RDSConfig,
        vpc_id: str,
        subnet_ids: List[str],
        access_security_groups: List[aws.ec2.SecurityGroup],
        opts: Optional[pulumi.ResourceOptions] = None):
        """Creates a RDS cluster and supporting resources.

        Resources created:
        - Security Group
        - RDS Cluster
        - RDS Cluster Instance
        - RDS Cluster Subnet Group

        NOTE: Even though the RDS cluster and cluster instance are general
        resources that could be used for any RDS cluster, the arguments used
        to create each resource depend on the engine used. The arguments used
        here are the arguments required for Aurora Serverless V2. If you want
        to use a different engine, you may need to modify this component in
        addition to the RDS configuration.
        
        Args:
            resource_name_prefix: Prefix to use for all resources
                created by this component.
            rds_config: Configuration for the RDS component.
            vpc_id: VPC to create the RDS cluster in.
            subnet_ids: Subnets to create the RDS cluster in.
            access_security_groups: Security groups given access to the
                RDS cluster.
            opts: Optional pulumi resource options.
        """
        self.resource_name_prefix = resource_name_prefix + "-rds"
        super().__init__(
            "ind:rds:RDS",
            resource_name_prefix,
            {},
            opts)

        self.security_group = aws.ec2.SecurityGroup(
            self.resource_name_prefix + "-sg",
            vpc_id=vpc_id,
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    from_port=rds_config.port,
                    to_port=rds_config.port,
                    protocol="tcp",
                    security_groups=access_security_groups),
            ],
            opts=pulumi.ResourceOptions(parent=self))

        self.subnet_group = aws.rds.SubnetGroup(
            self.resource_name_prefix + "-subnet-group",
            subnet_ids=subnet_ids,
            tags={
                "Name": self.resource_name_prefix + "-subnet-group",
            },
            opts=pulumi.ResourceOptions(parent=self))

        self.cluster = aws.rds.Cluster(
            self.resource_name_prefix + "-cluster",
            # Credentials
            cluster_identifier=rds_config.cluster_identifier,
            database_name=rds_config.database_name,
            master_username=rds_config.master_username,
            master_password=rds_config.master_password,
            # Engine
            engine=rds_config.engine,
            engine_mode=rds_config.engine_mode,
            engine_version=rds_config.engine_version,
            serverlessv2_scaling_configuration=aws.rds.ClusterServerlessv2ScalingConfigurationArgs(  # pylint: disable=line-too-long
                max_capacity=rds_config.max_capacity,
                min_capacity=rds_config.min_capacity,
            ),
            # Networking and Security
            db_subnet_group_name=self.subnet_group.id,
            vpc_security_group_ids=[self.security_group.id],
            skip_final_snapshot=True,
            opts=pulumi.ResourceOptions(parent=self))

        instance_identifier = self.resource_name_prefix + "-cluster-instance"
        self.cluster_instance = aws.rds.ClusterInstance(
            instance_identifier,
            cluster_identifier=self.cluster.id,
            identifier=instance_identifier,
            instance_class=rds_config.instance_class,
            engine=self.cluster.engine,
            engine_version=self.cluster.engine_version,
            opts=pulumi.ResourceOptions(parent=self))
