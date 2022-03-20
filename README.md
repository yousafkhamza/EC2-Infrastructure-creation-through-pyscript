# AWS Infrastructure Creation (Pyscript)
[![Build](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

---
## Description
Here it's a python script for creating AWS infrastructure through a python script and this is only for educational purposes also, we can do anything via python. 

----
## Feature
- Easy to configure for anyone 
- EC2 instance with root privilege
- Security Group for 80 & 22 (once we created other instances are using the same one)
- Variables and Configurations are passing through as a module

---
## Architecture
![alt_txt](https://i.ibb.co/Px9q8Xq/arch.jpg)

---
## Modules used
- [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [os](https://docs.python.org/3/library/os.html)
- [datetime](https://docs.python.org/3/library/datetime.html)


----
## Pre-Requests
- Basic Knowledge of python 
- Basic Knowledge of AWS IAM, EC2 service
- Need to change your IAM user creds and bucket name at config.py (region, access key, secret key)
- EC2 details are stored into var.py (password, size, type, sg name)

### IAM User Creation steps (_with screenshot_)
1. _log into your AWS account as a root user and go to IAM user_
2. _goto Access Managment >> Users_
![alt_txt](https://i.ibb.co/Y7kzZmN/IAM-1.png)
3. _Click Add User_ (_top right corner_)
![alt_txt](https://i.ibb.co/wW38xvR/IAM-2.png)
4. _Enter any username as you like and Choose "Programmatic access" >> Click Next Permissions_
![alt_txt](https://i.ibb.co/TrCbpBh/IAM-3.png)
5. _Set Permissions >> Select "Attach existing policies directly" >> Choose "AmazonEC2FullAccess" >> Click Next Tags_
![alt_txt](https://i.ibb.co/GkXxJrQ/Screenshot-3.png)
6. _Add Tags(Optional)_ >> _Enter a key and value as you like either you can leave as blank_
![alt_txt](https://i.ibb.co/QQb9svy/IAM-5.png)
7. _Review your user details and click "Create User"_
![alt_txt](https://i.ibb.co/SJy4VJB/Screenshot-4.png)
8. _Store your credentials to your local_
![alt_txt](https://i.ibb.co/nPVWcXZ/IAM-7.png)

_Reference URL_:: _IAM User creation [article](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html)_

----
### Pre-Requested (Dependency packages)
```sh
yum install -y git
yum install -y python3
yum install -y python3-pip
```

### How to get
```sh
git clone https://github.com/yousafkhamza/EC2-Infrastructure-creation-through-pyscript.git
cd EC2-Infrastructure-creation-through-pyscript
pip3 install -r requirements.txt
```
> Change your creds and bucket name in at config.py and ec2 details under var.py file

Command to run the script::
```
 python3 ec2_creation.py
```

----
## Output be like
```sh
$ python3 ec2_creation.py
Security Group Created sg-0f13a431524032168 in vpc vpc-00c2ae623614d9504. 

Instance Created Successfully and Details are given below:
----------------------------------------------------------
ID=i-02e1cbf5a1f54b6c2 PrivateIP=172.31.85.87
```

## Terminal Output
_Screenshot_
![alt_txt](https://i.ibb.co/267q5nx/terminal-out.png)

## Console output
_Screenshot_
![alt_txt](https://i.ibb.co/w7qYF6T/consol-out.png)

----
## Behind the code
_vim ec2_creation.py_
```sh
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

password = var.PASSWORD
USERDATA_SCRIPT = f'''
#!/bin/bash
echo "ClientAliveInterval 60" >> /etc/ssh/sshd_config
echo "LANG=en_US.utf-8" >> /etc/environment
echo "LC_ALL=en_US.utf-8" >> /etc/environment
echo "{password}" | passwd root --stdin
sed  -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
service sshd restart
'''


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
         UserData=USERDATA_SCRIPT,
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
    
instance_creation()
```
_vim config.py_
```sh
AWS_ACCESS_KEY_ID = 'YOUR ACCESS KEY HERE'
AWS_SECRET_ACCESS_KEY = 'YOUR PRIVATE KEY HERE'
REGION = 'REGION HERE'
```
_vim var.py_
```sh
PASSWORD = 'P@55W06D@12y' # You can modify your instance password here
SG_NAME = 'FOREC2'        # You can modify your Security Group Name here
IN_TYPE = 't2.micro'      # You can modify your instance type here
IN_SIZE = '10'            # You can modify your instance size here
```
----
## Conclusion
It's a simple python script to create AWS infrastructure like ansible/terraform but we don't use this we can able to create the same through python and it's an educational purpose. I hope you all understood the same and let me know your thoughts and comments.

### ⚙️ Connect with Me 

<p align="center">
<a href="mailto:yousaf.k.hamza@gmail.com"><img src="https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white"/></a>
<a href="https://www.linkedin.com/in/yousafkhamza"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"/></a> 
<a href="https://www.instagram.com/yousafkhamza"><img src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white"/></a>
<a href="https://wa.me/%2B917736720639?text=This%20message%20from%20GitHub."><img src="https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white"/></a><br />
