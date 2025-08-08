-- PostgreSQL database creation script
-- *******************************************************
-- Drops (if exists) and creates the 'net_analysis' database
-- Adjust OWNER or encoding/locales as needed for your environment.

-- Drop the database if it already exists (optional)
DROP DATABASE IF EXISTS net_analysis;

-- Create the database
CREATE DATABASE net_analysis
    WITH
    OWNER = postgres       -- change to desired role
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE   = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;
