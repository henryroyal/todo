-- name: increment_task_number_sequence
-- fn(board_id: int)
update board
set task_seq = task_seq + 1
where id = ?;

-- name: select_task_number_sequence
-- fn(board_id: int)
select task_seq as number
from board
where id = ?;

-- name: increment_comment_number_sequence
-- fn(task_id: int)
update task
set comment_seq = comment_seq + 1
where id = ?;

-- name: select_comment_number_sequence
-- fn(task_id: int)
select comment_seq as number
from task
where id = ?;

-- name: create_new_task
-- fn(number: int, board_id: int, creator_id: int, assignee_id: int, title: str, body: str, created: int)
insert into task (number, board_id, creator_id, assignee_id, title, body, created)
values (?, ?, ?, ?, ?, ?, ?);

-- name: query_task_search
select rowid, title, body, rank
from task_search
where task_search match ?
order by rank;

-- name: filter_search_result_by_user
select t.id
from task t
         left join board_user_role bur on t.board_id = bur.board_id
where bur.user_id = ?;

-- name: delete_task
-- fn(task_id: int)
delete
from task
where id = :task_id;

-- name: set_task_tag
-- fn(task_id: int, value: str)
insert into task_tag (task_id, value)
values (:task_id, :value)
on conflict do nothing;

-- name: select_task_tag
-- fn(task_id: int, value: str)
select id, task_id, value
from task_tag
where task_id = ?
  and value = ?;

-- name: select_task_tags
-- fn(task_id: int)
select id, task_id, value
from task_tag
where task_id = ?;

-- name: delete_task_tag
-- fn(tag_id: int)
delete
from task_tag
where id = :tag_id;

-- name: delete_task_tags
-- fn(task_id: int)
delete
from task_tag
where task_id = ?;

-- name: select_task_by_task_id
-- fn(task_id: int)
select id,
       number,
       board_id,
       creator_id,
       assignee_id,
       status_id,
       title,
       body,
       created,
       modified
from task
where task.id = ?;

-- name: select_tasks_by_board_id
-- fn(board_id: int)
select id,
       number,
       board_id,
       creator_id,
       assignee_id,
       status_id,
       title,
       body,
       created,
       modified
from task
where task.board_id = ?;

-- name: select_task_by_board_number
-- fn(board_id: int, task_number: int)
select id,
       number,
       board_id,
       creator_id,
       assignee_id,
       status_id,
       title,
       body,
       created,
       modified
from task
where task.board_id = ?
  and task.number = ?;

-- name: create_task_event
insert into task_event (task_id, user_id, created, description, change_field, change_old, change_new)
values (?, ?, ?, ?, ?, ?, ?);

-- name: select_task_events_by_task_id
select id,
       task_id,
       user_id,
       created,
       description,
       change_field,
       change_old,
       change_new
from task_event
where task_id = ?;

-- name: delete_task_events
-- fn(task_id: int)
delete
from task_event
where task_id = ?;

-- name: create_task_status
-- fn()
insert into task_status (task_id, name)
values (:task_id, :name)
on conflict do nothing;

-- name: delete_task_statuses
-- fn(task_id: int)
delete
from task_status
where task_id = ?;

-- name: set_task_status
update task
set status_id = :status_id
where id = :task_id;


-- name: select_task_statuses
select id, task_id, name
from task_status
where task_id = ?;

-- name: select_task_status
select id, task_id, name
from task_status
where task_id = ?
  and name = ?;

-- name: select_task_status_by_id
select id, task_id, name
from task_status
where id = ?;

-- name: create_task_comment
-- fn(task_id: int, contents: str)
insert into task_comment
    (task_id, number, user_id, contents, created)
values (?, ?, ?, ?, ?);


-- name: edit_task_comment
-- fn(contents: str, modified: int, task_id: int, number: int)
update task_comment
set contents = :contents,
    modified = :modified
where task_id = :task_id
  and number = :number;

-- name: delete_task_comment
-- fn(task_id: int, number: int)
delete
from task_comment
where task_id = ?
  and number = ?;

-- name: delete_task_comments
-- fn(task_id: int)
delete
from task_comment
where task_id = ?;

-- name: select_task_comments_by_task_id
-- fn(task_id: int)
select id, task_id, number, user_id, contents, created, modified
from task_comment
where task_id = ?
order by number desc;

-- name: select_task_comment_by_task_id_and_comment_number
-- fn(task_id: int, number: int)
select id, task_id, number, user_id, contents, created, modified
from task_comment
where task_id = ?
  and number = ?;

-- name: set_task_assignee
-- fn(assignee_id: int, modified: int, task_id: int)
update task
set assignee_id = ?,
    modified    = ?
where id = ?;

-- name: set_task_title
-- fn(title: str, modified: int, task_id: int)
update task
set title    = ?,
    modified = ?
where id = ?;

-- name: set_task_body
-- fn(body: str, modified: int, task_id: int)
update task
set body     = ?,
    modified = ?
where id = ?;

-- name: update_task_modified
-- fn(task_id: int, modified: int)
update task
set modified = ?
where id = ?;

-- name: user_tasks_summary
-- fn(user_id: int)
select b.symbol                                                 as symbol,
       t.number                                                 as number,
       t.title                                                  as description,
       (select name from task_status where id = t.status_id)    as status,
       (select username from user where id = b.creator_id)      as creator,
       (select username from user where id = t.assignee_id)     as asignee,
       (select count(1) from task_tag where task_id = t.id)     as tag_count,
       (select count(1) from task_comment where task_id = t.id) as comment_count,
       coalesce(t.modified, t.created)                          as last_updated
from board_user_role bur
         left join board b on b.id = bur.board_id
         join task t on b.id = t.board_id
where bur.user_id = ? and bur.is_accepted = 1
order by last_updated desc;


-- select b.symbol                                                 as symbol,
--        t.number                                                 as number,
--        t.title                                                  as description,
--        (select name from task_status where id = t.status_id)    as status,
--        (select username from user where id = b.creator_id)      as creator,
--        (select username from user where id = t.assignee_id)     as asignee,
--        (select count(1) from task_tag where task_id = t.id)     as tag_count,
--        (select count(1) from task_comment where task_id = t.id) as comment_count,
--        coalesce(t.modified, t.created)                          as last_updated
-- from board_user_role bur
--          left join board b on b.id = bur.board_id
--          join task t on b.id = t.board_id
-- where bur.user_id = ? and bur.is_accepted = 1
-- order by last_updated desc;
