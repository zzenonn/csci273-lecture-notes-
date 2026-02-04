# Complete Guide: Apache Hive on Google Cloud Dataproc

## Purpose

This comprehensive guide walks you through setting up Apache Hive on Google Cloud Dataproc, copying data from S3 to Google Cloud Storage (GCS), and running Hive queries. This guide uses the Google Cloud Console (web UI) for all configurations.

## Part 1: Network Setup

### Step 1: Create Cloud NAT Gateway (CLI)

Dataproc clusters need internet access to download data from S3. Use these CLI commands to create a Cloud NAT gateway:

```bash
# Step 1: Create the Cloud Router
gcloud compute routers create router-us-central1 \
  --network=default \
  --region=us-central1 \
  --asn=65001

# Step 2: Create the Cloud NAT Gateway
gcloud compute routers nats create nat-us-central1 \
  --router=router-us-central1 \
  --region=us-central1 \
  --nat-all-subnet-ip-ranges \
  --auto-allocate-nat-external-ips
```

**⚠️ COST WARNING:** The NAT gateway costs ~$0.045/hour. Remember to delete it when done!

## Part 2: Create Dataproc Cluster

### Step 2: Create Cluster Using Console

1. Go to [Dataproc > Clusters](https://console.cloud.google.com/dataproc/clusters)
2. Click **"Create Cluster"**
3. Click **"Create cluster on Compute Engine"**

#### Configure Cluster Basics

- **Cluster name**: `hive-cluster` (or your preferred name)
- **Region**: `us-central1`

#### Set up Cluster

**Cluster type**: Standard (1 master, N workers)

#### Configure Nodes

**Master node**:
- **Machine series**: N2
- **Machine type**: `n2-standard-2` (2 vCPUs, 8 GB memory)
- **Primary disk type**: SSD Persistent Disk
- **Primary disk size**: 100 GB

**Worker nodes**:
- **Number of workers**: `2`
- **Machine series**: N2
- **Machine type**: `n2-standard-2` (2 vCPUs, 8 GB memory)
- **Primary disk type**: SSD Persistent Disk
- **Primary disk size**: 100 GB

#### Customize Cluster

Click **"Configure"** under "Customize cluster"

**Cluster properties**:
1. Click **"Add property"**
2. Configure:
   - **Prefix**: `core`
   - **Property**: `fs.s3a.aws.credentials.provider`
   - **Value**: `org.apache.hadoop.fs.s3a.AnonymousAWSCredentialsProvider`
3. Click **"Add"**

This property allows the cluster to access public S3 buckets.

#### Create Cluster

1. Review your configuration
2. Click **"Create"**
3. Wait 3-5 minutes for cluster creation

The cluster will show a green checkmark when ready.

## Part 3: Create GCS Bucket

### Step 3: Create Storage Bucket (CLI)

Create a GCS bucket in the same region as your cluster:

```bash
gsutil mb -l us-central1 gs://<your-bucket-name>/
```

**Important:** Replace `<your-bucket-name>` with a globally unique name (e.g., `<your-project-id>-hive-data`).

Verify the bucket was created:

```bash
gsutil ls
```

## Part 4: Connect to Cluster and Copy Data

### Step 4: SSH into Cluster

1. Go to [Dataproc > Clusters](https://console.cloud.google.com/dataproc/clusters)
2. Click on your cluster name (`hive-cluster`)
3. Click **"VM Instances"** tab
4. Find the master node (ends with `-m`)
5. Click **"SSH"** button

A new browser window will open with a terminal session.

### Step 5: Verify S3 Access

Test that you can access S3:

```bash
# List Ookla dataset
hadoop fs -ls s3a://ookla-open-data/

# List impressions dataset
hadoop fs -ls s3a://elasticmapreduce/samples/hive-ads/tables/impressions/
```

If these commands work, S3 access is configured correctly.

### Step 6: Copy Data from S3 to GCS

Copy the entire Ookla dataset:

```bash
hadoop distcp s3a://ookla-open-data/parquet/ gs://<your-bucket-name>/
```

**Important:** Replace `<your-bucket-name>` with your actual bucket name.

This copies all Ookla performance data. This will take 15-30 minutes.

Verify the copy:

```bash
hadoop fs -ls gs://<your-bucket-name>/performance/
```

## Part 5: Create Hive Tables and Query Data

### Step 7: Start Beeline

```bash
beeline -u jdbc:hive2://localhost:10000
```

You should see:
```
Beeline version 3.1.3 by Apache Hive
beeline>
```

### Step 8: Create Database

```sql
CREATE DATABASE IF NOT EXISTS analytics;
USE analytics;
```

### Step 9: Create Ookla Performance Table

#### Understanding Partitions and Location

When you copied the data with `hadoop distcp s3a://ookla-open-data/parquet/ gs://<your-bucket-name>/`, the data was organized in a directory structure like this:

```
gs://<your-bucket-name>/
└── performance/
    ├── type=mobile/
    │   ├── year=2019/
    │   │   ├── quarter=1/
    │   │   │   └── [parquet files]
    │   │   ├── quarter=2/
    │   │   └── ...
    │   ├── year=2020/
    │   └── ...
    └── type=fixed/
        ├── year=2019/
        └── ...
```

The **LOCATION** in your Hive table should point to the **parent directory** where the partition directories start. In this case, it's `gs://<your-bucket-name>/performance/`.

The **PARTITIONED BY** clause tells Hive which directories represent partitions. Hive expects directories named in the format `key=value` (e.g., `type=mobile`, `year=2024`, `quarter=1`).

#### Create the Table

```sql
CREATE EXTERNAL TABLE mobile_performance (
    quadkey STRING,
    tile STRING,
    avg_d_kbps BIGINT,
    avg_u_kbps BIGINT,
    avg_lat_ms BIGINT,
    tests BIGINT,
    devices BIGINT,
    tile_x DOUBLE,
    tile_y DOUBLE,
    avg_lat_down_ms INT,
    avg_lat_up_ms INT
)
PARTITIONED BY (
    type STRING,
    year STRING,
    quarter STRING
)
STORED AS PARQUET
LOCATION 'gs://<your-bucket-name>/performance/';
```

**Important:** 
- Replace `<your-bucket-name>` with your actual bucket name
- The LOCATION points to `performance/` (the parent directory)
- Do NOT include partition directories (type=mobile, year=2024, etc.) in the LOCATION
- The partition columns (type, year, quarter) are NOT in the column list above - they're only in PARTITIONED BY

#### Discover Partitions

After creating the table, tell Hive to scan the directory and discover all partitions:

```sql
MSCK REPAIR TABLE mobile_performance;
```

This command finds all directories like `type=mobile/year=2024/quarter=1/` and registers them as partitions.

#### Verify Partitions

```sql
SHOW PARTITIONS mobile_performance;
```

You should see multiple partitions like:
```
type=fixed/year=2019/quarter=1
type=fixed/year=2019/quarter=2
type=mobile/year=2019/quarter=1
type=mobile/year=2024/quarter=1
...
```

Each partition represents a specific combination of type, year, and quarter.

### Step 10: Query Ookla Data

#### View Sample Data

```sql
SELECT * FROM mobile_performance LIMIT 10;
```

#### Count Total Records

```sql
SELECT COUNT(*) as total_records 
FROM mobile_performance;
```

### Step 17: Delete Cloud NAT Gateway (CLI)

**Important:** Delete the NAT gateway before deleting the router.

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

## Troubleshooting

### Cannot Access S3

**Issue:** `hadoop fs -ls s3a://...` fails

**Solution:**
1. Verify cluster property is set correctly
2. Check NAT gateway is created and active
3. Restart cluster if needed

### MSCK REPAIR TABLE Finds No Partitions

**Issue:** No partitions discovered

**Solution:**
1. Verify data exists: `hadoop fs -ls gs://<your-bucket-name>/ookla/mobile/`
2. Check directory structure matches partition scheme
3. Ensure partition directories follow `key=value` format

### Query Returns No Results

**Issue:** Query runs but returns 0 rows

**Solution:**
1. Check partitions: `SHOW PARTITIONS mobile_performance;`
2. Try without partition filter: `SELECT COUNT(*) FROM mobile_performance;`
3. Verify data files exist in GCS

## Best Practices

1. **Always delete resources when done** - Avoid unexpected charges
2. **Use the same region** - Cluster, NAT, and GCS bucket in us-central1
3. **Monitor costs** - Check [Billing](https://console.cloud.google.com/billing) regularly
4. **Use external tables** - Data persists even if tables are dropped
5. **Partition large datasets** - Improves query performance
6. **Use Parquet format** - More efficient than text/JSON
