import json
import time
from sys import stdout

import boto3


class DictPathAccess:
    def __init__(self, descriptor):
        self.descriptor = descriptor

    def get(self, path):
        element = self.descriptor
        levels = path.split('/')
        for level in levels:
            if level in element:
                element = element[level]
            else:
                return None
        return element

    def set(self, path, value, create=False):
        element = self.descriptor
        levels = path.split('/')
        if len(levels) > 0:
            for i in range(0, len(levels) - 1):
                if levels[i] not in element:
                    if create:
                        element[levels[i]] = dict()
                    else:
                        raise ValueError("Element {0} does not exist!".format(levels[i]))
                element = element[levels[i]]
            lastLevel = levels[len(levels) - 1]
            element[lastLevel] = value

    def exists(self, path):
        return self.get(path) != None


# Used to display log lines immediately by flushing STDOUT
def log(text):
    stdout.write("{}\n".format(text))
    stdout.flush()


def updateECSTask(cluster, serviceId, imageName=None, profileName=None, memory=None, cpu=None, env_vars=None,
                  wait=False,
                  waitTimeout=120,
                  waitRetryCount=10, log_options=None, cmd=None, name=None, hideEvents=False, envUpdateMode='all',
                  container_name=None):
    session = boto3.Session(profile_name=profileName)
    client = session.client('ecs')
    services = client.describe_services(cluster=cluster, services=[serviceId])
    if "services" in services and len(services["services"]) > 0:
        service = services["services"][0]
        if service["status"] != "ACTIVE":
            raise ValueError(
                "Service {0} in cluster {1} has status {2} and cannot be updated".format(serviceId, cluster,
                                                                                         service["status"]))
        if not name:
            idTaskDefinition = service["taskDefinition"]
            describeTaskDefinition = client.describe_task_definition(taskDefinition=idTaskDefinition)
            taskDefinition = describeTaskDefinition["taskDefinition"]
            taskFamily = taskDefinition["family"]
            if "taskRoleArn" in taskDefinition:
                taskRoleArn = taskDefinition["taskRoleArn"]
            else:
                taskRoleArn = None

            container_found = False
            for container in taskDefinition["containerDefinitions"]:
                if (not container_name) or container_name == container["name"]:
                    container_found = True
                    if imageName:
                        container["image"] = imageName
                    if memory != None:
                        container["memory"] = memory
                    if cpu != None:
                        container["cpu"] = cpu
                    if env_vars != None:
                        if envUpdateMode == 'all' or ("environment" not in container) or (not container["environment"]):
                            container["environment"] = env_vars
                        else:
                            for env in container["environment"]:
                                if env["name"] in env_vars:
                                    env["value"] = env_vars[env["name"]]
                    if log_options:
                        container["logConfiguration"] = json.loads(log_options)
                    if cmd:
                        container["command"] = [cmd]
            if not container_found:
                if container_name:
                    raise Exception(
                        "Container {0} not found in Task Definition {1}!".format(container_name, idTaskDefinition))
                else:
                    raise Exception(
                        "No containers found in Task Definition {0}!".format(idTaskDefinition))
            if taskRoleArn:
                newTaskRevision = client.register_task_definition(family=taskFamily, taskRoleArn=taskRoleArn,
                                                                  containerDefinitions=taskDefinition[
                                                                      "containerDefinitions"],
                                                                  volumes=taskDefinition["volumes"])
            else:
                newTaskRevision = client.register_task_definition(family=taskFamily,
                                                                  containerDefinitions=taskDefinition[
                                                                      "containerDefinitions"],
                                                                  volumes=taskDefinition["volumes"])
            newTaskRevisionName = DictPathAccess(newTaskRevision).get("taskDefinition/taskDefinitionArn")
        else:
            newTaskRevisionName = name
        log("Task definition name: {}".format(newTaskRevisionName))
        counter = 0
        while True:
            try:
                updatedService = client.update_service(cluster=cluster, service=serviceId,
                                                       taskDefinition=newTaskRevisionName)
                break
            except Exception as e:
                counter += 1
                log("Service update failed: {}".format(e.message))
                if counter >= waitRetryCount:
                    raise e
                else:
                    counter += 1
                    time.sleep(1)
                    log("Retrying...")
        log("Amazon ECS: updated service {0} in cluster {1}".format(serviceId, cluster))
        if wait:
            log("Waiting for ECS to complete the deployment")
            counter = 0
            done = False
            deployments = []
            deployment_date = None
            for deployment in updatedService["service"]["deployments"]:
                if deployment["status"] == "ACTIVE":
                    deployments.append(deployment["id"])
                    log("Monitoring active deployment: " + deployment["id"])
                else:
                    deployment_created = deployment["createdAt"]
                    if not deployment_date:
                        deployment_date = deployment_created
                    else:
                        if deployment_date > deployment_created:
                            deployment_date = deployment_created
            startTime = time.time()
            lastEventId = None
            while not done:
                currTime = time.time()
                timeDiff = currTime - startTime
                log("Waiting for ECS to complete the deployment     {0} second(s)...".format(int(timeDiff)))
                if timeDiff > waitTimeout:
                    raise Exception("Wait timeout!")
                try:
                    services = client.describe_services(cluster=cluster, services=[serviceId])
                    if "services" in services and len(services["services"]) > 0:
                        service = services["services"][0]
                        found = False
                        for deployment in service["deployments"]:
                            if (deployment["id"] in deployments) and (deployment["status"] == "ACTIVE"):
                                found = True
                        done = not found
                        if not done:
                            if not hideEvents:
                                events = []
                                for event in service["events"]:
                                    if lastEventId:
                                        eventId = event["id"]
                                        if lastEventId == eventId:
                                            break
                                    if event["createdAt"] >= deployment_date:
                                        events.append(event)
                                if len(events) > 0:
                                    lastEventId = events[0]["id"]
                                while len(events) > 0:
                                    event = events.pop()
                                    log("Event {0}   {1}:   {2}".format(event["id"], event["createdAt"],
                                                                        event["message"]))
                            time.sleep(10)
                        else:
                            log("Deployed successfully!")
                    else:
                        raise ValueError("Service {0} does not exist!".format(serviceId))
                except ValueError as v:
                    raise v
                except Exception as e:
                    counter += 1
                    log(e.message)
                    if counter >= waitRetryCount:
                        raise e
                    else:
                        counter += 1
                        time.sleep(1)
    else:
        raise ValueError("Service {0} not found in cluster {1}".format(serviceId, cluster))
