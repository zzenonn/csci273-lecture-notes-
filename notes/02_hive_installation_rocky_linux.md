# Installing Apache Hive on Rocky Linux 10

> **⚠️ UNDER CONSTRUCTION ⚠️**
> 
> **This guide is currently under development and may contain issues. The Hive 4.0.1 installation is experiencing classpath configuration problems with the schematool initialization. Please check back later for a working version or use alternative Hive installation methods.**

## Purpose

This guide provides step-by-step instructions for installing and configuring Apache Hive on Rocky Linux 10. Hive provides a SQL-like interface (HiveQL) for querying and analyzing large datasets stored in Hadoop HDFS, eliminating the need to write complex MapReduce code.

**Important:** This guide assumes you have already completed the Hadoop installation from the previous notes. Hive requires a running Hadoop environment.

## Prerequisites

### Required Software

- **Rocky Linux 10** with Hadoop installed and configured
- **Java 8 (Amazon Corretto)** - Already installed from Hadoop setup
- **Hadoop 2.x or 3.x** - Running in pseudo-distributed or fully-distributed mode
- **Apache Hive 4.0.1** - Stable release compatible with Java 8

**Note:** Hive 4.0.1 is compatible with Java 8, unlike newer versions which require Java 11+.

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

Download Hive 4.0.1 from the Apache archives:

```bash
cd ~
wget https://archive.apache.org/dist/hive/hive-4.0.1/apache-hive-4.0.1-bin.tar.gz
```

**Note:** We're using Hive 4.0.1 because it's compatible with Java 8. Newer versions (4.2.0+) require Java 21 or higher.

### 3. Extract Hive Distribution

Extract the downloaded archive:

```bash
tar -xzvf apache-hive-4.0.1-bin.tar.gz
```

This creates a directory named `apache-hive-4.0.1-bin`.

### 4. Configure Hive Environment Variables

Add Hive to your environment by editing `~/.bashrc`:

```bash
vim ~/.bashrc
```

Add the following lines at the end:

```bash
export HIVE_HOME=~/apache-hive-4.0.1-bin
export PATH=$HIVE_HOME/bin:$PATH
```

Apply the changes:

```bash
source ~/.bashrc
```

Verify Hive is in your path:

```bash
which beeline
beeline --version
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
hadoop fs -mkdir -p /tmp
hadoop fs -mkdir -p /user/hive/warehouse
hadoop fs -chmod g+w /tmp
hadoop fs -chmod g+w /user/hive/warehouse
```

**Explanation:**
- `/tmp` - Temporary directory for Hive operations
- `/user/hive/warehouse` - Default location for Hive tables (hive.metastore.warehouse.dir)
- `g+w` - Group write permissions required for Hive to function properly

Verify the directories were created:

```bash
hadoop fs -ls /
hadoop fs -ls /user/hive
```

### 7. Initialize Hive Metastore

Hive uses a metastore to store metadata about tables, columns, and partitions. For this tutorial, we'll use Derby, an embedded database that doesn't require additional installation.

**Important:** Derby is suitable for testing and learning but not for production. Production environments should use MySQL or PostgreSQL.

#### Fix Guava Library Conflict

Hive 4.0.1 and Hadoop 3.4.2 have conflicting Guava library versions. Fix this before initializing:

```bash
# Remove the old Guava from Hive
rm $HIVE_HOME/lib/guava-*.jar

# Copy Hadoop's Guava to Hive
cp $HADOOP_HOME/share/hadoop/common/lib/guava-*.jar $HIVE_HOME/lib/
```

#### Fix Schematool Classpath Issue

The schematool script may not be finding Hive classes. Edit the schematool script:

```bash
vim $HIVE_HOME/bin/schematool
```

Find the line that starts with `exec` near the end of the file and add the Hive lib directory to the classpath. Look for a line like:

```bash
exec "$HADOOP" jar "$JAR" org.apache.hive.beeline.schematool.HiveSchemaTool "$@"
```

Change it to:

```bash
export HADOOP_CLASSPATH="$HIVE_HOME/lib/*:$HADOOP_CLASSPATH"
exec "$HADOOP" jar "$JAR" org.apache.hive.beeline.schematool.HiveSchemaTool "$@"
```

Save and exit.

#### Alternative: Use Direct Java Command

If editing the script doesn't work, run schematool directly with Java:

```bash
cd ~
export HADOOP_CLASSPATH=$HIVE_HOME/lib/*

hadoop jar $HIVE_HOME/lib/hive-standalone-metastore-*.jar \
  org.apache.hive.beeline.schematool.HiveSchemaTool \
  -dbType derby -initSchema
```

#### Initialize the Metastore

Now try initializing:

```bash
cd ~
schematool -dbType derby -initSchema
```

You should see output indicating successful schema initialization:

```
Metastore connection URL: jdbc:derby:;databaseName=metastore_db;create=true
Metastore Connection Driver : org.apache.derby.jdbc.EmbeddedDriver
...
schemaTool completed
```

**Note:** This creates a `metastore_db` directory in your current location. Always run Beeline from the same directory where you initialized the metastore.

### 8. Verify Hive Installation

Start Beeline (the modern Hive CLI):

```bash
beeline -u jdbc:hive2://
```

**Note:** This starts Beeline and HiveServer2 in the same process for testing purposes. Beeline is the recommended interface for Hive, replacing the deprecated Hive CLI.

You should see the Beeline prompt:

```
Beeline version 4.0.1 by Apache Hive
beeline>
```

Test basic commands:

```sql
SHOW DATABASES;
```

Expected output:
```
+----------------+
| database_name  |
+----------------+
| default        |
+----------------+
1 row selected
```

Exit Beeline:

```sql
!quit
```

Or simply:

```sql
exit;
```

## Next Steps

Now that Hive is installed, you can start working with it. See [Working with Apache Hive](03_working_with_hive.md) for examples of:
- Processing JSON data
- Creating tables and loading data
- Running HiveQL queries
- Managing Beeline sessions
- Common HiveQL operations

## Configuration Files

### Important Configuration Locations

- **hive-site.xml** - Main configuration file (`$HIVE_HOME/conf/hive-site.xml`)
- **hive-default.xml** - Default configurations (`$HIVE_HOME/conf/hive-default.xml`)
- **hive-log4j.properties** - Logging configuration (`$HIVE_HOME/conf/hive-log4j.properties`)

For detailed configuration options and usage examples, see [Working with Apache Hive](03_working_with_hive.md).

## Common Issues and Troubleshooting

### Derby Metastore Issues

**Symptom:** "Another instance of Derby may have already booted the database"

**Solution:**
- Only one Beeline session can use Derby at a time
- Ensure no other Hive/Beeline processes are running
- Check for running HiveServer2: `ps aux | grep hiveserver2`
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
hadoop fs -chmod -R 777 /user/hive/warehouse
hadoop fs -chmod -R 777 /tmp
```

**Note:** 777 permissions are acceptable for learning environments but not for production.

### Hadoop Not Running

**Symptom:** "Connection refused" errors

**Solution:**
1. Check Hadoop services: `jps`
2. Start Hadoop if needed: `start-all.sh`
3. Verify HDFS is accessible: `hadoop fs -ls /`

### NameNode in Safe Mode

**Symptom:** `mkdir: Cannot create directory. Name node is in safe mode.`

**Cause:** HDFS is in safe mode, which is a read-only state that prevents modifications. This typically occurs when:
- HDFS is starting up and checking block replication
- The cluster has insufficient DataNodes running
- HDFS detected issues during startup

**Solution:**

Check safe mode status:
```bash
hadoop dfsadmin -safemode get
```

If safe mode is ON, you can manually leave safe mode:
```bash
hadoop dfsadmin -safemode leave
```

**Note:** Only use this command if you're certain HDFS has finished its startup checks. In production, let HDFS exit safe mode automatically to ensure data integrity.

If the problem persists:
1. Check DataNode is running: `jps` (should show DataNode)
2. Check HDFS logs: `$HADOOP_HOME/logs/hadoop-*-namenode-*.log`
3. Verify block replication: `hadoop dfsadmin -report`

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
2. **Dedicated HiveServer2** - Run HiveServer2 as a separate service for multi-user access
3. **Security** - Implement Kerberos authentication
4. **High Availability** - Configure metastore HA
5. **Performance** - Use Tez or Spark execution engine instead of MapReduce
6. **Connection Pooling** - Configure JDBC connection pooling for better performance

## Summary

You now have a working Apache Hive 4.0.1 installation on Rocky Linux 10 that:

- Uses Java 8 (compatible with both Hadoop and Hive 4.0.1)
- Uses Beeline as the modern interface (HiveCLI is deprecated)
- Uses Derby as an embedded metastore (suitable for learning)
- Integrates with your existing Hadoop installation
- Provides SQL-like interface for querying HDFS data
- Automatically converts HiveQL to MapReduce jobs
- Supports JSON and other data formats via SerDes

This setup allows you to analyze large datasets using familiar SQL syntax without writing complex MapReduce code.
