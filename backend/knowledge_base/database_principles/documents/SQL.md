# SQL

## 概述

SQL（Structured Query Language）是结构化查询语言，是关系数据库的标准语言，用于管理和操作关系数据库。

### SQL的分类

**DDL（数据定义语言）**：
- CREATE、DROP、ALTER

**DML（数据操作语言）**：
- INSERT、UPDATE、DELETE

**DQL（数据查询语言）**：
- SELECT

**DCL（数据控制语言）**：
- GRANT、REVOKE

## DDL（数据定义语言）

### CREATE

**创建数据库**：
```sql
CREATE DATABASE university;
```

**创建表**：
```sql
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    student_name VARCHAR(50) NOT NULL,
    department VARCHAR(50),
    grade INT,
    gender CHAR(1)
);
```

**创建视图**：
```sql
CREATE VIEW student_view AS
SELECT student_id, student_name, department
FROM students
WHERE department = '计算机学院';
```

**创建索引**：
```sql
CREATE INDEX idx_student_name ON students(student_name);
```

### DROP

**删除数据库**：
```sql
DROP DATABASE university;
```

**删除表**：
```sql
DROP TABLE students;
```

**删除视图**：
```sql
DROP VIEW student_view;
```

**删除索引**：
```sql
DROP INDEX idx_student_name;
```

### ALTER

**添加列**：
```sql
ALTER TABLE students ADD COLUMN email VARCHAR(100);
```

**修改列**：
```sql
ALTER TABLE students MODIFY COLUMN grade INT DEFAULT 1;
```

**删除列**：
```sql
ALTER TABLE students DROP COLUMN email;
```

**添加约束**：
```sql
ALTER TABLE students ADD CONSTRAINT pk_student_id PRIMARY KEY(student_id);
```

## DML（数据操作语言）

### INSERT

**插入单行**：
```sql
INSERT INTO students (student_id, student_name, department)
VALUES (1001, '张三', '计算机学院');
```

**插入多行**：
```sql
INSERT INTO students (student_id, student_name, department)
VALUES 
    (1002, '李四', '电子工程学院'),
    (1003, '王五', '计算机学院');
```

**从其他表插入**：
```sql
INSERT INTO new_students (student_id, student_name)
SELECT student_id, student_name FROM students WHERE grade = 1;
```

### UPDATE

**更新单行**：
```sql
UPDATE students 
SET department = '软件工程学院' 
WHERE student_id = 1001;
```

**更新多行**：
```sql
UPDATE students 
SET grade = grade + 1 
WHERE department = '计算机学院';
```

**使用子查询更新**：
```sql
UPDATE students 
SET department = (SELECT department FROM departments WHERE department_id = 1)
WHERE student_id = 1001;
```

### DELETE

**删除单行**：
```sql
DELETE FROM students WHERE student_id = 1001;
```

**删除多行**：
```sql
DELETE FROM students WHERE grade = 4;
```

**删除所有行**：
```sql
DELETE FROM students;
```

## DQL（数据查询语言）

### SELECT基础

**查询所有列**：
```sql
SELECT * FROM students;
```

**查询指定列**：
```sql
SELECT student_id, student_name FROM students;
```

**去重查询**：
```sql
SELECT DISTINCT department FROM students;
```

**使用别名**：
```sql
SELECT student_id AS id, student_name AS name FROM students;
```

### WHERE子句

**条件查询**：
```sql
SELECT * FROM students WHERE grade = 1;
```

**多条件查询**：
```sql
SELECT * FROM students 
WHERE department = '计算机学院' AND gender = '男';
```

**范围查询**：
```sql
SELECT * FROM students WHERE grade BETWEEN 1 AND 3;
```

**模糊查询**：
```sql
SELECT * FROM students WHERE student_name LIKE '张%';
```

**空值查询**：
```sql
SELECT * FROM students WHERE department IS NULL;
```

### ORDER BY子句

**升序排序**：
```sql
SELECT * FROM students ORDER BY student_id ASC;
```

**降序排序**：
```sql
SELECT * FROM students ORDER BY grade DESC;
```

**多列排序**：
```sql
SELECT * FROM students ORDER BY department ASC, grade DESC;
```

### LIMIT子句

**限制返回行数**：
```sql
SELECT * FROM students LIMIT 10;
```

**分页查询**：
```sql
SELECT * FROM students LIMIT 10 OFFSET 20;
```

### 聚合函数

**COUNT**：
```sql
SELECT COUNT(*) FROM students;
SELECT COUNT(DISTINCT department) FROM students;
```

**SUM**：
```sql
SELECT SUM(grade) FROM students;
```

**AVG**：
```sql
SELECT AVG(grade) FROM students;
```

**MAX/MIN**：
```sql
SELECT MAX(grade), MIN(grade) FROM students;
```

### GROUP BY子句

**分组查询**：
```sql
SELECT department, COUNT(*) FROM students GROUP BY department;
```

**分组过滤**：
```sql
SELECT department, COUNT(*) FROM students 
GROUP BY department HAVING COUNT(*) > 10;
```

### JOIN操作

**内连接**：
```sql
SELECT * FROM students 
JOIN enrollments ON students.student_id = enrollments.student_id;
```

**左外连接**：
```sql
SELECT * FROM students 
LEFT JOIN enrollments ON students.student_id = enrollments.student_id;
```

**右外连接**：
```sql
SELECT * FROM students 
RIGHT JOIN enrollments ON students.student_id = enrollments.student_id;
```

**全外连接**：
```sql
SELECT * FROM students 
FULL JOIN enrollments ON students.student_id = enrollments.student_id;
```

**交叉连接**：
```sql
SELECT * FROM students CROSS JOIN courses;
```

### 子查询

**单行子查询**：
```sql
SELECT * FROM students 
WHERE department = (SELECT department FROM departments WHERE department_id = 1);
```

**多行子查询**：
```sql
SELECT * FROM students 
WHERE department IN (SELECT department FROM departments WHERE type = '工科');
```

**相关子查询**：
```sql
SELECT * FROM students s
WHERE EXISTS (SELECT * FROM enrollments e WHERE e.student_id = s.student_id);
```

### 窗口函数

**排名函数**：
```sql
SELECT student_id, student_name, grade,
    ROW_NUMBER() OVER (ORDER BY grade DESC) AS rank,
    RANK() OVER (ORDER BY grade DESC) AS rank_with_gap,
    DENSE_RANK() OVER (ORDER BY grade DESC) AS dense_rank
FROM students;
```

**聚合窗口函数**：
```sql
SELECT student_id, student_name, department, grade,
    AVG(grade) OVER (PARTITION BY department) AS avg_grade
FROM students;
```

**累积计算**：
```sql
SELECT student_id, student_name, grade,
    SUM(grade) OVER (ORDER BY student_id) AS cumulative_sum
FROM students;
```

## DCL（数据控制语言）

### GRANT

**授权**：
```sql
GRANT SELECT ON students TO user1;
GRANT INSERT, UPDATE ON students TO user2;
GRANT ALL ON students TO admin;
```

**授权并允许转授权**：
```sql
GRANT SELECT ON students TO user1 WITH GRANT OPTION;
```

### REVOKE

**回收权限**：
```sql
REVOKE SELECT ON students FROM user1;
REVOKE INSERT, UPDATE ON students FROM user2;
```

## 事务控制

### BEGIN

**开始事务**：
```sql
BEGIN TRANSACTION;
```

### COMMIT

**提交事务**：
```sql
COMMIT;
```

### ROLLBACK

**回滚事务**：
```sql
ROLLBACK;
```

### SAVEPOINT

**设置保存点**：
```sql
SAVEPOINT savepoint1;
ROLLBACK TO savepoint1;
```

## 总结

SQL是关系数据库的核心语言：
- DDL：定义数据结构
- DML：操作数据
- DQL：查询数据
- DCL：控制权限
- 支持复杂查询、连接、子查询和窗口函数