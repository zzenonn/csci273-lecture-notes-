# Working with Apache Hive

## Purpose

This guide demonstrates how to use Apache Hive for data analysis, including creating tables, loading data, and running queries. This assumes you have completed the Hive installation from the previous notes.

## Prerequisites

- Hive 4.0.1 installed and configured
- Hadoop running with HDFS accessible
- Basic understanding of SQL

## Example 1: Processing CSV Data (Titanic Dataset)

This example demonstrates basic Hive operations using a simple CSV file.

### 1. Download Sample Data

Download the Titanic dataset:

```bash
cd ~
wget https://raw.githubusercontent.com/datasciencedojo/datasets/refs/heads/master/titanic.csv
```

View the first few lines to understand the structure:

```bash
head titanic.csv
```

### 2. Upload Data to HDFS

Create a directory in HDFS and upload the data:

```bash
hadoop fs -mkdir -p /user/<your-username>/titanic
hadoop fs -put titanic.csv /user/<your-username>/titanic/
```

**Important:** Replace `<your-username>` with your actual username (e.g., `zenon`, `hadoop`, etc.).

Verify the upload:

```bash
hadoop fs -ls /user/<your-username>/titanic
```

### 3. Create Table in Hive

Start Beeline:

```bash
beeline -u jdbc:hive2://
```

Create an external table for the Titanic data:

```sql
CREATE EXTERNAL TABLE titanic (
    PassengerId INT,
    Survived INT,
    Pclass INT,
    Name STRING,
    Sex STRING,
    Age DOUBLE,
    SibSp INT,
    Parch INT,
    Ticket STRING,
    Fare DOUBLE,
    Cabin STRING,
    Embarked STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/<your-username>/titanic/'
TBLPROPERTIES ("skip.header.line.count"="1");
```

**Important:** Replace `<your-username>` with your actual username in the LOCATION path.

**Explanation:**
- `EXTERNAL TABLE` - Data remains in HDFS even if table is dropped
- `ROW FORMAT DELIMITED` - Data is in delimited text format
- `FIELDS TERMINATED BY ','` - CSV format with comma separator
- `LOCATION` - Points to HDFS directory containing the data
- `TBLPROPERTIES ("skip.header.line.count"="1")` - Skip the header row

### 4. Repair Table Metadata

Since this is an external table, tell Hive to discover the data files:

```sql
MSCK REPAIR TABLE titanic;
```

**Note:** `MSCK REPAIR TABLE` scans the HDFS location and updates the metastore with information about the data files. This is required for external tables.

### 5. Query the Data

View first 10 rows:

```sql
SELECT * FROM titanic LIMIT 10;
```

Count total passengers:

```sql
SELECT COUNT(*) as total_passengers FROM titanic;
```

Calculate survival rate:

```sql
SELECT 
    Survived,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM titanic
GROUP BY Survived;
```

Survival rate by gender:

```sql
SELECT 
    Sex,
    SUM(Survived) as survived,
    COUNT(*) as total,
    ROUND(SUM(Survived) * 100.0 / COUNT(*), 2) as survival_rate
FROM titanic
GROUP BY Sex;
```

Average fare by passenger class:

```sql
SELECT 
    Pclass,
    ROUND(AVG(Fare), 2) as avg_fare,
    COUNT(*) as passengers
FROM titanic
GROUP BY Pclass
ORDER BY Pclass;
```

## Example 2: Processing JSON Data from S3

This example demonstrates how to work with JSON data stored in Amazon S3, including copying to HDFS and accessing directly from S3.

### Prerequisites: Configure S3 Access

Before accessing S3 data, you need to configure Hadoop with the necessary libraries and settings.

#### 1. Check for Required JARs

Check if the AWS JARs are present:

```bash
ls $HADOOP_HOME/share/hadoop/tools/lib | grep aws
```

You should see both:
- `hadoop-aws-*.jar`
- `aws-java-sdk-bundle-*.jar`

#### 2. Download Missing JARs (if needed)

If the JARs are missing (common on local installs), download them:

```bash
cd $HADOOP_HOME/share/hadoop/tools/lib
curl -O https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.2/hadoop-aws-3.4.2.jar
curl -O https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.683/aws-java-sdk-bundle-1.12.683.jar
```

**Note:** Match the `hadoop-aws` version to your Hadoop version (3.4.2 in this guide).

#### 3. Configure S3 Access in Hadoop

Edit the Hadoop configuration:

```bash
vim $HADOOP_HOME/etc/hadoop/core-site.xml
```

Add the following properties inside the `<configuration>` block:

```xml
<property>
    <name>fs.s3a.impl</name>
    <value>org.apache.hadoop.fs.s3a.S3AFileSystem</value>
</property>

<property>
    <name>fs.s3a.aws.credentials.provider</name>
    <value>org.apache.hadoop.fs.s3a.AnonymousAWSCredentialsProvider</value>
</property>
```

**Explanation:**
- `fs.s3a.impl` - Specifies the S3A filesystem implementation
- `AnonymousAWSCredentialsProvider` - Allows access to public S3 buckets without credentials

**For private S3 buckets**, use this instead:

```xml
<property>
    <name>fs.s3a.access.key</name>
    <value>YOUR_ACCESS_KEY</value>
</property>

<property>
    <name>fs.s3a.secret.key</name>
    <value>YOUR_SECRET_KEY</value>
</property>

<property>
    <name>fs.s3a.aws.credentials.provider</name>
    <value>org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider</value>
</property>
```

#### 4. Restart Hadoop

Restart Hadoop services to apply the configuration:

```bash
stop-all.sh
start-all.sh
```

#### 5. Verify S3 Access

Test access to the S3 bucket:

```bash
hadoop fs -ls s3a://elasticmapreduce/samples/hive-ads/tables/impressions/
```

You should see a list of files in the S3 bucket. If you get an error, check:
- JARs are in the correct location
- Configuration is correct in `core-site.xml`
- Hadoop services were restarted

### Method A: Copy from S3 to HDFS using DistCp

DistCp (Distributed Copy) is Hadoop's tool for large-scale data copying.

#### 1. Copy Data from S3 to HDFS

Use Hadoop DistCp to copy the impressions data from S3:

```bash
hadoop distcp s3a://elasticmapreduce/samples/hive-ads/tables/impressions/ /user/<your-username>/impressions/
```

**Important:** Replace `<your-username>` with your actual username.

This will copy all files from the S3 bucket to your HDFS directory.

Verify the data was copied:

```bash
hadoop fs -ls /user/<your-username>/impressions/
hadoop fs -cat /user/<your-username>/impressions/000000_0 | head -5
```

#### 2. Create External Table for JSON Data

Start Beeline:

```bash
beeline -u jdbc:hive2://
```

Create an external table pointing to the HDFS location:

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
LOCATION '/user/<your-username>/impressions/';
```

**Important:** Replace `<your-username>` with your actual username in the LOCATION path.

**Explanation:**
- `EXTERNAL TABLE` - Data remains in HDFS even if table is dropped
- `ROW FORMAT SERDE` - Specifies JSON SerDe for parsing JSON files
- `STRUCT` - For nested JSON objects like `timers`
- `LOCATION` - Points to HDFS directory containing the data

#### 3. Query the Data

View sample records:

```sql
SELECT * FROM impressions LIMIT 10;
```

View specific fields:

```sql
SELECT requestBeginTime, adId, referrer, ip 
FROM impressions 
LIMIT 10;
```

Count total impressions:

```sql
SELECT COUNT(*) FROM impressions;
```

Count impressions by ad:

```sql
SELECT adId, COUNT(*) as impression_count
FROM impressions
GROUP BY adId
ORDER BY impression_count DESC
LIMIT 10;
```

Top referrers:

```sql
SELECT referrer, COUNT(*) as visits
FROM impressions
GROUP BY referrer
ORDER BY visits DESC
LIMIT 10;
```

Access nested timer data:

```sql
SELECT 
    adId,
    timers.modelLookup,
    timers.requestTime
FROM impressions
LIMIT 10;
```
ORDER BY impression_count DESC
LIMIT 10;
```

### Method B: Access S3 Data Directly

You can also query data directly from S3 without copying to HDFS.

#### 1. Create External Table Pointing to S3

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

**Note:** This uses the S3 configuration you set up in the prerequisites section.

#### 2. Query S3 Data Directly

```sql
SELECT COUNT(*) FROM impressions_s3;
```

**Advantages of Direct S3 Access:**
- No need to copy data to HDFS
- Saves storage space
- Data stays in S3 for other applications

**Disadvantages:**
- Slower query performance (network latency)
- Requires AWS credentials
- Incurs S3 data transfer costs

### Comparison: HDFS vs S3

| Aspect | HDFS (DistCp) | Direct S3 Access |
|--------|---------------|------------------|
| Performance | Faster (local) | Slower (network) |
| Storage | Uses HDFS space | No local storage needed |
| Cost | No transfer costs | S3 transfer costs |
| Setup | One-time copy | Requires credentials |
| Best for | Frequent queries | Occasional queries |

**Important:** Replace `<your-username>` with your actual username.

Then create the table as shown in Method A, step 2.

## Basic Hive Operations

### View Databases and Tables

List all databases:

```sql
SHOW DATABASES;
```

List tables in current database:

```sql
SHOW TABLES;
```

Describe table structure:

```sql
DESCRIBE titanic;
DESCRIBE impressions;
```

Show detailed table information:

```sql
DESCRIBE FORMATTED titanic;
```

### Drop Tables

Drop a table (data remains in HDFS for external tables):

```sql
DROP TABLE IF EXISTS impressions_s3;
```

## Managing Beeline Sessions

### Starting Beeline

For testing (embedded mode - starts HiveServer2 automatically):

```bash
beeline -u jdbc:hive2://
```

For production (connect to running HiveServer2):

First, start HiveServer2 as a background service:

```bash
hiveserver2 &
```

Then connect with Beeline:

```bash
beeline -u jdbc:hive2://localhost:10000
```

**Note:** In production, HiveServer2 should be run as a system service, not as a background process.

### Exiting Beeline

```sql
!quit
```

Or:

```sql
exit;
```

### Running HiveQL Scripts

Execute HiveQL from a file:

```bash
beeline -u jdbc:hive2:// -f script.hql
```

Execute inline commands:

```bash
beeline -u jdbc:hive2:// -e "SHOW DATABASES;"
```

## Persistent Tables

Once you create tables in Hive, they persist across sessions:

1. Tables remain available after exiting Beeline
2. Metadata is stored in the Derby metastore
3. Data remains in HDFS at the specified location
4. You can add more files to the HDFS directory, and they'll be automatically included in queries

**Example:**

```bash
# Add more data files
hadoop fs -put newdata.json /user/<your-username>/impressions/

# Query will automatically include new files
beeline -u jdbc:hive2:// -e "SELECT COUNT(*) FROM impressions;"
```

**Important:** Replace `<your-username>` with your actual username.

## Configuration Files

### Important Configuration Locations

- **hive-site.xml** - Main configuration file (`$HIVE_HOME/conf/hive-site.xml`)
- **hive-default.xml** - Default configurations (`$HIVE_HOME/conf/hive-default.xml`)
- **hive-log4j.properties** - Logging configuration (`$HIVE_HOME/conf/hive-log4j.properties`)

### Common Configuration Options

To customize Hive, create or edit `$HIVE_HOME/conf/hive-site.xml`:

```xml
<configuration>
    <property>
        <name>hive.metastore.warehouse.dir</name>
        <value>/user/hive/warehouse</value>
        <description>Default location for Hive tables</description>
    </property>
    
    <property>
        <name>hive.exec.mode.local.auto</name>
        <value>false</value>
        <description>Enable automatic local mode for small datasets</description>
    </property>
</configuration>
```

## Hive Logging

### Log Locations

Hive stores logs in `/tmp/<username>/`:
- `hive.log` - Main Hive log file
- Query logs - Per-session query logs

### Viewing Logs

To see logs in the console with Beeline:

```bash
beeline -u jdbc:hive2:// --hiveconf hive.root.logger=INFO,console
```

To change log level:

```bash
beeline -u jdbc:hive2:// --hiveconf hive.root.logger=DEBUG,DRFA
```

For HiveServer2 logs:

```bash
hiveserver2 --hiveconf hive.root.logger=INFO,console
```

## Performance Considerations

Hive queries run as MapReduce jobs, which means:
- Initial setup time for each query
- Better suited for batch processing than interactive queries
- Queries on small datasets may be slower than direct file processing

**Tip:** For faster query execution, newer versions of Hive can use Apache Spark instead of MapReduce as the execution engine.

## Best Practices

1. **Use external tables** - Data persists even if tables are dropped
2. **Partition large tables** - Improves query performance significantly
3. **Use appropriate file formats** - ORC and Parquet are more efficient than text
4. **Avoid SELECT *** - Specify only the columns you need
5. **Use LIMIT for testing** - Test queries on small subsets before running on full data
6. **Monitor MapReduce jobs** - Check ResourceManager UI at http://localhost:8088/
7. **Clean up temporary files** - Hive creates temporary files in `/tmp`

## Common HiveQL Operations

### Creating Databases

```sql
CREATE DATABASE mydb;
USE mydb;
```

### Creating Tables

Internal table (managed by Hive):

```sql
CREATE TABLE users (
    id INT,
    name STRING,
    email STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE;
```

External table (data managed separately):

```sql
CREATE EXTERNAL TABLE users_ext (
    id INT,
    name STRING,
    email STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION '/user/data/users';
```

### Loading Data

Load data from local file:

```sql
LOAD DATA LOCAL INPATH '/path/to/file.csv' INTO TABLE users;
```

Load data from HDFS:

```sql
LOAD DATA INPATH '/user/data/file.csv' INTO TABLE users;
```

### Partitioned Tables

Create partitioned table:

```sql
CREATE TABLE logs (
    timestamp STRING,
    message STRING
)
PARTITIONED BY (year INT, month INT)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ',';
```

Add partition:

```sql
ALTER TABLE logs ADD PARTITION (year=2024, month=1)
LOCATION '/user/data/logs/2024/01';
```

### Querying Data

Basic SELECT:

```sql
SELECT * FROM users WHERE id > 100;
```

Aggregations:

```sql
SELECT COUNT(*), AVG(id) FROM users;
```

Joins:

```sql
SELECT u.name, o.order_id
FROM users u
JOIN orders o ON u.id = o.user_id;
```

Group by:

```sql
SELECT name, COUNT(*) as order_count
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY name
ORDER BY order_count DESC;
```

## Next Steps

- Explore partitioning and bucketing for better performance
- Learn about Hive optimization techniques
- Experiment with different file formats (ORC, Parquet)
- Set up HiveServer2 for multi-user access
- Integrate with BI tools using JDBC/ODBC
- Explore Hive UDFs (User Defined Functions)

## Summary

This guide covered:
- Processing JSON data with Hive
- Creating external tables with SerDes
- Running SQL queries on HDFS data
- Managing Beeline sessions
- Common HiveQL operations
- Best practices for Hive usage

Hive provides a powerful SQL interface for analyzing large datasets in Hadoop without writing complex MapReduce code.


gcloud dataproc clusters create cluster-a345 --enable-component-gateway --region us-central1 --no-address --single-node --master-machine-type n4-standard-2 --master-boot-disk-type hyperdisk-balanced --master-boot-disk-size 100 --image-version 2.2-debian12 --properties core:fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.AnonymousAWSCredentialsProvider --scopes 'https://www.googleapis.com/auth/cloud-platform' --project admu-iscs-30-23