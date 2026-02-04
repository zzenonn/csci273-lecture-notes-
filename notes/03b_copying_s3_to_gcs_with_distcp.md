# Copying Data from S3 to Google Cloud Storage with DistCp

## Purpose

This guide demonstrates how to use Hadoop DistCp (Distributed Copy) to copy large datasets from Amazon S3 to Google Cloud Storage (GCS), then create Hive external tables to query the data. This is useful for migrating data or working with public datasets.

## Prerequisites

- Google Cloud Dataproc cluster running (see guide 03a)
- SSH access to the cluster master node (already connected)
- Basic understanding of Hive and HDFS commands

**Note:** This guide assumes you are already SSH'd into your Dataproc cluster master node. If not, connect using:
```bash
gcloud compute ssh <your-cluster-name>-m --zone=us-central1-a
```

## Why Copy from S3 to GCS?

- **Performance**: Querying data in GCS is faster than accessing S3 from GCP
- **Cost**: Avoid S3 egress charges for repeated queries
- **Integration**: Better integration with other GCP services
- **Reliability**: Data stored in the same cloud provider as your compute

## Example Dataset: Ookla Open Data

We'll use the Ookla Open Data dataset, which contains global network performance metrics. This is a public dataset available on S3.

## Step 1: Create a GCS Bucket

### Using gcloud CLI

```bash
# Create a bucket with a unique name
gsutil mb -l us-central1 gs://<your-bucket-name>/

# Example with your project ID
gsutil mb -l us-central1 gs://<<your-project-id>>-hive-data/
```

**Important:** 
- Replace `<your-bucket-name>` with a globally unique name
- Bucket names must be unique across all of GCS
- Use lowercase letters, numbers, hyphens, and underscores only

### Verify Bucket Creation

```bash
# List your buckets
gsutil ls

# List contents (should be empty)
gsutil ls gs://<your-bucket-name>/
```

## Step 2: Copy Data from S3 to GCS using DistCp

### Explore the Ookla Dataset

First, let's see what's available in the Ookla S3 bucket:

```bash
# List top-level directories
hadoop fs -ls s3a://ookla-open-data/

# List parquet files (network performance data)
hadoop fs -ls s3a://ookla-open-data/parquet/performance/type=mobile/year=2024/quarter=1/
```

### Copy All of the data
Here, this is copying all Parquet data to GCS from S3.
```bash
 hadoop distcp s3a://ookla-open-data/parquet/ gs://<bucket_name>
```

### Copy a Subset of Data

For this example, we'll copy mobile network performance data from Q1 2024:

```bash
# Copy mobile performance data for Q1 2024
hadoop distcp \
  s3a://ookla-open-data/parquet/performance/type=mobile/year=2024/quarter=1/ \
  gs://<your-bucket-name>/ookla/mobile/2024/q1/
```

**Important:** Replace `<your-bucket-name>` with your actual bucket name.

**Note:** This will take several minutes depending on the data size. You'll see progress output showing:
- Number of files copied
- Bytes copied
- Copy speed

### Copy Multiple Quarters (Optional)

To copy more data:

```bash
# Copy Q1 and Q2 2024
hadoop distcp \
  s3a://ookla-open-data/parquet/performance/type=mobile/year=2024/quarter=1/ \
  gs://<your-bucket-name>/ookla/mobile/2024/q1/

hadoop distcp \
  s3a://ookla-open-data/parquet/performance/type=mobile/year=2024/quarter=2/ \
  gs://<your-bucket-name>/ookla/mobile/2024/q2/
```

### Copy Fixed Broadband Data (Alternative)

```bash
# Copy fixed broadband data instead
hadoop distcp \
  s3a://ookla-open-data/parquet/performance/type=fixed/year=2024/quarter=1/ \
  gs://<your-bucket-name>/ookla/fixed/2024/q1/
```

### Copy Impressions Data (JSON)

You can also copy the impressions dataset from the earlier examples:

```bash
# Copy impressions data (JSON format)
hadoop distcp \
  s3a://elasticmapreduce/samples/hive-ads/tables/impressions/ \
  gs://<your-bucket-name>/impressions/
```

This dataset contains ad impression logs in JSON format, which we used in the earlier Hive examples.

### Verify the Copy

```bash
# List files in GCS
hadoop fs -ls gs://<your-bucket-name>/ookla/mobile/2024/q1/

# Or use gsutil
gsutil ls -r gs://<your-bucket-name>/ookla/
```

## Step 3: Create Hive External Table

### Start Beeline

```bash
beeline -u jdbc:hive2://localhost:10000
```

### Create Database

```sql
CREATE DATABASE IF NOT EXISTS ookla_data;
USE ookla_data;
```

### Create External Table for Mobile Performance Data

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
LOCATION 'gs://<your-bucket-name>/parquet/performance/';
```

**Important:** Replace `<your-bucket-name>` with your actual bucket name.

**Explanation:**
- `EXTERNAL TABLE` - Data remains in GCS even if table is dropped
- `PARTITIONED BY` - Organizes data by type, year, and quarter (as STRING)
- `STORED AS PARQUET` - Specifies the file format (Parquet is columnar and efficient)
- `LOCATION` - Points to the GCS bucket path
- Additional fields: `tile`, `tile_x`, `tile_y`, `avg_lat_down_ms`, `avg_lat_up_ms` for more detailed analysis

### Repair Table to Discover Partitions

```sql
MSCK REPAIR TABLE mobile_performance;
```

This command scans the GCS location and discovers all partitions (year/quarter combinations).

### Verify Partitions

```sql
SHOW PARTITIONS mobile_performance;
```

You should see output like:
```
type=mobile/year=2024/quarter=1
```

## Step 4: Query the Data

### View Sample Data

```sql
SELECT * FROM mobile_performance LIMIT 10;
```

### Count Total Records

```sql
SELECT COUNT(*) as total_records 
FROM mobile_performance;
```

### Average Download Speed by Quarter

```sql
SELECT 
    year,
    quarter,
    ROUND(AVG(avg_d_kbps), 2) as avg_download_kbps,
    ROUND(AVG(avg_u_kbps), 2) as avg_upload_kbps,
    ROUND(AVG(avg_lat_ms), 2) as avg_latency_ms,
    SUM(tests) as total_tests
FROM mobile_performance
GROUP BY year, quarter
ORDER BY year, quarter;
```

### Top 10 Locations by Download Speed

```sql
SELECT 
    quadkey,
    ROUND(avg_d_kbps, 2) as download_kbps,
    ROUND(avg_u_kbps, 2) as upload_kbps,
    tests,
    devices
FROM mobile_performance
WHERE year = 2024 AND quarter = 1
ORDER BY avg_d_kbps DESC
LIMIT 10;
```

### Filter by Performance Threshold

```sql
SELECT 
    COUNT(*) as locations,
    AVG(avg_d_kbps) as avg_download
FROM mobile_performance
WHERE year = 2024 
  AND quarter = 1
  AND avg_d_kbps > 50000;  -- Locations with >50 Mbps download
```

## Step 5: Create Table for Fixed Broadband (Optional)

If you copied fixed broadband data:

```sql
CREATE EXTERNAL TABLE fixed_performance (
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
LOCATION 'gs://<your-bucket-name>/ookla/fixed/';

MSCK REPAIR TABLE fixed_performance;
```

### Compare Mobile vs Fixed Performance

```sql
SELECT 
    'Mobile' as network_type,
    ROUND(AVG(avg_d_kbps), 2) as avg_download_kbps,
    ROUND(AVG(avg_lat_ms), 2) as avg_latency_ms
FROM mobile_performance
WHERE year = 2024 AND quarter = 1

UNION ALL

SELECT 
    'Fixed' as network_type,
    ROUND(AVG(avg_d_kbps), 2) as avg_download_kbps,
    ROUND(AVG(avg_lat_ms), 2) as avg_latency_ms
FROM fixed_performance
WHERE year = 2024 AND quarter = 1;
```

## Step 6: Create Table for Impressions Data (Optional)

If you copied the impressions dataset:

```sql
CREATE EXTERNAL TABLE impressions (
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
LOCATION 'gs://<your-bucket-name>/impressions/';

MSCK REPAIR TABLE impressions;
```

### Query Impressions Data

```sql
-- Count total impressions
SELECT COUNT(*) FROM impressions;

-- Top referrers
SELECT referrer, COUNT(*) as visits
FROM impressions
GROUP BY referrer
ORDER BY visits DESC
LIMIT 10;

-- Impressions by ad
SELECT adId, COUNT(*) as impression_count
FROM impressions
GROUP BY adId
ORDER BY impression_count DESC
LIMIT 10;
```

## Understanding the Ookla Data

### Quadkey Explanation

The `quadkey` field is a geospatial identifier that represents a specific tile on a map:
- Longer quadkeys = smaller geographic areas (more precise)
- Shorter quadkeys = larger geographic areas
- Based on Bing Maps Tile System

### Data Fields

- `quadkey` - Geographic tile identifier (Bing Maps Tile System)
- `tile` - Tile identifier string
- `avg_d_kbps` - Average download speed in kilobits per second
- `avg_u_kbps` - Average upload speed in kilobits per second
- `avg_lat_ms` - Average latency in milliseconds
- `tests` - Number of speed tests performed
- `devices` - Number of unique devices tested
- `tile_x` - X coordinate of the tile
- `tile_y` - Y coordinate of the tile
- `avg_lat_down_ms` - Average download latency in milliseconds
- `avg_lat_up_ms` - Average upload latency in milliseconds

## Performance Considerations

### Why Use Parquet?

Parquet is a columnar storage format that:
- Compresses data efficiently (smaller storage costs)
- Allows reading only needed columns (faster queries)
- Works well with Hive and other big data tools

### Query Optimization Tips

1. **Use partition filters** - Always filter by year/quarter when possible:
   ```sql
   WHERE year = 2024 AND quarter = 1
   ```

2. **Select specific columns** - Don't use `SELECT *` for large datasets:
   ```sql
   SELECT quadkey, avg_d_kbps FROM mobile_performance
   ```

3. **Use aggregations** - Summarize data rather than returning all rows:
   ```sql
   SELECT AVG(avg_d_kbps) FROM mobile_performance
   ```

## Cost Considerations

### Storage Costs

- **GCS Standard Storage**: ~$0.020 per GB/month
- **Ookla Q1 2024 mobile data**: ~5-10 GB (varies by quarter)
- **Monthly cost**: ~$0.10-0.20 for one quarter of data

### Data Transfer Costs

- **S3 to GCS (DistCp)**: S3 egress charges apply (~$0.09/GB)
- **Within GCS**: No charges for data access within same region
- **Tip**: Copy only the data you need to minimize transfer costs

### Cleanup

To delete the data and avoid storage costs:

```bash
# Delete the entire bucket
gsutil rm -r gs://<your-bucket-name>/

# Or delete specific paths
gsutil rm -r gs://<your-bucket-name>/ookla/
```

## Troubleshooting

### DistCp Fails with S3 Access Error

**Issue:** Cannot access S3 bucket

**Solution:** Verify the cluster has the S3 property configured:
```bash
hadoop fs -ls s3a://ookla-open-data/
```

If this fails, the cluster needs the `fs.s3a.aws.credentials.provider` property (see guide 03a).

### MSCK REPAIR TABLE Finds No Partitions

**Issue:** `MSCK REPAIR TABLE` returns 0 partitions

**Solution:**
1. Verify data exists in GCS:
   ```bash
   gsutil ls -r gs://<your-bucket-name>/ookla/
   ```

2. Check the directory structure matches the partition scheme:
   ```
   gs://bucket/ookla/mobile/type=mobile/year=2024/quarter=1/
   ```

3. Ensure partition directories follow Hive naming convention: `key=value`

### Query Returns No Results

**Issue:** Query runs but returns 0 rows

**Solution:**
1. Check partitions exist:
   ```sql
   SHOW PARTITIONS mobile_performance;
   ```

2. Verify data in partition:
   ```bash
   hadoop fs -ls gs://<your-bucket-name>/ookla/mobile/2024/q1/
   ```

3. Try querying without partition filter:
   ```sql
   SELECT COUNT(*) FROM mobile_performance;
   ```

## Alternative: Direct S3 Access

Instead of copying to GCS, you can query S3 directly:

```sql
CREATE EXTERNAL TABLE mobile_performance_s3 (
    avg_d_kbps DOUBLE,
    avg_u_kbps DOUBLE,
    avg_lat_ms DOUBLE,
    tests BIGINT,
    devices BIGINT,
    quadkey STRING
)
PARTITIONED BY (
    type STRING,
    year INT,
    quarter INT
)
STORED AS PARQUET
LOCATION 's3a://ookla-open-data/parquet/performance/';

MSCK REPAIR TABLE mobile_performance_s3;
```

**Pros:**
- No data transfer costs
- No GCS storage costs
- Always up-to-date with source data

**Cons:**
- Slower query performance (network latency)
- S3 data transfer charges for each query
- Dependent on S3 availability

## Next Steps

- Explore other Ookla datasets (shapefiles, tiles)
- Join mobile and fixed performance data
- Analyze performance trends over multiple quarters
- Create visualizations using BigQuery or Data Studio
- Export aggregated results back to GCS for reporting

## Summary

You now know how to:

- Create GCS buckets for storing data
- Use DistCp to copy data from S3 to GCS
- Create Hive external tables pointing to GCS
- Query Parquet data efficiently with Hive
- Work with partitioned tables
- Analyze real-world network performance data

This pattern can be applied to any public or private S3 dataset, making it easy to migrate data to GCP for analysis.
