# Installing Apache Hive on Rocky Linux 10

## Purpose

This guide provides step-by-step instructions for installing and configuring Apache Hive on Rocky Linux 10. Hive provides a SQL-like interface (HiveQL) for querying and analyzing large datasets stored in Hadoop HDFS, eliminating the need to write complex MapReduce code.

**Important:** This guide assumes you have already completed the Hadoop installation from the previous notes. Hive requires a running Hadoop environment.

## Prerequisites

### Required Software

- **Rocky Linux 10** with Hadoop installed and configured
- **Java 8 (Amazon Corretto)** - Already installed from Hadoop setup
- **Hadoop 2.x or 3.x** - Running in pseudo-distributed or fully-distributed mode
- **Apache Hive 2.3.9** - Stable release for production use

### Assumptions

- Hadoop is installed and HDFS is running
- JAVA_HOME is properly configured
- HADOOP_HOME is set in your environment
- You have a non-root user with sudo privileges

## Installation Steps

### 1. Verify Environment Variables

Before installing Hive, ensure your Hadoop environment is properly configured. If these are not set, refer to the Hadoop installation notes.

Check your current environment:

```bash
echo $JAVA_HOME
echo $HADOOP_HOME
echo $PATH
```

If HADOOP_HOME is not set, add it to your `~/.bashrc`:

```bash
vim ~/.bashrc
```

Add the following lines if not already present:

```bash
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-amazon-corretto
export HADOOP_HOME=~/hadoop-3.4.2
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
```

Apply the changes:

```bash
source ~/.bashrc
```

### 2. Download Apache Hive

Download the latest stable release of Hive 2.x from the Apache mirrors:

```bash
cd ~
wget https://downloads.apache.org/hive/hive-2.3.9/apache-hive-2.3.9-bin.tar.gz
```

**Note:** We're using Hive 2.3.9 (stable2) as it's the most stable version for Hadoop 3.x and suitable for learning environments. While Hive 3.x is available, version 2.3.9 provides better compatibility and stability.

### 3. Extract Hive Distribution

Extract the downloaded archive:

```bash
tar -xzvf apache-hive-2.3.9-bin.tar.gz
```

This creates a directory named `apache-hive-2.3.9-bin`.

### 4. Configure Hive Environment Variables

Add Hive to your environment by editing `~/.bashrc`:

```bash
vim ~/.bashrc
```

Add the following lines at the end:

```bash
export HIVE_HOME=~/apache-hive-2.3.9-bin
export PATH=$HIVE_HOME/bin:$PATH
```

Apply the changes:

```bash
source ~/.bashrc
```

Verify Hive is in your path:

```bash
which hive
hive --version
```

### 5. Start Hadoop Services

Before configuring Hive, ensure Hadoop is running:

```bash
start-all.sh
```

Verify all services are running:

```bash
jps
```

You should see:
- NameNode
- DataNode
- SecondaryNameNode
- ResourceManager
- NodeManager

### 6. Create HDFS Directories for Hive

Hive requires specific directories in HDFS with proper permissions:

```bash
hdfs dfs -mkdir -p /tmp
hdfs dfs -mkdir -p /user/hive/warehouse
hdfs dfs -chmod g+w /tmp
hdfs dfs -chmod g+w /user/hive/warehouse
```

**Explanation:**
- `/tmp` - Temporary directory for Hive operations
- `/user/hive/warehouse` - Default location for Hive tables (hive.metastore.warehouse.dir)
- `g+w` - Group write permissions required for Hive to function properly

Verify the directories were created:

```bash
hdfs dfs -ls /
hdfs dfs -ls /user/hive
```

### 7. Initialize Hive Metastore

Hive uses a metastore to store metadata about tables, columns, and partitions. For this tutorial, we'll use Derby, an embedded database that doesn't require additional installation.

**Important:** Derby is suitable for testing and learning but not for production. Production environments should use MySQL or PostgreSQL.

Initialize the metastore schema:

```bash
schematool -dbType derby -initSchema
```

You should see output indicating successful schema initialization.

**Note:** This creates a `metastore_db` directory in your current location. The first time you run `hive`, make sure you're in the same directory, or Derby will create a new metastore.

### 8. Verify Hive Installation

Start the Hive CLI:

```bash
hive
```

You should see the Hive prompt:

```
hive>
```

Test basic commands:

```sql
SHOW DATABASES;
```

Expected output:
```
OK
default
Time taken: 0.5 seconds, Fetched: 1 row(s)
```

Exit Hive:

```sql
exit;
```

## Working with Hive - Example Workflow

### Example: Processing JSON Data

This example demonstrates how to process JSON log files using Hive, which would otherwise require complex MapReduce code.

#### 1. Download Sample Data

For this example, we'll use AWS impression logs. Download the sample data:

```bash
cd ~
wget https://s3.amazonaws.com/hw-sandbox/tutorial8/impressions.tar.gz
```

**Note:** If the link is unavailable, any JSON dataset can be used with appropriate schema modifications.

Extract the data:

```bash
tar -xzvf impressions.tar.gz
```

#### 2. Upload Data to HDFS

Upload the impressions data to HDFS:

```bash
hdfs dfs -put impressions /user/$USER/impressions
```

Verify the upload:

```bash
hdfs dfs -ls /user/$USER/impressions
```

#### 3. Start Hive and Create Table

Start Hive:

```bash
hive
```

First, add the JSON SerDe (Serializer/Deserializer) library:

```sql
ADD JAR /path/to/hive-hcatalog-core.jar;
```

**Note:** The exact path depends on your Hive installation. Typically found in `$HIVE_HOME/hcatalog/share/hcatalog/`.

Create an external table for the JSON data:

```sql
CREATE EXTERNAL TABLE impressions (
    requestBeginTime STRING,
    adId STRING,
    impressionId STRING,
    referrer STRING,
    userAgent STRING,
    userCookie STRING,
    ip STRING
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION '/user/$USER/impressions';
```

**Explanation:**
- `EXTERNAL TABLE` - Data remains in HDFS even if table is dropped
- `ROW FORMAT SERDE` - Specifies JSON SerDe for parsing JSON files
- `LOCATION` - Points to HDFS directory containing the data

#### 4. Load Metadata

Repair the table to load partition metadata:

```sql
MSCK REPAIR TABLE impressions;
```

#### 5. Query the Data

Now you can use SQL to query the data:

```sql
SELECT requestBeginTime FROM impressions LIMIT 10;
```

Count total records:

```sql
SELECT COUNT(*) FROM impressions;
```

**Note:** Hive converts these SQL queries into MapReduce jobs automatically. You'll see MapReduce job progress in the output.

#### 6. View Databases and Tables

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
DESCRIBE impressions;
```

### Performance Considerations

Hive queries run as MapReduce jobs, which means:
- Initial setup time for each query
- Better suited for batch processing than interactive queries
- Queries on small datasets may be slower than direct file processing

**Tip:** For faster query execution, newer versions of Hive can use Apache Spark instead of MapReduce as the execution engine.

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

To see logs in the console:

```bash
hive --hiveconf hive.root.logger=INFO,console
```

To change log level:

```bash
hive --hiveconf hive.root.logger=DEBUG,DRFA
```

## Managing Hive Sessions

### Starting Hive

```bash
hive
```

### Exiting Hive

```sql
exit;
```

Or:

```sql
quit;
```

### Running Hive Scripts

Execute HiveQL from a file:

```bash
hive -f script.hql
```

Execute inline commands:

```bash
hive -e "SHOW DATABASES;"
```

## Persistent Tables

Once you create tables in Hive, they persist across sessions:

1. Tables remain available after exiting Hive
2. Metadata is stored in the Derby metastore
3. Data remains in HDFS at the specified location
4. You can add more files to the HDFS directory, and they'll be automatically included in queries

**Example:**

```bash
# Add more data files
hdfs dfs -put newdata.json /user/$USER/impressions/

# Query will automatically include new files
hive -e "SELECT COUNT(*) FROM impressions;"
```

## Common Issues and Troubleshooting

### Derby Metastore Issues

**Symptom:** "Another instance of Derby may have already booted the database"

**Solution:**
- Only one Hive session can use Derby at a time
- Ensure no other Hive processes are running
- For multi-user environments, use MySQL or PostgreSQL instead

### HADOOP_HOME Not Set

**Symptom:** "HADOOP_HOME is not set" error

**Solution:**
1. Verify HADOOP_HOME in `~/.bashrc`
2. Run `source ~/.bashrc`
3. Test with `echo $HADOOP_HOME`

### Permission Denied in HDFS

**Symptom:** Permission errors when creating tables

**Solution:**
```bash
hdfs dfs -chmod -R 777 /user/hive/warehouse
hdfs dfs -chmod -R 777 /tmp
```

**Note:** 777 permissions are acceptable for learning environments but not for production.

### Hadoop Not Running

**Symptom:** "Connection refused" errors

**Solution:**
1. Check Hadoop services: `jps`
2. Start Hadoop if needed: `start-all.sh`
3. Verify HDFS is accessible: `hdfs dfs -ls /`

## Best Practices

1. **Always start Hadoop before Hive** - Hive requires HDFS and YARN to be running
2. **Use external tables** - Data persists even if tables are dropped
3. **Partition large tables** - Improves query performance
4. **Use appropriate file formats** - ORC and Parquet are more efficient than text
5. **Monitor MapReduce jobs** - Check ResourceManager UI at http://localhost:8088/
6. **Clean up temporary files** - Hive creates temporary files in `/tmp`
7. **Use production metastore** - Replace Derby with MySQL/PostgreSQL for production

## Upgrading to Production

For production environments, consider:

1. **External Metastore** - Use MySQL or PostgreSQL instead of Derby
2. **HiveServer2** - Enables multi-user access and JDBC/ODBC connections
3. **Beeline** - Modern CLI that connects to HiveServer2
4. **Security** - Implement Kerberos authentication
5. **High Availability** - Configure metastore HA
6. **Performance** - Use Tez or Spark execution engine instead of MapReduce

## Next Steps

- Explore HiveQL syntax and advanced queries
- Learn about partitioning and bucketing
- Experiment with different file formats (ORC, Parquet)
- Set up HiveServer2 for multi-user access
- Integrate with BI tools using JDBC/ODBC
- Explore Hive optimization techniques

## Summary

You now have a working Apache Hive installation on Rocky Linux 10 that:

- Uses Derby as an embedded metastore (suitable for learning)
- Integrates with your existing Hadoop installation
- Provides SQL-like interface for querying HDFS data
- Automatically converts HiveQL to MapReduce jobs
- Supports JSON and other data formats via SerDes

This setup allows you to analyze large datasets using familiar SQL syntax without writing complex MapReduce code.
