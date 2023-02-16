-- name: create_new_board
-- fn(symbol: str, name: str, creator: int, created: int)
insert into board (symbol, name, creator_id, created)
values (?, ?, ?, ?);

-- name: delete_board
-- fn(board_id: int)
delete
from board
where id = ?;

-- name: delete_board_tasks
-- fn()
delete
from task
where board_id = ?;

-- name: delete_board_roles
-- fn(board_id: int)
delete
from board_user_role
where board_id = ?;

-- name: add_board_status
-- fn(creator_id: int, symbol: str)
insert into board_status (board_id, name)
values ((select id from board where creator_id = :creator_id and symbol = :symbol), :status)
on conflict do nothing;

-- name: delete_board_status
-- fn(status_id: int)
delete
from board_status
where id = ?;

-- name: delete_board_statuses
-- fn()
delete
from board_status
where board_id = ?;


-- name: select_board_by_id
-- fn(board_id: int)
select id,
       creator_id,
       symbol,
       task_seq,
       status,
       name,
       created,
       modified
from board
where id = ?;

-- name: select_board_by_creator_symbol
-- fn(creator_id: int, symbol: str)
select id,
       creator_id,
       symbol,
       task_seq,
       status,
       name,
       created,
       modified
from board
where creator_id = ?
  and symbol = ?;

-- name: select_boards_by_user
-- fn(user_id: int)
select bur.board_id,
       b.creator_id,
       b.symbol,
       b.task_seq,
       b.status,
       b.name,
       b.created,
       b.modified
from board_user_role bur
         left join board b on b.id = bur.board_id
where bur.user_id = ?;

-- name: select_board_statuses
-- fn(board_id: int)
select id, board_id, name
from board_status
where board_id = ?;


-- name: create_board_status
-- fn(board_id: int, name: str)
insert into board_status (board_id, name)
values (?, ?);

-- name: set_board_status
-- fn(creator_id: int, symbol: str, status: str)
update board
set status = (select id
              from board_status
              where board_id = :board_id
                and name = :name)
where id = :board_id;


-- name: select_board_user
-- fn(board_id: int, user_id: int)
select bur.id, bur.board_id, bur.user_id, r.name
from board_user_role bur
         left join role r on r.id = bur.role_id
where board_id = ?
  and user_id = ?;

-- name: delete_board_user
-- fn(board_id: int, user_id: int
delete
from board_user_role
where board_id = ?
  and user_id = ?;


-- name: set_board_user_role
-- fn(user_role: str, board_id: int, user_id: int)
insert into board_user_role (board_id, user_id, role_id, invitation_from)
values (:board_id, :user_id, (select id from role where name = :role_name), :invitation_from)
on conflict (board_id, user_id) do update set role_id         = (select id from role where name = :role_name),
                                              invitation_from = :invitation_from
where board_id = :board_id
  and user_id = :user_id;


-- name: accept_board_user_role
-- fn(board_id: int, user_id: int)
update board_user_role
set is_accepted = 1,
    is_declined = 0
where board_id = :board_id
  and user_id = :user_id;


-- name: decline_board_user_role
-- fn(board_id: int, user_id: int)
update board_user_role
set is_accepted = 0,
    is_declined = 1
where board_id = :board_id
  and user_id = :user_id;


-- name: list_user_share_requests_received
-- fn(user_id: int)
select u.username as board_creator,
       b.symbol   as board_symbol,
       b.name     as board_name,
       r.name     as role_name
from board_user_role bur
         left outer join board b on b.id = bur.board_id and bur.id is not null
         left outer join user u on u.id = b.creator_id and bur.id is not null
         left join role r on bur.role_id = r.id
where bur.user_id = :user_id
  and bur.is_invited = 1
  and bur.is_accepted = 0
  and bur.is_declined = 0;

-- name: list_user_share_for_assignees
-- fn(user_id: int)
select u.username
from board_user_role bur
         left outer join board b on b.id = bur.board_id and bur.id is not null
         left outer join user u on u.id = bur.user_id and bur.id is not null
         left join role r on bur.role_id = r.id
where bur.board_id = :board_id
  and bur.is_accepted = 1
  and r.name != 'viewer';


-- name: select_board_status_by_id
-- fn(status_id: int)
select id, board_id, name
from board_status
where id = :status_id;


-- name: rename_board
-- fn(new_name: str, board_id: int)
update board
set name = :new_name
where id = :board_id;

-- name: set_board_symbol
-- fn(board_id: int, symbol: str)
update board
set symbol = :symbol
where id = :board_id;

-- name: user_boards_summary
select bur.id                                                       role_id,
       b.symbol                                                     symbol,
       b.name                                                       name,
       (select name from board_status where id = b.status)          status,
       cu.id                                                        creator_id,
       cu.username                                                  creator,
       r.name                                                    as role,
       coalesce(b.modified, b.created)                              last_updated,
       (select count(1) from task where board_id = bur.board_id) as task_count,
       (select count(1)
        from board_user_role
        where is_accepted = 1
          and board_id = b.id
          and user_id != :user_id
          and id is not null)                                       shares
from board b
         left outer join board_user_role bur
                         on b.id = bur.board_id and (b.creator_id = :user_id or bur.user_id = :user_id)
                             and bur.id is not null
         left join role r on r.id = bur.role_id
         left join user cu on b.creator_id = cu.id
where bur.user_id = :user_id
  and bur.is_accepted = 1
order by status, last_updated;


-- name: board_tasks_summary
-- fn(board_id: int)
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
where bur.user_id = :user_id
  and bur.board_id = :board_id
  and ((bur.is_invited = 1 and bur.is_accepted = 1) or b.creator_id = :user_id)
order by status, last_updated desc;


-- name: board_user_role_summary
-- fn(board_id: int)
select cu.username     as board_creator,
       b.symbol        as board_symbol,
       gu.username     as username,
       r.name          as role,
       gu.is_active    as is_active,
       bur.is_invited  as is_invited,
       bur.is_accepted as is_accepted,
       bur.is_declined as is_declined
from board_user_role bur
         left join board b on bur.board_id = b.id
         left join user cu on b.creator_id = cu.id
         left join user gu on bur.user_id = gu.id
         left join role r on bur.role_id = r.id
where bur.board_id = :board_id
  and bur.user_id != :user_id
  and bur.is_accepted = 1;


-- name: user_board_roles_summary
-- fn()
select cu.username     as board_creator,
       b.symbol        as board_symbol,
       gu.username     as username,
       r.name          as role,
       gu.is_active    as is_active,
       bur.is_invited  as is_invited,
       bur.is_accepted as is_accepted,
       bur.is_declined as is_declined
from board_user_role bur
         left join board b on bur.board_id = b.id
         left join user cu on b.creator_id = cu.id
         left join user gu on bur.user_id = gu.id
         left join role r on bur.role_id = r.id
where bur.user_id = ?;
