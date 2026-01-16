# Lab 1: Apache Cassandra Installation and CQL Operations

## Objective
Install and configure Apache Cassandra on Rocky Linux 10, then practice CQL (Cassandra Query Language) operations including keyspace creation, table creation, data insertion, and querying using a provided dataset.

## Prerequisites
- Rocky Linux 10 virtual machine or physical system
- Non-root user with sudo privileges
- Internet connection for downloading packages

## Part 1: Installation

### Step 1: Update System Packages

Update your local package index:

```bash
sudo dnf update -y
```

### Step 2: Install Java 8 (Amazon Corretto)

Apache Cassandra requires Java 8. Install Amazon Corretto 8:

```bash
sudo rpm --import https://yum.corretto.aws/corretto.key
sudo curl -L -o /etc/yum.repos.d/corretto.repo https://yum.corretto.aws/corretto.repo
sudo yum install java-1.8.0-amazon-corretto-devel -y
```

Verify Java installation:

```bash
java -version
```

### Step 3: Install Python and pip3

Install Python 3 and pip3 for cqlsh:

```bash
sudo yum install python3 python3-pip -y
sudo pip3 install cqlsh
```

### Step 4: Add Apache Cassandra Repository

Create a yum repository file:

```bash
sudo vi /etc/yum.repos.d/cassandra.repo
```

Add the following content:

```ini
[cassandra]
name=Apache Cassandra
baseurl=https://redhat.cassandra.apache.org/41x/
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://downloads.apache.org/cassandra/KEYS
```

Save and close the file.

### Step 5: Update System and Handle GPG Keys

Run the system update:

```bash
sudo dnf update -y
```

**Note:** If you encounter GPG key import errors:

```bash
sudo update-crypto-policies --set LEGACY
sudo reboot
```

### Step 6: Install Apache Cassandra

```bash
sudo dnf install cassandra -y
```

### Step 7: Create Systemd Unit File

Create the systemd service file:

```bash
sudo vi /etc/systemd/system/cassandra.service
```

Add the following content:

```ini
[Unit]
Description=Apache Cassandra
After=network.target

[Service]
PIDFile=/var/run/cassandra/cassandra.pid
User=cassandra
Group=cassandra
ExecStart=/usr/sbin/cassandra -f -p /var/run/cassandra/cassandra.pid
Restart=always

[Install]
WantedBy=multi-user.target
```

Save and close the file.

### Step 8: Start Cassandra Service

```bash
sudo systemctl daemon-reload
sudo systemctl start cassandra
sudo systemctl enable cassandra
```

Verify Cassandra is running:

```bash
sudo systemctl status cassandra
nodetool status
```

### Step 9: Connect to Cassandra

```bash
cqlsh
```

You should see the cqlsh prompt. Type `exit` to exit for now.

## Part 2: Lab Tasks

### Dataset

You will work with a product catalog dataset. Create a file named `products.json` with the following content:

```json
[
  {
    "product_id": "P001",
    "name": "Laptop",
    "category": "Electronics",
    "price": 899.99,
    "stock": 45,
    "manufacturer": "TechCorp",
    "release_year": 2023
  },
  {
    "product_id": "P002",
    "name": "Wireless Mouse",
    "category": "Electronics",
    "price": 29.99,
    "stock": 150,
    "manufacturer": "PeripheralPro",
    "release_year": 2022
  },
  {
    "product_id": "P003",
    "name": "Office Chair",
    "category": "Furniture",
    "price": 249.99,
    "stock": 30,
    "manufacturer": "ComfortSeating",
    "release_year": 2023
  },
  {
    "product_id": "P004",
    "name": "Mechanical Keyboard",
    "category": "Electronics",
    "price": 129.99,
    "stock": 75,
    "manufacturer": "KeyMaster",
    "release_year": 2023
  },
  {
    "product_id": "P005",
    "name": "Standing Desk",
    "category": "Furniture",
    "price": 449.99,
    "stock": 20,
    "manufacturer": "ErgoWorks",
    "release_year": 2022
  },
  {
    "product_id": "P006",
    "name": "USB-C Hub",
    "category": "Electronics",
    "price": 49.99,
    "stock": 200,
    "manufacturer": "ConnectAll",
    "release_year": 2023
  },
  {
    "product_id": "P007",
    "name": "Monitor 27-inch",
    "category": "Electronics",
    "price": 349.99,
    "stock": 60,
    "manufacturer": "DisplayTech",
    "release_year": 2023
  },
  {
    "product_id": "P008",
    "name": "Desk Lamp",
    "category": "Furniture",
    "price": 39.99,
    "stock": 100,
    "manufacturer": "BrightLight",
    "release_year": 2022
  }
]
```

### Task 1: Create Keyspace (5 points)

Create a keyspace named `product_catalog` with SimpleStrategy replication and replication factor of 1.

```cql
-- Your CQL query here
```

### Task 2: Create Products Table (10 points)

Create a table named `products` in the `product_catalog` keyspace with the following schema:
- `product_id` (TEXT, PRIMARY KEY)
- `name` (TEXT)
- `category` (TEXT)
- `price` (DECIMAL)
- `stock` (INT)
- `manufacturer` (TEXT)
- `release_year` (INT)

```cql
-- Your CQL query here
```

### Task 3: Insert All Products (10 points)

Write CQL INSERT statements to add all 8 products from the JSON file into the `products` table.

```cql
-- Your CQL queries here (8 INSERT statements)
```

### Task 4: Query All Products (5 points)

Write a query to retrieve all products from the `products` table.

```cql
-- Your CQL query here
```

### Task 5: Query Single Product by ID (5 points)

Write a query to retrieve the product with `product_id = 'P004'`.

```cql
-- Your CQL query here
```

### Task 6: Query Electronics Products (5 points)

**Note:** Since Cassandra requires filtering on non-primary key columns, you'll need to use `ALLOW FILTERING`. In production, you would create a secondary index or use a different table design.

Write a query to retrieve all products in the "Electronics" category.

```cql
-- Your CQL query here
```

### Task 7: Query Products by Price Range (5 points)

Write a query to find all products with a price between 100 and 500 (inclusive).

```cql
-- Your CQL query here
```

### Task 8: Update Product Stock (5 points)

Write a query to update the stock of the product with `product_id = 'P002'` to 175.

```cql
-- Your CQL query here
```

### Task 9: Query Products by Manufacturer (5 points)

Write a query to retrieve all products manufactured by "TechCorp".

```cql
-- Your CQL query here
```

### Task 10: Delete a Product (5 points)

Write a query to delete the product with `product_id = 'P008'`.

```cql
-- Your CQL query here
```

## Deliverables

Submit **only**:
- **CSCI273-[StudentID]-[LastName]-CassandraLab.cql**

**File format example**:
```cql
/*
Certificate of Authorship:
I have not discussed the CQL code in my program with anyone 
other than my instructor or the teaching assistants assigned to this course.
I have not used CQL code obtained from another student, 
or any other unauthorized source, either modified or unmodified.
If any CQL code or documentation used in my program 
was obtained from another source, such as a textbook or course notes, 
that has been clearly noted with a proper citation in the comments of my program.
*/

-- Lab 1 Solution - Apache Cassandra Installation and CQL Operations
-- Student: [Your Name]
-- Student ID: [Your Student ID]

-- Task 1: Create Keyspace (5 points)
-- Your query here

-- Task 2: Create Products Table (10 points)
-- Your query here

-- Task 3: Insert All Products (10 points)
-- Your queries here

-- Task 4: Query All Products (5 points)
-- Your query here

-- Task 5: Query Single Product by ID (5 points)
-- Your query here

-- Task 6: Query Electronics Products (5 points)
-- Your query here

-- Task 7: Query Products by Price Range (5 points)
-- Your query here

-- Task 8: Update Product Stock (5 points)
-- Your query here

-- Task 9: Query Products by Manufacturer (5 points)
-- Your query here

-- Task 10: Delete a Product (5 points)
-- Your query here
```

## Grading

**Total: 50 points**

- Task 1: Create keyspace (5 points)
- Task 2: Create products table (10 points)
- Task 3: Insert all products (10 points)
- Task 4: Query all products (5 points)
- Task 5: Query single product by ID (5 points)
- Task 6: Query electronics products (5 points)
- Task 7: Query by price range (5 points)
- Task 8: Update product stock (5 points)
- Task 9: Query by manufacturer (5 points)
- Task 10: Delete a product (5 points)

## Important Configuration Files

- **Main Configuration:** `/etc/cassandra/default.conf/cassandra.yaml`
- **Data Directory:** `/var/lib/cassandra/data`
- **Logs:** `/var/log/cassandra/`

## Managing Cassandra Service

### Start Cassandra
```bash
sudo systemctl start cassandra
```

### Stop Cassandra
```bash
sudo systemctl stop cassandra
```

### Restart Cassandra
```bash
sudo systemctl restart cassandra
```

### Check Status
```bash
sudo systemctl status cassandra
nodetool status
```

## Troubleshooting

### Issue 1: Cassandra Service Won't Start

**Symptoms:** Service fails to start or immediately stops

**Solution:**
1. Check logs:
   ```bash
   sudo journalctl -u cassandra -xe
   ```
2. Verify Java installation:
   ```bash
   java -version
   ```
3. Check disk space:
   ```bash
   df -h
   ```
4. Verify permissions on data directories:
   ```bash
   ls -la /var/lib/cassandra/
   ```

### Issue 2: Cannot Connect with cqlsh

**Symptoms:** `cqlsh` command fails or cannot connect

**Solution:**
1. Verify Cassandra is running:
   ```bash
   sudo systemctl status cassandra
   ```
2. Check if port 9042 is listening:
   ```bash
   sudo netstat -tulpn | grep 9042
   ```
3. Wait a few minutes after starting Cassandra (it takes time to initialize)

### Issue 3: GPG Key Import Errors

**Symptoms:** Errors during `dnf update` about GPG keys

**Solution:**
Update crypto policies to LEGACY:
```bash
sudo update-crypto-policies --set LEGACY
sudo reboot
```

### Issue 4: Python Import Errors with cqlsh

**Symptoms:** `ImportError: cannot import name 'authproviderhandling' from 'cqlshlib'`

**Solution:**
1. Find the cqlshlib path:
   ```bash
   find /usr/lib/ -name cqlshlib
   ```
2. Export the path (adjust based on your output):
   ```bash
   export PYTHONPATH=$PYTHONPATH:/usr/lib/python3.6/site-packages/
   ```
3. Re-run the cqlsh command

### Issue 5: ALLOW FILTERING Warning

**Symptoms:** Query requires `ALLOW FILTERING` clause

**Explanation:** Cassandra is optimized for queries on primary keys. Filtering on non-primary key columns requires full table scans, which is inefficient.

**Solution for Production:**
- Create secondary indexes on frequently queried columns
- Design tables with appropriate primary keys based on query patterns
- Use materialized views for different query patterns

**For this lab:** Using `ALLOW FILTERING` is acceptable for learning purposes.
