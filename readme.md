# Performance Monitoring 

**Goal:** Measure the CPU-cycles taken by a particular microservice (of interest) in an open-source benchmark suite called DeathStarBench, on multiple nodes.

To measure microarchitectural statistics, Perf requires the PID as an argument. Follow the steps below to obtain it.

```bash

## Step 1: Identify Task ID - Run this on the master node

# List Docker services to find the task id of the microservice you want to profile
sudo docker service ls

## Step 2: Identify Node

sudo docker service ps <task-id-of-the-microservice>

# Identify the node number and SSH into it 

## Step 3: Obtain Container ID

# List running containers to identify the container ID of the microservice of interest
sudo docker ps

# Identify the container ID of the microservice of interest.

# Use docker inspect to get the PID of the container
docker inspect --format '{{.State.Pid}}' <container-id>

# This command returns the PID. Use this PID to perform monitoring by passing it to Perf.

# Record microarchitectural statistics (CPU cycles) for 60 seconds
sudo perf record -g -e cycles -p <PID> sleep 60

# The output is written to a file called perf.data. Add any necessary comments as required.
```
