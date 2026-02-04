# Running Apache Hive on Google Cloud Dataproc

## Purpose

This guide provides instructions for running Apache Hive on Google Cloud Dataproc, a managed Hadoop and Spark service. Dataproc comes with Hive pre-installed and configured, making it easier to get started compared to manual installation.

## Prerequisites

- Google Cloud Platform (GCP) account
- `gcloud` CLI installed and configured
- Basic understanding of GCP services
- Completed the Hive basics from the previous notes

## Why Use Dataproc?

- **Pre-configured**: Hive, Hadoop, and Spark are already installed
- **Managed**: Google handles cluster management and updates
- **Scalable**: Easy to scale up or down based on workload
- **Cost-effective**: Pay only for what you use, can delete clusters when done
- **Integration**: Works seamlessly with Google Cloud Storage (GCS)

## Step 1: Configure Network Access (NAT Gateway)

Dataproc clusters by default have no internet access. To enable internet connectivity (needed for downloading data, accessing S3, etc.), you need to create a Cloud NAT gateway.

### Create NAT Gateway for us-central1

```bash
# Step 1: Create the Cloud Router
# This creates the router required for the NAT gateway
gcloud compute routers create router-us-central1 \
  --network=default \
  --region=us-central1 \
  --asn=65001

# Step 2: Create the Cloud NAT Gateway
# This creates the NAT gateway and attaches it to the router
gcloud compute routers nats create nat-us-central1 \
  --router=router-us-central1 \
  --region=us-central1 \
  --nat-all-subnet-ip-ranges \
  --auto-allocate-nat-external-ips
```

**⚠️ IMPORTANT - COST WARNING:**
- The NAT gateway incurs charges (~$0.045/hour + data processing fees)
- **Delete the NAT gateway immediately after you're done** to avoid unnecessary costs
- The NAT is only needed while the cluster is running and needs internet access
- See the cleanup section below for deletion commands

### Verify NAT Gateway

```bash
# List routers
gcloud compute routers list --filter="region:us-central1"

# List NAT gateways
gcloud compute routers nats list --router=router-us-central1 --region=us-central1
```

## Step 2: Create a Dataproc Cluster

### Using Google Cloud Console (Web UI)

1. Go to the [Dataproc Clusters page](https://console.cloud.google.com/dataproc/clusters)
2. Click **"Create Cluster"**
3. Configure the cluster:

**Cluster Basics:**
- **Cluster name**: `hive-test-cluster` (or your preferred name)
- **Region**: `us-central1`
- **Cluster type**: **Single Node** (1 master, 0 workers)
  - This is perfect for testing and learning
  - Lower cost than multi-node clusters

**Configure nodes:**
- **Machine type**: `n1-standard-2` (2 vCPUs, 7.5 GB memory)
- **Primary disk size**: 100 GB (default)

**Customize cluster (Optional components):**
- Select **Hive WebHCat** if you want web interface access

**Cluster properties:**
- Click **"Add property"**
- **Prefix**: `Core`
- **Property**: `fs.s3a.aws.credentials.provider`
- **Value**: `org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider`

This property allows the cluster to access S3 data (needed for the impressions example).

4. Click **"Create"**

The cluster will take 2-3 minutes to provision.

### Using gcloud CLI

Alternatively, create the cluster using the command line:

```bash
gcloud dataproc clusters create cluster-a346 \
  --enable-component-gateway \
  --region us-central1 \
  --no-address \
  --single-node \
  --master-machine-type n4-standard-2 \
  --master-boot-disk-type hyperdisk-balanced \
  --master-boot-disk-size 100 \
  --image-version 2.2-debian12 \
  --properties core:fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.AnonymousAWSCredentialsProvider \
  --scopes 'https://www.googleapis.com/auth/cloud-platform'
```

**Explanation:**
- `--enable-component-gateway` - Enables web interface access through GCP console
- `--no-address` - No external IP (uses NAT for internet access)
- `--single-node` - Creates a cluster with 1 master and 0 workers (for testing)
- `--master-machine-type n4-standard-2` - Uses N4 series VM (2 vCPUs, 8 GB memory)
- `--master-boot-disk-type hyperdisk-balanced` - Uses Hyperdisk Balanced for better performance
- `--master-boot-disk-size 100` - 100 GB boot disk
- `--image-version 2.2-debian12` - Dataproc image version (includes Hadoop, Hive, Spark)
- `--properties` - Sets the S3 credentials provider to Anonymous (for public S3 buckets)
- `--scopes` - Grants full cloud platform access to the cluster

**Note:** Change `cluster-a346` to your preferred cluster name.

### Verify Cluster Creation

```bash
# List clusters
gcloud dataproc clusters list --region=us-central1

# Get cluster details
gcloud dataproc clusters describe cluster-a346 --region=us-central1
```

**Note:** Replace `cluster-a346` with your actual cluster name.

## Step 3: Connect to the Cluster

### SSH into the Master Node

```bash
gcloud compute ssh cluster-a346-m --zone=us-central1-a
```

**Note:** 
- Replace `cluster-a346` with your actual cluster name
- The master node is named `<cluster-name>-m` by default
- The zone may vary; check your cluster details if connection fails

Once connected, you'll be in the master node's terminal.

### Verify Hive Installation

```bash
# Check Hive version
hive --version

# Check Beeline
beeline --version

# Check Hadoop
hadoop version
```

## Step 4: Working with Hive on Dataproc

### Start Beeline

```bash
beeline -u jdbc:hive2://localhost:10000
```

You should see the Beeline prompt:

```
Beeline version 3.1.3 by Apache Hive
beeline>
```

### Run Basic Commands

```sql
-- Show databases
SHOW DATABASES;

-- Create a test database
CREATE DATABASE test_db;

-- Use the database
USE test_db;

-- Show tables
SHOW TABLES;
```

### Exit Beeline

```sql
!quit
```

## Step 5: Working with Data

### Using Google Cloud Storage (GCS)

Dataproc integrates seamlessly with GCS. You can create external tables pointing to GCS:

```sql
CREATE EXTERNAL TABLE gcs_data (
    id INT,
    name STRING,
    value DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION 'gs://your-bucket-name/data/';
```

**Note:** Replace `your-bucket-name` with your actual GCS bucket name.

### Using S3 Data (with the configured property)

You can also access S3 data directly:

```sql
CREATE EXTERNAL TABLE impressions_s3 (
    number STRING,
    referrer STRING,
    processId STRING,
    adId STRING,
    browserCookie STRING,
    userCookie STRING,
    requestEndTime STRING,
    impressionId STRING,
    userAgent STRING,
    timers STRUCT<modelLookup:STRING, requestTime:STRING>,
    threadId STRING,
    ip STRING,
    modelId STRING,
    hostname STRING,
    sessionId STRING,
    requestBeginTime STRING
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION 's3a://elasticmapreduce/samples/hive-ads/tables/impressions/';
```

### Using HDFS

You can also use HDFS on the cluster:

```bash
# Create directory in HDFS
hadoop fs -mkdir -p /user/$USER/data

# Upload data
hadoop fs -put local-file.csv /user/$USER/data/

# Create table pointing to HDFS
beeline -u jdbc:hive2://localhost:10000
```

```sql
CREATE EXTERNAL TABLE hdfs_data (
    col1 STRING,
    col2 INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION '/user/<your-username>/data/';
```

## Step 6: Running Queries from Examples

You can now run all the examples from the "Working with Hive" guide:

1. **Titanic CSV example** - Upload CSV to GCS or HDFS
2. **JSON impressions example** - Access directly from S3 (already configured)
3. **All HiveQL operations** - Work the same as on a local installation

## Step 7: Monitoring and Management

### Dataproc Web Interfaces

Access the Hadoop and Hive web interfaces:

1. Go to the [Dataproc Clusters page](https://console.cloud.google.com/dataproc/clusters)
2. Click on your cluster name
3. Click on **"Web Interfaces"** tab
4. Access:
   - **YARN ResourceManager** - Monitor MapReduce jobs
   - **HDFS NameNode** - Browse HDFS files
   - **Hive WebHCat** - Hive web interface (if enabled)

### View Logs

```bash
# View Hive logs
gcloud dataproc jobs list --region=us-central1 --cluster=cluster-a346

# Get job details
gcloud dataproc jobs describe <job-id> --region=us-central1
```

**Note:** Replace `cluster-a346` with your actual cluster name.

## Step 8: Cleanup (Important!)

**⚠️ CRITICAL - AVOID UNEXPECTED CHARGES:**

When you're done, **immediately delete all resources** to avoid charges. The NAT gateway and cluster both incur hourly charges even when idle.

### Delete the Dataproc Cluster

```bash
gcloud dataproc clusters delete cluster-a346 --region=us-central1
```

**Note:** Replace `cluster-a346` with your actual cluster name.

Or via the console:
1. Go to Dataproc Clusters page
2. Select your cluster
3. Click **"Delete"**

### Delete the NAT Gateway and Router

**⚠️ IMPORTANT:** Delete the NAT gateway before deleting the router.

```bash
# Step 1: Delete the Cloud NAT Gateway
gcloud compute routers nats delete nat-us-central1 \
  --router=router-us-central1 \
  --region=us-central1

# Step 2: Delete the Cloud Router
gcloud compute routers delete router-us-central1 \
  --region=us-central1
```

Both commands will prompt you for confirmation.

**💰 COST SAVINGS TIP:** The NAT gateway costs ~$0.045/hour. Deleting it immediately after your work can save significant costs over time.

### Verify Deletion

```bash
# Check clusters
gcloud dataproc clusters list --region=us-central1

# Check routers
gcloud compute routers list --filter="region:us-central1"
```

## Cost Considerations

### Dataproc Pricing

- **Single-node cluster (n1-standard-2)**: ~$0.10-0.15/hour
- **NAT Gateway**: ~$0.045/hour + data processing charges
- **Storage**: GCS or HDFS storage charges

### Cost-Saving Tips

1. **Delete clusters when not in use** - Don't leave clusters running overnight
2. **Use preemptible VMs** - For non-critical workloads (add `--worker-machine-type=n1-standard-2 --num-preemptible-workers=2`)
3. **Use GCS instead of HDFS** - Cheaper for long-term storage
4. **Set auto-delete** - Configure clusters to auto-delete after idle time

## Advantages of Dataproc vs Local Installation

| Aspect | Dataproc | Local Installation |
|--------|----------|-------------------|
| Setup Time | 2-3 minutes | 30-60 minutes |
| Configuration | Pre-configured | Manual setup required |
| Scalability | Easy to scale | Limited by hardware |
| Maintenance | Managed by Google | Manual updates |
| Cost | Pay per use | Fixed hardware cost |
| Internet Access | Requires NAT | Direct access |
| Integration | GCS, BigQuery | Local filesystem |

## Troubleshooting

### Cluster Creation Fails

**Issue:** Quota exceeded

**Solution:** Check your GCP quotas and request increases if needed:
```bash
gcloud compute project-info describe --project=<your-project-id>
```

### Cannot Access S3 Data

**Issue:** S3 access denied or connection timeout

**Solution:** 
1. Verify the cluster property is set: `fs.s3a.aws.credentials.provider`
2. Check NAT gateway is configured
3. For private S3 buckets, add AWS credentials as cluster properties

### Beeline Connection Refused

**Issue:** Cannot connect to HiveServer2

**Solution:**
```bash
# Check if HiveServer2 is running
sudo systemctl status hive-server2

# Restart if needed
sudo systemctl restart hive-server2
```

## Next Steps

- Explore the Titanic and impressions examples from the main guide
- Try creating tables with GCS data
- Experiment with partitioning and bucketing
- Learn about Dataproc jobs API for automation
- Integrate with BigQuery for analytics

## Summary

You now have a working Hive environment on Google Cloud Dataproc that:

- Runs on a managed, pre-configured cluster
- Has internet access via Cloud NAT
- Can access data from S3, GCS, and HDFS
- Provides the same Hive functionality as local installation
- Can be easily scaled and deleted to control costs

This setup is ideal for learning, testing, and running production Hive workloads without managing infrastructure.
