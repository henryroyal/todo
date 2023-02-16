-- name: create_table_task
create table if not exists task
(
    id          integer not null primary key autoincrement,
    number      integer not null,
    board_id    integer not null,
    creator_id  integer not null,
    assignee_id integer,
    status_id   integer,
    title       text    not null,
    body        text    not null,
    created     integer not null,
    modified    integer,
    comment_seq integer default 0,

    unique (board_id, number),
    foreign key (board_id) references board (id) on delete cascade,
    foreign key (creator_id) references user (id) on delete restrict,
    foreign key (assignee_id) references user (id) on delete set null,
    foreign key (status_id) references task_status (id) on delete cascade
);

-- name: create_task_search_idx
create virtual table task_search using fts5
(
    title,
    body,
    content='task',
    content_rowid='id'
);

-- name: create_task_search_insert_trigger
create trigger task_search_on_insert
    after insert
    on task
begin
    insert into task_search (rowid, title, body)
    values (new.id, new.title, new.body);
end;

-- name: create_task_search_update_trigger
create trigger task_search_on_update
    after update
    on task
begin
    insert into task_search (task_search, rowid, title, body)
    values ('delete', old.id, old.title, old.body);
    insert into task_search (rowid, title, body)
    values (new.id, new.title, new.body);
end;

-- name: create_task_search_delete_trigger
create trigger task_search_on_delete
    after delete
    on task
begin
    insert into task_search (task_search, rowid, title, body)
    values ('delete', old.id, old.title, old.body);
end;

-- name: initialize_fts_index
insert into task_search(task_search) VALUES ('rebuild');

-- name: create_table_task_status
create table if not exists task_status
(
    id      integer not null primary key autoincrement,
    task_id integer not null,
    name    text    not null,

    unique (task_id, name),
    foreign key (task_id) references task (id) on delete cascade
);


-- name: create_table_task_tags
create table if not exists task_tag
(
    id      integer not null primary key autoincrement,
    task_id integer not null,
    value   text    not null,

    foreign key (task_id) references task (id) on delete cascade
);

-- name: create_task_tag_idx
create unique index task_tag_idx on task_tag (value, task_id);


-- name: create_table_task_comments
create table if not exists task_comment
(
    id       integer not null primary key autoincrement,
    task_id  integer not null,
    number   integer not null,
    user_id  integer not null,
    contents text    not null,
    created  integer not null,
    modified integer,

    unique (task_id, number),
    foreign key (task_id) references task (id) on delete cascade,
    foreign key (user_id) references user (id) on delete cascade
);


-- name: create_table_task_event
create table if not exists task_event
(
    id           integer not null primary key autoincrement,
    task_id      integer not null,
    user_id      integer not null,
    created      integer not null,
    description  text    not null,
    change_field text,
    change_old   text,
    change_new   text,

    foreign key (task_id) references task (id) on delete cascade,
    foreign key (user_id) references user (id) on delete cascade
);
