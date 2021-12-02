import boto3
import os
from dotenv import load_dotenv
import time

load_dotenv()


#-------------------------------------------------------------------------------------------------------
# Credenciais 
access_key = os.getenv('ACCESS_KEY')
secret_access_key = os.getenv('SECRET_ACESS_KEY')

#-------------------------------------------------------------------------------------------------------
# Criando client EC2 em cada região
print('Criando client EC2 em cada região\n')

ec2_client_north_virginia = boto3.client(
    "ec2",
    region_name="us-east-1",
    aws_access_key_id = access_key,
    aws_secret_access_key = secret_access_key
)

ec2_client_ohio = boto3.client(
    "ec2",
    region_name="us-east-2",
    aws_access_key_id = access_key,
    aws_secret_access_key = secret_access_key
)

#-------------------------------------------------------------------------------------------------------
# Criação dos keypairs
print('Criando os keypairs em cada região\n')

# --------Ohio------------
kpName_ohio = 'matheus-key-pair'
keyFileName_ohio = 'matheus-key-pair.pem'

kp_response_ohio = ec2_client_ohio.describe_key_pairs(
    Filters=[
        {'Name': 'key-name', 'Values': [kpName_ohio]}
    ]
)

if kp_response_ohio['KeyPairs']:
    ec2_client_ohio.delete_key_pair(KeyName=kpName_ohio)

key_pair_ohio = ec2_client_ohio.create_key_pair(KeyName=kpName_ohio)
private_key_ohio = key_pair_ohio["KeyMaterial"]

try:
    if os.path.exists(keyFileName_ohio):
        os.remove(keyFileName_ohio)
except:
    print("Error while deleting file ", os.getcwd())

# write private key to file with 777 permissions
with os.fdopen(os.open(keyFileName_ohio, os.O_WRONLY | os.O_CREAT, 0o777), "w+") as handle:
    handle.write(private_key_ohio)

# ----North Virginia-----
kpName_nv = 'matheus-key-pair-nv'
keyFileName_nv = 'matheus-key-pair-nv.pem'

kp_response_nv = ec2_client_north_virginia.describe_key_pairs(
    Filters=[
        {'Name': 'key-name', 'Values': [kpName_nv]}
    ]
)

if kp_response_nv['KeyPairs']:
    ec2_client_north_virginia.delete_key_pair(KeyName=kpName_nv)

ec2_client_north_virginia.delete_key_pair(KeyName=kpName_nv)

key_pair_nv = ec2_client_north_virginia.create_key_pair(KeyName=kpName_nv)
private_key_nv = key_pair_nv["KeyMaterial"]

try:
    if os.path.exists(keyFileName_nv):
        os.remove(keyFileName_nv)
except:
    print("Error while deleting file ", os.getcwd())

# write private key to file with 777 permissions
with os.fdopen(os.open(keyFileName_nv, os.O_WRONLY | os.O_CREAT, 0o777), "w+") as handle:
    handle.write(private_key_nv)

#-------------------------------------------------------------------------------------------------------
# Deletando AutoScaling Group se já existe
print('Deletando AutoScaling Group se já existe\n')

autosgName = 'AutoSG-Mat-NV'

ec2_client_north_virginia_AS = boto3.client(service_name="autoscaling",
                                            region_name="us-east-1",
                                            aws_access_key_id = access_key,
                                            aws_secret_access_key = secret_access_key
                                           )

try:
    desc_inst = ec2_client_north_virginia_AS.describe_auto_scaling_instances()


    ec2_client_north_virginia_AS.update_auto_scaling_group(
        AutoScalingGroupName=autosgName,
        MinSize=0,
        DesiredCapacity=0,
    )

    waiter_AS_Instance = ec2_client_north_virginia.get_waiter('instance_terminated')

    for inst in desc_inst['AutoScalingInstances']:
        id_inst = inst['InstanceId']

        ec2_client_north_virginia.terminate_instances(InstanceIds=[id_inst])

        print('Terminando instâncias criadas pelo Autoscaling\n')

        waiter_AS_Instance.wait(
            Filters=[
                {
                    'Name': 'instance-id',
                    'Values': [
                        id_inst,
                    ]
                },
            ]
        )


        ec2_client_north_virginia_AS.delete_auto_scaling_group(
            AutoScalingGroupName=autosgName,
            ForceDelete=True
        )

except:
    print('Autoscaling não existe\n')
    
#-------------------------------------------------------------------------------------------------------
# Deletando instâncias caso já existam antes de criar security group
print('Deletando as instâncias antes de criar security group\n')

# --------Ohio------------
print('Deletando instância de Ohio se existir\n')
waiter_ohio = ec2_client_ohio.get_waiter('instance_terminated')

responseInst_ohio = ec2_client_ohio.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Mat-PSQL-Ohio',
            ]
        },
        {
            'Name': 'instance-state-name',
            'Values': [
                'running',
            ]
            
        },
    ],
)

if responseInst_ohio['Reservations']:
    instanceId_ohio = responseInst_ohio['Reservations'][0]['Instances'][0]['InstanceId']
    ec2_client_ohio.terminate_instances(InstanceIds=[instanceId_ohio])

    waiter_ohio.wait(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    'Mat-PSQL-Ohio',
                ]
            },
        ]
    )

# ----North Virginia-----
print('Deletando instância de NV se existir\n')
waiter_nv = ec2_client_north_virginia.get_waiter('instance_terminated')

responseInst_nv = ec2_client_north_virginia.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Mat-DJANGO-NV',
            ]
        },
        {
            'Name': 'instance-state-name',
            'Values': [
                'running',
            ]
            
        },
    ],
)


if responseInst_nv['Reservations']:
    instanceId_nv = responseInst_nv['Reservations'][0]['Instances'][0]['InstanceId']
    ec2_client_north_virginia.terminate_instances(InstanceIds=[instanceId_nv])

    waiter_nv.wait(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    'Mat-DJANGO-NV',
                ]
            },
        ]
    )

#-------------------------------------------------------------------------------------------------------
# Deletando listener se já existe
print('Deletando listener se já existe\n')

ec2_client_north_virginia_LB = boto3.client(service_name="elbv2",
                                            region_name="us-east-1",
                                            aws_access_key_id = access_key,
                                            aws_secret_access_key = secret_access_key
                                           )

loadbalancer_name = 'Loadbalancer-Mat-NV'

try:
    LB_response = ec2_client_north_virginia_LB.describe_load_balancers(
        Names=[
            loadbalancer_name,
        ],
    )


    if LB_response['LoadBalancers']:
        LB_Arn = LB_response['LoadBalancers'][0]['LoadBalancerArn']                      

        listeners_response = ec2_client_north_virginia_LB.describe_listeners(
            LoadBalancerArn=LB_Arn,
        )


        if listeners_response['Listeners']:
            listener_arn = listeners_response['Listeners'][0]['ListenerArn']
            
            response = ec2_client_north_virginia_LB.delete_listener(
                ListenerArn=listener_arn
            )
except:
    print('Load Balancer não existe\n')

#-------------------------------------------------------------------------------------------------------
# Deletando loadbalancer se já existir
print('Deletando Loadbalancer se já existir\n')

try:
    LB_response = ec2_client_north_virginia_LB.describe_load_balancers(
        Names=[
            loadbalancer_name,
        ],
    )

    LB_Arn = LB_response['LoadBalancers'][0]['LoadBalancerArn']

    ec2_client_north_virginia_LB.delete_load_balancer(
        LoadBalancerArn=LB_Arn
    )

except:
    print('Loadbalancer não existe\n')

#-------------------------------------------------------------------------------------------------------
# Deletando Target Group se já existe
print('Deletando Target Group se já existe\n')

target_grp_name = 'TargetGrp-Mat-NV'

try:
    TG_response = ec2_client_north_virginia_LB.describe_target_groups(
        Names=[
            target_grp_name,
        ],
    )
    TG_Arn = TG_response['TargetGroups'][0]['TargetGroupArn']
    response = ec2_client_north_virginia_LB.delete_target_group(
        TargetGroupArn=TG_Arn
    )
    
except:
    print('Target Group não existe ainda\n')

#-------------------------------------------------------------------------------------------------------
# Deletando Launch Configuration se não existe (depende do AUTOSCALING)
print('Deletando Launch Configuration se não existe\n')

lcName = 'LC-Mat-NV' 

response = ec2_client_north_virginia_AS.describe_launch_configurations(
    LaunchConfigurationNames=[
        lcName,
    ],
)

if response['LaunchConfigurations']:
    ec2_client_north_virginia_AS.delete_launch_configuration(
        LaunchConfigurationName=lcName,
    )

time.sleep(40)

#-------------------------------------------------------------------------------------------------------
# Criação dos security groups
print('Criando os security groups em cada região\n')

# --------Ohio------------
scName_ohio = 'matheus-security-group'

vpcs = ec2_client_ohio.describe_vpcs()
for vpc in vpcs['Vpcs']:
    vpc_ohio = vpc['VpcId']


sc_response_ohio = ec2_client_ohio.describe_security_groups(
    Filters=[
        {'Name': 'group-name', 'Values': [scName_ohio]}
    ]
)

if sc_response_ohio['SecurityGroups']:
    scId_ohio = sc_response_ohio['SecurityGroups'][0]['GroupId']

    ec2_client_ohio.delete_security_group(
        GroupId=scId_ohio,
    )

security_group_ohio = ec2_client_ohio.create_security_group(
    GroupName= scName_ohio,
    Description= 'Projeto Cloud',
    VpcId= vpc_ohio,
)

scId_ohio = security_group_ohio['GroupId']


# ------North Virginia-------
scName_nv = 'matheus-nv-security-group'

vpcs = ec2_client_north_virginia.describe_vpcs()
for vpc in vpcs['Vpcs']:
    vpc_nv = vpc['VpcId']


sc_response_nv = ec2_client_north_virginia.describe_security_groups(
    Filters=[
        {'Name': 'group-name', 'Values': [scName_nv]}
    ]
)

if sc_response_nv['SecurityGroups']:
    scId_nv = sc_response_nv['SecurityGroups'][0]['GroupId']

    ec2_client_north_virginia.delete_security_group(
        GroupId=scId_nv,
    )

security_group_nv = ec2_client_north_virginia.create_security_group(
    GroupName= scName_nv,
    Description= 'Projeto Cloud',
    VpcId= vpc_nv,
)

scId_nv = security_group_nv['GroupId']

#-------------------------------------------------------------------------------------------------------
# Configurando regras de entrada para cada security group
print('Configurando regras de entrada para cada security group\n')

ec2_client_ohio.authorize_security_group_ingress(
    GroupId=scId_ohio,
    IpPermissions=[
        {'IpProtocol': 'tcp',
         'FromPort': 80,
         'ToPort': 80,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp',
         'FromPort': 22,
         'ToPort': 22,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp',
         'FromPort': 5432,
         'ToPort': 5432,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
    ])

ec2_client_north_virginia.authorize_security_group_ingress(
    GroupId=scId_nv,
    IpPermissions=[
        {'IpProtocol': 'tcp',
         'FromPort': 80,
         'ToPort': 80,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp',
         'FromPort': 22,
         'ToPort': 22,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp',
         'FromPort': 8080,
         'ToPort': 8080,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
    ])

#-------------------------------------------------------------------------------------------------------
# Criando instância Postgres de Ohio
print('Criando instância Postgres de Ohio\n')

USERDATA_OHIO = '''#!/bin/bash
cd /
sudo apt update 
sudo apt install postgresql postgresql-contrib -y
sudo -u postgres psql -c "create user cloud;"
sudo -u postgres createdb tasks -O cloud
sudo sed -i s/"^#listen_addresses = 'localhost'"/"listen_addresses = '*'"/g  /etc/postgresql/12/main/postgresql.conf
sudo sed -i -e '$a\host all all 0.0.0.0/0 trust' /etc/postgresql/12/main/pg_hba.conf
sudo ufw allow 5432/tcp
sudo systemctl restart postgresql
touch foo.txt
'''

responseInst_ohio = ec2_client_ohio.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Mat-PSQL-Ohio',
            ]
        },
    ],
)

if responseInst_ohio['Reservations']:
    instanceId_ohio = responseInst_ohio['Reservations'][0]['Instances'][0]['InstanceId']
    ec2_client_ohio.terminate_instances(InstanceIds=[instanceId_ohio])

instances = ec2_client_ohio.run_instances(
        ImageId="ami-0629230e074c580f2",
        MinCount=1,
        MaxCount=1,
        InstanceType="t2.micro",
        KeyName=kpName_ohio,
        UserData = USERDATA_OHIO,
        SecurityGroups = [scName_ohio]
    )



instanceId_ohio = instances['Instances'][0]['InstanceId']

print("ID da instância Ohio: ", instanceId_ohio, "\n")

ec2_client_ohio.create_tags(Resources=[instanceId_ohio], Tags=[{'Key':'Name', 'Value':'Mat-PSQL-Ohio'}])

responseInst_ohio = ec2_client_ohio.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Mat-PSQL-Ohio',
            ]
        },
    ],
)

#-------------------------------------------------------------------------------------------------------
# Pegando IP Público da instância Postgres de Ohio
print('Pegando IP Público da instância Postgres de Ohio\n')

waiter_IP = ec2_client_ohio.get_waiter('instance_running')


waiter_IP.wait(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Mat-PSQL-Ohio',
            ]
        },
        {
            'Name': 'instance-state-name',
            'Values': [
                'running',
            ]
            
        },
    ]
)

responseInst_ohio = ec2_client_ohio.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Mat-PSQL-Ohio',
            ]
        },
        {
            'Name': 'instance-state-name',
            'Values': [
                'running',
            ]
            
        },
    ]
)

instance_ohio_IPaddress = responseInst_ohio['Reservations'][0]['Instances'][0]['PublicIpAddress']        

#-------------------------------------------------------------------------------------------------------
# Criando instância Django de North Virginia
print('Criando instância Django de North Virginia\n')

USERDATA_NORTH_VIRGINIA = f'''#!/bin/bash
cd /
sudo apt update
git clone https://github.com/MatFreitas/tasks.git
cd tasks/portfolio
sudo sed -i s/"'HOST': 'node1',"/"'HOST': '{instance_ohio_IPaddress}',"/g  settings.py
sudo sed -i s/"'PASSWORD': 'cloud',"/"'PASSWORD': '',"/g  settings.py
cd ../
./install.sh
sudo ufw allow 8080/tcp 
./run.sh
'''

responseInst_nv = ec2_client_north_virginia.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Mat-DJANGO-NV',
            ]
        },
    ],
)

if responseInst_nv['Reservations']:
    instanceId_nv = responseInst_nv['Reservations'][0]['Instances'][0]['InstanceId']
    ec2_client_north_virginia.terminate_instances(InstanceIds=[instanceId_nv])

instances = ec2_client_north_virginia.run_instances(
        ImageId="ami-0279c3b3186e54acd",
        MinCount=1,
        MaxCount=1,
        InstanceType="t2.micro",
        KeyName=kpName_nv,
        UserData = USERDATA_NORTH_VIRGINIA,
        SecurityGroups = [scName_nv]
    )

instanceId_nv = instances['Instances'][0]['InstanceId']

print("ID da instância NV: ", instanceId_nv, "\n")

ec2_client_north_virginia.create_tags(Resources=[instanceId_nv], Tags=[{'Key':'Name', 'Value':'Mat-DJANGO-NV'}])

responseInst_nv = ec2_client_north_virginia.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Mat-DJANGO-NV',
            ]
        },
    ],
)

#-------------------------------------------------------------------------------------------------------
# Esperando a instância Django de NV rodar
print('Esperando a instância Django de NV rodar\n')

waiter_NV = ec2_client_north_virginia.get_waiter('instance_running')


waiter_NV.wait(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'Mat-DJANGO-NV',
            ]
        },
        {
            'Name': 'instance-state-name',
            'Values': [
                'running',
            ]     
        },
    ]
)

#-------------------------------------------------------------------------------------------------------
# Deleta imagem se já existe
# print('Deleta imagem se já existe\n')

AMI_Name = 'AMI-mat-NV'

im_response = ec2_client_north_virginia.describe_images(
    Owners=['self'],
    Filters=[
        {
            'Name': 'name',
            'Values': [
                AMI_Name,
            ]
        },
    ]
)

if im_response['Images']:
    imageId = im_response['Images'][0]['ImageId']
    ec2_client_north_virginia.deregister_image(ImageId=imageId)

#-------------------------------------------------------------------------------------------------------
# Criando imagem da instância Django de NV
print('Criando imagem da instância Django de NV\n')

image_NV = ec2_client_north_virginia.create_image(InstanceId=instanceId_nv, Name=AMI_Name)
image_NV_Id = image_NV["ImageId"]

waiter_AMI = ec2_client_north_virginia.get_waiter('image_available')


waiter_AMI.wait(
    ImageIds=[
        image_NV_Id,
    ], 
)


#-------------------------------------------------------------------------------------------------------
# Deletando instância Django de NV
print('Deletando instância Django de NV\n')

ec2_client_north_virginia.terminate_instances(InstanceIds=[instanceId_nv])

#-------------------------------------------------------------------------------------------------------
# Criando o Loadbalancer
print('Criando o loadbalancer\n')


subnets = []
sn_all = ec2_client_north_virginia.describe_subnets()
for sn in sn_all['Subnets']:
    subnets.append(sn['SubnetId'])

LB_create_response = ec2_client_north_virginia_LB.create_load_balancer(Name=loadbalancer_name,
                                                         Subnets=subnets,
                                                         SecurityGroups=[scId_nv],
                                                         Scheme='internet-facing'
                                                 )

LB_Arn = LB_create_response['LoadBalancers'][0]['LoadBalancerArn']

#-------------------------------------------------------------------------------------------------------
# Criando o Target Group
print('Criando o target group\n')

TG_create_response = ec2_client_north_virginia_LB.create_target_group(Name=target_grp_name,
                                                        Protocol='HTTP',
                                                        Port=8080,
                                                        VpcId=vpc_nv)

TG_Arn = TG_create_response['TargetGroups'][0]['TargetGroupArn']

#-------------------------------------------------------------------------------------------------------
# Criando listener (depende do LOADBALANCER)
print('Criando listener no loadbalancer\n')

listener_response = ec2_client_north_virginia_LB.create_listener(LoadBalancerArn=LB_Arn,
                                                          Protocol='HTTP', Port=80,
                                                          DefaultActions=[{'Type': 'forward',
                                                                           'TargetGroupArn': TG_Arn}])


#-------------------------------------------------------------------------------------------------------
# Formatando string do Resource
print('Formatando string do Resource\n')

arn_loadbalancer = 'a' + LB_Arn.split('/a')[1]

print(f"arn_loadbalancer: {arn_loadbalancer}", '\n')

tgId = TG_create_response['TargetGroups'][0]['TargetGroupArn']
arn_targetgroup = 't' + tgId.split(':t')[1]
print(f"arn_targetgroup: {arn_targetgroup}", '\n')

ResourceLabelString = arn_loadbalancer + '/' + arn_targetgroup
print(f"Resource Label String: {ResourceLabelString}", '\n')


#-------------------------------------------------------------------------------------------------------
# Criando Launch Configuration
print('Criando Launch Configuration\n')


LC_response = ec2_client_north_virginia_AS.create_launch_configuration(
    LaunchConfigurationName = lcName,
    ImageId = image_NV_Id,
    KeyName = kpName_nv,
    SecurityGroups = [scId_nv],
    UserData=USERDATA_NORTH_VIRGINIA,
    InstanceType = 't2.micro'
)

#-------------------------------------------------------------------------------------------------------
# Criando Autoscaling Group
print('Criando Autoscaling Group\n')

autosgName = 'AutoSG-Mat-NV'

AS_response = ec2_client_north_virginia_AS.create_auto_scaling_group(
    AutoScalingGroupName=autosgName,
    LaunchConfigurationName=lcName,
    MinSize=1,
    MaxSize=3,
    VPCZoneIdentifier='subnet-0fcc35c353bf9b254',
    TargetGroupARNs=[tgId],
    Tags = [
            {
                "Key": "Name",
                "Value": "ASG-Mat-instance",
                "PropagateAtLaunch": True
            }
    ]
)

print('Criando Scaling Policy\n')
SP_response = ec2_client_north_virginia_AS.put_scaling_policy(
    AutoScalingGroupName=autosgName,
    PolicyName='alb1000-target-tracking-scaling-policy',
    PolicyType='TargetTrackingScaling',
    TargetTrackingConfiguration={
        'PredefinedMetricSpecification': {
            'PredefinedMetricType': 'ALBRequestCountPerTarget',
            'ResourceLabel': ResourceLabelString,
        },
        'TargetValue': 50.0,
    },
)
