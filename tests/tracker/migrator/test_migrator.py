def test_migrations_applied(app):
    with app.database as db:
        cursor = db.cursor()
        migration = cursor.execute(
            "select filename from migrations"
        )

        result = cursor.fetchall()
        assert result[0][0] == "auth/migrations/0000_initial_tables.sql"
        assert result[1][0] == "auth/migrations/0001_permissions_seed.sql"
        assert result[2][0] == "board/migrations/0000_initial_tables.sql"
        assert result[3][0] == "task/migrations/0000_initial_tables.sql"
