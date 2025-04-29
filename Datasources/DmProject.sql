
-- Create the database
CREATE DATABASE IF NOT EXISTS DmProject;
USE DmProject;

-- Drop tables if they exist
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS region;

-- Create region table
CREATE TABLE region (
    rnumber INT PRIMARY KEY,
    rname VARCHAR(50)
);

-- Create customer table
CREATE TABLE customer (
    customerId INT PRIMARY KEY,
    fname VARCHAR(50),
    lname VARCHAR(50),
    age INT,
    rno INT,
    FOREIGN KEY (rno) REFERENCES region(rnumber)
);

-- Insert into region
INSERT INTO region (rnumber, rname) VALUES
(1, 'North'),
(2, 'South'),
(3, 'West');

-- Insert into customer
INSERT INTO customer (customerId, fname, lname, age, rno) VALUES
(201, 'Irene', 'Davis', 54, 1),
(202, 'Steve', 'Jones', 44, 2),
(203, 'Irene', 'Moore', 24, 3),
(204, 'Mona', 'Jones', 55, 3),
(205, 'Nina', 'Davis', 56, 2),
(206, 'Bob', 'Wilson', 28, 3),
(207, 'Oscar', 'Taylor', 51, 1),
(208, 'Mona', 'Jones', 35, 1),
(209, 'Charlie', 'Taylor', 37, 2),
(210, 'Charlie', 'Wilson', 46, 1),
(211, 'Irene', 'Davis', 45, 1),
(212, 'Jack', 'Davis', 18, 1),
(213, 'Hank', 'Miller', 50, 1),
(214, 'Liam', 'Johnson', 64, 2),
(215, 'Mona', 'Wilson', 43, 3),
(216, 'Paul', 'Taylor', 32, 2),
(217, 'Steve', 'Moore', 64, 3),
(218, 'Kathy', 'Smith', 22, 2),
(219, 'Quincy', 'Brown', 53, 3),
(220, 'Kathy', 'Wilson', 41, 3);
