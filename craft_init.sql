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
