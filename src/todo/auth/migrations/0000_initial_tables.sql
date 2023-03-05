-- name: create_role_table
create table if not exists role
(
    id   integer primary key autoincrement,
    name text not null unique
);


-- name: create_user_table
create table if not exists user
(
    id        integer primary key autoincrement,
    username  text not null unique,
    password  text not null,
    is_admin  int default 0,
    is_active int default 1,
    created   int  not null,
    modified  int  null
);
