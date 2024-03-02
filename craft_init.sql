create table try_apply_record
(
    id          int not null,
    apply_times int default 1,
    primary key (id)
);

create table authentication_code
(
    uuid varchar(40),
    owner_id int default null,
    primary key (uuid)
);

/* Default UUID: 70db1934-417e-4120-9f70-cec9d9f5a312 */
insert into authentication_code (uuid) values ('70db1934-417e-4120-9f70-cec9d9f5a312');