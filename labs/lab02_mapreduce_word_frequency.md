# Lab 2: MapReduce Word Frequency Analysis on Hadoop

## Objective
Adapt the MapReduce word count example to calculate word frequency (percentage) instead of raw counts. This lab demonstrates how to modify MapReduce jobs to perform more complex analytics on text data using Hadoop HDFS and streaming.

## Prerequisites
- Hadoop installation on Rocky Linux 10 (completed from notes)
- Basic understanding of MapReduce concepts
- Python 3 installed
- HDFS running and accessible

## Background

Word count shows the raw number of times each word appears. Word frequency shows the percentage of total words that each word represents, providing better insight into word distribution in a document.

**Example:**
- Text: "hello world hello"
- Word Count: hello=2, world=1
- Word Frequency: hello=66.67%, world=33.33%

## Part 1: Understanding the Original Word Count

Review the MapReduce word count example from the notes:

**mapper.py** - Emits (word, 1) for each word
**sort** - Groups identical words together
**reducer.py** - Sums counts for each word

## Part 2: Lab Tasks

### Task 1: Download Input Data (5 points)

Download the King James Bible from Project Gutenberg:

```bash
wget https://www.gutenberg.org/cache/epub/21/pg21.txt -O bible.txt
```

**Screenshot Required:** Show the download command and file size verification using `ls -lh bible.txt`.

### Task 2: Upload to HDFS (10 points)

Create an input directory in HDFS and upload the Bible text:

```bash
bin/hdfs dfs -mkdir -p /user/<your-username>/lab2/input
bin/hdfs dfs -put bible.txt /user/<your-username>/lab2/input/
bin/hdfs dfs -ls /user/<your-username>/lab2/input
```

**Screenshot Required:** Show the HDFS commands and directory listing confirming the file upload.

### Task 3: Run Original Word Count on Hadoop (15 points)

Run the original word count using Hadoop Streaming:

```bash
bin/hadoop jar share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -input /user/<your-username>/lab2/input/bible.txt \
  -output /user/<your-username>/lab2/wordcount_output \
  -mapper /path/to/mapper.py \
  -reducer /path/to/reducer.py
```

View the results:

```bash
bin/hdfs dfs -cat /user/<your-username>/lab2/wordcount_output/part-00000 | head -20
```

**Screenshot Required:** Show the Hadoop Streaming job execution and the top 20 word counts.

### Task 4: Modify Reducer for Word Frequency (30 points)

Create a new file `frequency_reducer.py` that:
1. Collects all word counts (first pass)
2. Calculates total word count
3. Outputs each word with its frequency as a percentage

**Requirements:**
- Output format: `word\tfrequency` (e.g., `hello\t66.67`)
- Round to 2 decimal places
- Frequencies should sum to 100%

```python
#!/usr/bin/env python3
# Your code here
```

**Code Required:** Submit your `frequency_reducer.py` file.

### Task 5: Run Word Frequency on Hadoop (15 points)

Run the word frequency job on Hadoop:

```bash
bin/hadoop jar share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -input /user/<your-username>/lab2/input/bible.txt \
  -output /user/<your-username>/lab2/frequency_output \
  -mapper /path/to/mapper.py \
  -reducer /path/to/frequency_reducer.py
```

View the results:

```bash
bin/hdfs dfs -cat /user/<your-username>/lab2/frequency_output/part-00000 | head -20
```

**Screenshot Required:** Show the Hadoop Streaming job execution and the top 20 word frequencies.

### Task 6: Analysis Questions (15 points)

Answer the following questions in a text file named `analysis.txt`:

1. What is the most frequent word in the Bible and its percentage? (3 points)
2. How many unique words are in the Bible? (3 points)
3. What percentage of words appear only once? (3 points)
4. Why is word frequency more useful than word count for text analysis? (3 points)
5. What modification would you make to exclude common words (the, a, an, etc.)? (3 points)

### Task 7: Create README (5 points)

Create a `README.md` file documenting:
- How to run the word frequency pipeline on Hadoop
- Differences from word count
- Sample output format
- HDFS paths used

### Task 8: Sort by Frequency (For Grade A) (25 points)

Modify your pipeline to output results sorted by frequency from highest to lowest.

**Note:** This may require multiple MapReduce jobs or additional processing steps. Consider:
- Can you pipe the HDFS output through sort?
- Do you need an additional mapper/reducer pair?
- How does sorting by numeric values differ from sorting by text?

**Requirements:**
- Output must be sorted by frequency (highest first)
- Maintain the same output format: `word\tfrequency`
- Document your approach in the README

**Hint:** You can retrieve HDFS output and sort it:
```bash
bin/hdfs dfs -cat /user/<your-username>/lab2/frequency_output/part-00000 | sort -t$'\t' -k2 -nr | head -20
```

Or run a second MapReduce job to sort the data.

**Screenshot Required:** Show the sorted output with the most frequent words at the top (at least top 20).

## Deliverables

Submit a **single ZIP file** named: **CSCI273-[StudentID]-[LastName]-Lab2.zip**

The ZIP file must contain:

1. **frequency_reducer.py** - Your modified reducer code
2. **mapper.py** - Copy of the original mapper (for completeness)
3. **analysis.txt** - Answers to analysis questions
4. **README.md** - Documentation
5. **screenshots/** folder containing:
   - `task1_download.png` - Bible download and file verification
   - `task2_hdfs_upload.png` - HDFS upload and directory listing
   - `task3_wordcount.png` - Hadoop word count job and results
   - `task5_frequency.png` - Hadoop word frequency job and results
   - `task8_sorted.png` - Sorted frequency output (for A grade)

**File Header Template for frequency_reducer.py:**
```python
#!/usr/bin/env python3
"""
Certificate of Authorship:
I have not discussed the Python code in my program with anyone 
other than my instructor or the teaching assistants assigned to this course.
I have not used Python code obtained from another student, 
or any other unauthorized source, either modified or unmodified.
If any Python code or documentation used in my program 
was obtained from another source, such as a textbook or course notes, 
that has been clearly noted with a proper citation in the comments of my program.

Lab 2 - MapReduce Word Frequency Analysis
Student: [Your Name]
Student ID: [Your Student ID]
Date: [Submission Date]
"""

# Your code here
```

## Grading

**Total: 100 points (Base) + 25 points (Task 8 for A grade)**

**Base Grade (100 points):**
- Task 1: Download input data (5 points)
- Task 2: Upload to HDFS (10 points)
- Task 3: Run original word count on Hadoop (15 points)
- Task 4: Modify reducer for word frequency (30 points)
  - Correct calculation (20 points)
  - Proper output format (5 points)
  - Code quality and comments (5 points)
- Task 5: Run word frequency on Hadoop (15 points)
- Task 6: Analysis questions (15 points)
- Task 7: Create README (5 points)
- Task 8: Sort by frequency (5 points base documentation)

**For A Grade:**
- Task 8: Sort by frequency implementation (25 points)
  - Correct sorting implementation (15 points)
  - Documentation of approach (5 points)
  - Screenshot showing sorted output (5 points)

**Deductions:**
- Missing screenshots: -5 points each
- Incorrect file naming: -5 points
- Missing certificate of authorship: -10 points
- Code without comments: -5 points
- Not running on Hadoop: -20 points

## Important Notes

### Making Python Scripts Executable

Ensure your mapper and reducer scripts are executable:

```bash
chmod +x mapper.py frequency_reducer.py
```

### Cleaning Up HDFS Directories

If you need to re-run a job, delete the output directory first:

```bash
bin/hdfs dfs -rm -r /user/<your-username>/lab2/wordcount_output
bin/hdfs dfs -rm -r /user/<your-username>/lab2/frequency_output
```

### Hadoop Streaming Path

The Hadoop Streaming JAR location may vary. Find it with:

```bash
find . -name "hadoop-streaming*.jar"
```

## Hints

### Hint 1: Two-Pass Approach
Your reducer needs to:
1. First pass: Read all input and store word counts
2. Calculate total words
3. Second pass: Output frequencies

### Hint 2: Data Structure
Use a dictionary to store word counts:
```python
word_counts = {}
```

### Hint 3: Percentage Calculation
```python
frequency = (count / total_words) * 100
```

### Hint 4: Formatting Output
```python
print(f"{word}\t{frequency:.2f}")
```

### Hint 5: Sorting by Numeric Values
The Linux `sort` command can sort by numeric values in specific columns:
```bash
sort -t$'\t' -k2 -nr
```
- `-t$'\t'` - Use tab as delimiter
- `-k2` - Sort by column 2
- `-n` - Numeric sort
- `-r` - Reverse (highest first)

### Hint 6: Testing Locally First
Before running on Hadoop, test your scripts locally:
```bash
cat bible.txt | python3 mapper.py | sort | python3 frequency_reducer.py | head -20
```

## Additional Resources

- MapReduce word count notes: `/notes/mapreduce_wordcount/`
- Hadoop Streaming documentation: https://hadoop.apache.org/docs/stable/hadoop-streaming/HadoopStreaming.html
- Python string methods: https://docs.python.org/3/library/stdtypes.html#string-methods
- Linux sort command: `man sort`

## Academic Integrity

This is an individual assignment. You may discuss concepts with classmates, but all code must be your own work. Copying code from any source without proper attribution is a violation of academic integrity policies.
