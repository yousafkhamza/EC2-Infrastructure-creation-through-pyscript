import boto3
import datetime
import os
from botocore.exceptions import ClientError
import config
import var

ec2_client = boto3.client('ec2',
                      aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                      region_name=config.REGION
                    )

ec2 = boto3.resource('ec2',
                      aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                      region_name=config.REGION
                    )

def key_pair():
    key_pair = ec2_client.describe_key_pairs()['KeyPairs']
    for item in key_pair:
        if item['KeyName'] == var.KEY_NAME:
            print ('The Key Pair "%s" is already created in amazon, So, we are using the same into this instance' % (var.KEY_NAME))
        else:
            key_pair = ec2_client.create_key_pair(KeyName=var.KEYNAME)
            private_key = key_pair["KeyMaterial"]
            # write private key to file with 400 permissions
            with os.fdopen(os.open("./%s.pem" % (var.KEY_NAME), os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:
                handle.write(private_key)
        
def instance_creation():
    # AMI Finding
    year = datetime.datetime.now().year

    ami_img = []
    ami = ec2_client.describe_images(Owners=['137112412989'])['Images']
    for item in ami:
        if item['ImageOwnerAlias'] == "amazon" and item["Name"].startswith('amzn2-ami-hvm') and item['CreationDate'].startswith(str(year)):
            ami_img.append(item['ImageId'])
            
    # Security Group Creation
    group_id = []
    sg_group = ec2_client.describe_security_groups()['SecurityGroups']
    for item in sg_group:
        if item['GroupName'] == var.SG_NAME:
            print ('The Security Group "%s" is already created in amazon, So, we are using the same into this instance' % (var.SG_NAME))
            group_id.append(item['GroupId'])
        else:
            response = ec2_client.describe_vpcs()
            vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
            try:
                response = ec2_client.create_security_group(GroupName=var.SG_NAME,
                                                     Description='DESCRIPTION',
                                                     VpcId=vpc_id)
                security_group_id = response['GroupId']
                print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
                group_id.append(security_group_id)
                data = ec2_client.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {'IpProtocol': 'tcp',
                         'FromPort': 80,
                         'ToPort': 80,
                         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                        {'IpProtocol': 'tcp',
                         'FromPort': 22,
                         'ToPort': 22,
                         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
                    ])
            except ClientError as e:
                continue
        
    # Instance Creation
    instances = ec2.create_instances(
             BlockDeviceMappings=[
                  {
                    'DeviceName': '/dev/xvda',
                    'Ebs': {
                        'DeleteOnTermination': True,
                        'VolumeSize': int(var.IN_SIZE),
                        'VolumeType': 'gp2'
                    },
                },
            ],
         ImageId=ami_img[0],
         MinCount=1,
         MaxCount=1,
         InstanceType=var.IN_TYPE,
         SecurityGroupIds=[ group_id[0] ],
         KeyName=var.KEY_NAME,
         TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'EC2-From-Python'
                            },
                        ]
                    },
                ]
        )
    print('\nInstance Created Successfully and Details are given below:')
    print('----------------------------------------------------------')
    print("ID="+instances[0].id, "PrivateIP="+instances[0].private_ip_address)
    
key_pair()
instance_creation()