## EC2-Boto3

This project uses Boto3 in order to manage AWS EC2 Instances. The idea is to have a script that automates the entire process of creating each Instance,
then Loadbalancers and AutoScaling groups to manage incoming traffic. This project can be tested by running the `PF.py` file and setting your credentials
in the file, i.e., the `ACCESS_KEY` and `SECRET_ACCESS_KEY`.

An example of the logs printed by the application can be found at `log.txt`. It describes the entire process of the application. It should be noted that
this project can be run more than once, even if your instances are up in AWS. The application was built in a way that it checks whether there exists each
of the resources, such as a target group of an instance for example, and in case that is true, it will automatically delete such resource.

## First of all you need to install the aws CLI

<a href="https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html">Install AWS CLI</a>

## Then you need to configure with you AWS account

On your terminal run:

```bash
aws configure
```

**Then you need to put your aws user credentials, select the region and the output format you can leave it default**

## To manage your instances you need to install `boto3` with the following tutorial

<a href="https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#installation">Boto3 Installation</a>

## Using boto3

To check if you are authenticated and boto3 is working with your AWS account try to run thie python file:

**On the output you should see all the AWS users in the account**

```python
#this command is used to check if you are authenticated to aws

import boto3
iam = boto3.client("iam")

for user in iam.list_users()["Users"]:
    print("")
    print(user["UserName"])
    print(user["UserId"])
    print(user["Arn"])
    print(user["CreateDate"])
```

## How to Run

1. If you would like, change the names of this variables in the main.py file:
    
```python
    KeyName = 'matheus-key-pair' #(KeyPair in Ohio name)
    GroupIdName = 'matheus-security-group' #(Security Group name)
    KeyNameNV = 'matheus-key-pair-nv' #(KeyPair in North Virginia name)
    AMIName = 'AMI-mat-NV' #(AMI name)
    LbName = 'Loadbalancer-Mat-NV' #(Load Balancer name)
    TgName = 'TargetGrp-Mat-NV' #(Target Group name)
    LaunchConfigName = 'LC-Mat-NV' #(Launch Configuratio name)
    AutoScalingName = 'AutoSG-Mat-NV' #(Autoscalling Group name)
    PolicyName = 'alb1000-target-tracking-scaling-policy' #(Policy name)
```

2. Run the `main.py` file
3. When step 2 is done (this may take a while) open yours EC2 dashboard in AWS and head to the LoadBalancer tab
4. Copy the IP address of the LB
5. Run the `client.py`
6. Open in the navigator the LB ip address
7. Execute the commands in the client terminal
8. Refresh the navigator to see the db change in real time
