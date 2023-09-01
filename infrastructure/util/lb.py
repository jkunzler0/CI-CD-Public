# Copyright 2022 Inductor, Inc.

"""Load Balancer Component Resources"""

from typing import List

import pulumi
import pulumi_aws as aws


class LoadBalancer(pulumi.ComponentResource):
    """Load Balancer Component Resource"""

    def __init__(self,
        resource_name_prefix: str,
        vpc_id: str,
        subnet_ids: List[aws.ec2.Subnet],
        opts=None):
        """Create an Application Load Balancer and associated resources.

        Resources created:
        - Security Group
        - Application Load Balancer
        
        Args:
            resource_name_prefix: Prefix to use for all resources
                created by this component.
            vpc_id: VPC to create the load balancer in.
            subnets: Subnets to create the load balancer in.
            opts: Optional pulumi resource options.
        """
        self.resource_name_prefix = resource_name_prefix + "-lb"
        super().__init__(
            "ind:network:LoadBalancer",
            self.resource_name_prefix,
            {},
            opts)

        self.records = []
        self.target_groups = []
        self.target_group_attachments = []
        self.listeners = []

        self.security_group = aws.ec2.SecurityGroup(
            self.resource_name_prefix + "-sg",
            vpc_id=vpc_id,
            description="Inbound: Any HTTPS. Outbound: Any HTTP.",
            opts=pulumi.ResourceOptions(parent=self)
        )
        aws.ec2.SecurityGroupRule(
            self.resource_name_prefix + "-sg-ingress",
            type="ingress",
            from_port=443,
            to_port=443,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
            ipv6_cidr_blocks=["::/0"],
            security_group_id=self.security_group.id,
            opts=pulumi.ResourceOptions(parent=self)
        )
        aws.ec2.SecurityGroupRule(
            self.resource_name_prefix + "-sg-engress",
            type="egress",
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
            ipv6_cidr_blocks=["::/0"],
            security_group_id=self.security_group.id,
            opts=pulumi.ResourceOptions(parent=self)
        )

        alb_name = self.resource_name_prefix + "-alb"
        self.alb = aws.lb.LoadBalancer(
            alb_name,
            name=alb_name,
            internal=False,
            load_balancer_type="application",
            security_groups=[self.security_group.id],
            subnets=subnet_ids,
            idle_timeout=600,  # 10 minutes
            opts=pulumi.ResourceOptions(parent=self)
        )

    def add_dns_record(self, domain_name: str):
        """Creates a DNS record for the load balancer.
        
        Args:
            domain_name: Domain name to use for the DNS record.
        """
        hosted_zone = aws.route53.get_zone(name=domain_name)
        self.records.append(aws.route53.Record(
            self.resource_name_prefix + "-alb-record",
            zone_id=hosted_zone.id,
            name=domain_name,
            type="A",
            aliases=[aws.route53.RecordAliasArgs(
                name=self.alb.dns_name,
                zone_id=self.alb.zone_id,
                evaluate_target_health=True,
            )],
            opts=pulumi.ResourceOptions(parent=self)
        ))

    def add_target_group(
        self,
        health_check_path: str
    ) -> aws.lb.TargetGroup:
        """Creates a target group for the load balancer.
        
        Args:
            health_check_path: Path to use for the target group health check.
        """
        target_group = aws.lb.TargetGroup(
            self.resource_name_prefix + "-tg",
            port=80,
            protocol="HTTP",
            vpc_id=self.alb.vpc_id,
            health_check={
                "path": health_check_path,
            },
            target_type="ip",
            opts=pulumi.ResourceOptions(parent=self))
        self.target_groups.append(target_group)
        return target_group

    def add_listener(
        self,
        certificate_domain: str,
        target_group: aws.lb.TargetGroup
    ) -> aws.lb.Listener:
        """Creates a listener for the load balancer.

        Args:
            certificate_domain: Domain name to use for the certificate.
            target_group: Target group to forward requests to.
        """
        certificate = aws.acm.get_certificate(domain=certificate_domain)
        listener = aws.lb.Listener(
            self.resource_name_prefix + "-listener",
            load_balancer_arn=self.alb.arn,
            port=443,
            protocol="HTTPS",
            ssl_policy="ELBSecurityPolicy-2016-08",
            default_actions=[{
                "type": "forward",
                "target_group_arn": target_group.arn,
            }],
            certificate_arn=certificate.arn,
            opts=pulumi.ResourceOptions(parent=self)
        )
        self.listeners.append(listener)
        return listener
