# ECS Tools

These tools were developed by Chegg to work with AWS EC2 Container Services. Tools help to automate new ECS service creation, new release rollout, and also help to debug existing code.
    
    
    
## Installation
Run 
```bash
$ ./setup.sh
```
    
All tools use **awscli** profiles to authenticate in AWS services. Use parameter **--profile** if you have configured multiple AWS credential profiles on your machine, otherwise _default_ profile will be used.
COnfigure **awscli** using following command:
```bash
$ aws configure
```
    
    
## Usage    
    
    
### create-ecs-service
Create new ECS service. This includes registration of new Task Definition and creation of Elastic Load Balancer.
    
If an input file with image names is provided, the tool will create services for each line in the file. In this case **--port** value will be used as a port number for the first service, and will be incremented by 1 for each next service.
Use either **--image** or **--file** option.
     
**create-ecs-service** has many parameters to help configuring all nodes of the service properly:
 
 
```
  --cluster CLUSTER     ECS Cluster name
  --image IMAGE         Container image name
  --port PORT           Host machine's port
  --memory MEMORY       Allocated memory
  --cpu CPU             Allocated CPU units
  --container-port CONTAINER_PORT
                        Container port
  --elb-port ELB_PORT   LoadBalancer port
  --profile PROFILE     AWS user profile
  --desired-count DESIRED_COUNT
                        Desired count of running containers
  --minimum-healthy-percent MINIMUM_HEALTHY_PERCENT
                        ECS Service minimum healthy percent
  --maximum-percent MAXIMUM_PERCENT
                        ECS Service maximum percent
  --iam-role IAM_ROLE   IAM Role
  --elb-health-check-uri ELB_HEALTH_CHECK_URI
                        ELB health check URI
  --elb-health-check-interval ELB_HEALTH_CHECK_INTERVAL
                        ELB health check interval
  --elb-health-check-timeout ELB_HEALTH_CHECK_TIMEOUT
                        ELB health check timeout
  --elb-health-check-unhealthy-threshold ELB_HEALTH_CHECK_UNHEALTHY_THRESHOLD
                        ELB health check unhealthy treshold
  --elb-health-check-healthy-threshold ELB_HEALTH_CHECK_HEALTHY_THRESHOLD
                        ELB health check healthy threshold
  --retry-count RETRY_COUNT
                        Retry count for each AWS API call
  --retry-interval RETRY_INTERVAL
                        Retry interval for AWS API calls (seconds)
  -f FILE, --file FILE  Input file with service name lines
  --cluster-prefix      Use cluster name as a prefix for service names
  --cmd CMD             Container run command line
  --user USER           Username added as a created-by tag in ELB
  --subnets SUBNETS     Comma separated subnets list
  --security-groups SECURITY_GROUPS
                        Comma separated security groups list
  --log-options LOG_OPTIONS
                        Logger options in JSON format
```
    
Example:
    
```bash
$ ./create-ecs-service --cluster test --profile default \
--image mytestproject:latest  --container-port 8080--port 8888 --elb-port 80 \
--desired-count 3 --memory 1024 --cpu 256 --minimum-healthy-percent 50 \
--maximum-percent 200 --iam-role MyEcsRole --elb-health-check-uri "/status" \
--elb-health-check-interval 60 --elb-health-check-timeout 15 --elb-health-check-unhealthy-threshold 5 \
--elb-health-check-healthy-threshold 3 --retry-count 25 --retry-interval 3 \
--subnets subnet1,subnet2,subnet3 --security-groups default --log-options "{\"logDriver\":\"json-file\"}"
```
    
### update-ecs-service
Deploy new Docker image, update service configuration or simply bounce the service.
This tool creates a new Task Definition revision, and update the ECS service to use this new revision.
If configured, **update-ecs-service** will wait for the deployment to complete. While waiting, this tool will poll ECS service events, so you see how the deployment goes and what's exactly happening with the service.
    
```
  --cluster CLUSTER     ECS Cluster name
  --service SERVICE     ECS Service name
  --profile PROFILE     AWS User profile
  --wait                Wait for ECS Service deployment to complete
  --wait-timeout WAIT_TIMEOUT
                        Wait timeout
  --retry-count RETRY_COUNT
                        AWS API calls retry count
  --memory MEMORY       New memory allocation for container
  --cpu CPU             New CPU units allocation for container
  --env_vars ENV_VARS   Environment Variables
  --env_vars-update-mode {key,all}
                        Environment Variables
  --cmd CMD             Command
  --log-options LOG_OPTIONS
                        Logger options in JSON format
  --hide-events         Do not display ECS events
  --task-definition TASK_DEFINITION
                        Existing Task Definition name or ARN
  --container CONTAINER
                        Specific name of the container definition inside Task
                        Definition
  
  image                 Name of the Docker image                          
```
    
Example:
    
```bash
$ ./update-ecs-service --cluster test --service mytestproject \
--container primary_service --wait --wait-timeout 600 mytestproject:v2
```

Same tool can be used to bounce a service. In this case provide only cluster and service name:
```bash
$ ./update-ecs-service --cluster test --service mytestproject --wait --wait-timeout 600
```

    
### delete-ecs-service
Remove an ECS service. This includes deletion of Elastic Load Balancer.
    
```
  --cluster CLUSTER     ECS Cluster name
  --service SERVICE     ECS Service name
  --retry-count RETRY_COUNT
                        Retry count for each AWS API call
  --retry-interval RETRY_INTERVAL
                        Retry interval for AWS API calls (seconds)
  --profile PROFILE     AWS user profile
  -f FILE, --file FILE  Input file with service name lines
  --cluster-prefix      Search for service names prefixed with cluster name
  --user USER           If set, must match created-by tag value in ELB 
```
    
Example:
    
```bash
$ ./delete-ecs-service --cluster test --service mytestproject
```


### clone-service
Clone an ECS service, including ELB cloning. New ECS service will point to same Task Definition.
    
```
  --profile PROFILE     AWS Profile
  --cluster CLUSTER     ECS cluster name
  --dest-cluster DEST_CLUSTER
                        Destination ECS cluster name
  --service SERVICE     ECS service name
  --dest-name DEST_NAME
                        Destination ECS service name
```
    
Example:
    
```bash
$ ./clone-service --cluster test --service mytestproject \
--dest-cluster dev --dest-name migratedtestproject 
```
    
### revert-service-revision
Rollback new deployment. This tool will search for previous Task Definition revision, and will update the ECS service to use this revision via **update-ecs-service**.
    
```
  --cluster CLUSTER     ECS cluster name
  --service SERVICE     ECS service name
  --revision REVISION   Task Definition revision number. If not provided,
                        service will be reverted to previous revision
  --profile PROFILE     AWS profile name
  --find-active         Find active revision
  --wait                Wait for ECS Service deployment to complete
  --wait-timeout WAIT_TIMEOUT
                        Wait timeout
```
    
Example:
    
```bash
$ ./revert-service --cluster test --service mytestproject \
--find-active --wait --wait-timeout 600
```    
    
### run-local-task
This tool is very useful for debugging. It scans the Task Definition, and converts it into a local **docker run** command.
    
```
  --profile PROFILE     AWS User profile
  --container CONTAINER
                        Specific name of the container definition inside Task
                        Definition

  task_definition       Task Definition name or ARN
```
    
    
Example:
    
```bash
$ ./run-local-task --container primary_service test-mytestproject:4
```


