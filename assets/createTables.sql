create database returns;
use returns;
create table returnsforex(
    date date,
    profit double,
    amount double,
    symbol varchar(100),
    total_time double,
    PRIMARY KEY(date,symbol)
);
