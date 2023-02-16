-- name: select_role_by_id
-- fn(role_id: int)
select *
from role
where id = ?;

-- name: select_role_by_name
-- fn(role_name: str)
select *
from role
where name = :role_name;

-- name: create_user
-- fn(username: str, password: bytes, created: int)
insert into user (username, password, created, is_admin, is_active)
values (:username, :password, :created, :is_admin, :is_active);

-- name: select_user_by_id
-- fn(username: str)
select id,
       username,
       password,
       is_admin,
       is_active,
       created,
       modified
from user
where user.id = :user_id;

-- name: select_user_by_username
-- fn(username: str)
select id,
       username,
       password,
       is_admin,
       is_active,
       created,
       modified
from user
where user.username = ?
  and user.is_active = true;

-- name: select_all_users_for_admin
-- fn()
select u.username,
       u.is_admin,
       u.is_active,
       coalesce(u.modified, u.created)                          as last_modified,
       (select count(1) from task t where t.creator_id = u.id)  as task_count,
       (select count(1) from board b where b.creator_id = u.id) as board_count
from user u;
