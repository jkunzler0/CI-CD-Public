# Inductor: Infrastructure
>- [Inductor README](../README.md)

## Overview
This directory contains the code for the Inductor Infrastructure. The infrastructure is managed using Pulumi. (See the Pulumi [Getting Started](https://www.pulumi.com/docs/get-started/aws/) guide for more information.)

## File Structure
- `__main__.py` is the entry point for the Pulumi program. 
- `Pulumi.yaml` contains the project configuration while `Pulumi.{stack}.yaml` contains the stack configuration, where {stack} is the name of the Pulumi stack that is selected. (See the Pulumi [Stacks](https://www.pulumi.com/docs/intro/concepts/stack/) and [Configuration](https://www.pulumi.com/docs/intro/concepts/config/) guides for more information.)
- `config.py` formats the project/stack configuration for use by the program, contains information about the configurable parameters, and sets default values for certain parameters.
- `util/*` contains modules that are organized by resource type. These modules contain Pulumi ComponentResource classes that instantiate a collection of related resources. (See the Pulumi [Components](https://www.pulumi.com/docs/intro/concepts/resources/#components) guide for more information.)

## Stacks
- `dev`: The development stack. This stack is used for development and testing.

## Requirements
- [Install Pulumi](https://www.pulumi.com/docs/get-started/install/) (Included in the devcontainer.)
- Pulumi Account/Credentials.
- AWS Credentials.
