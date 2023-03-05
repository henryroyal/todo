-- name: create_table_board
create table if not exists board
(
    id         integer primary key autoincrement,
    creator_id int  not null,
    symbol     text not null,
    task_seq   int default 0,
    status     int,
    name       text not null,
    created    int  not null,
    modified   int,

    unique (creator_id, symbol),
    foreign key (status) references board_status (id) on delete cascade,
    foreign key (creator_id) references user (id) on delete cascade
);


-- name: create_table_board_status
create table if not exists board_status
(
    id       integer primary key autoincrement,
    board_id int  not null,
    name     text not null,

    unique (board_id, name),
    foreign key (board_id) references board (id)
);


-- name: create_table_board_user
create table if not exists board_user_role
(
    id              integer primary key autoincrement,
    board_id        integer not null,
    user_id         integer not null,
    role_id         integer not null,
    is_invited      integer default 1,
    is_accepted     integer default 0,
    is_declined     integer default 0,
    invitation_from integer not null,

    unique (board_id, user_id),
    foreign key (board_id) references board (id),
    foreign key (user_id) references user (id),
    foreign key (role_id) references role (id),
    foreign key (invitation_from) references user (id)
);
