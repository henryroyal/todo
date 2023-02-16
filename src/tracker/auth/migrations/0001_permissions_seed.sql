-- name: seed_roles
insert into role (id, name)
values (0, 'manager'),
       (1, 'collaborator'),
       (2, 'viewer');
